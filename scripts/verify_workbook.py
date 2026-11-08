"""Inspect saved OOXML caches, metadata and formulas against Python outputs."""

import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

# Configuration
ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "excel" / "asset_management_toolkit.xlsx"
INPUT = ROOT / "examples" / "output" / "workbook_inputs.json"
REPORT = ROOT / "examples" / "output" / "excel_verification.json"
AUTHOR = "Yazad Madan"
NAMESPACE = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
CORE_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
TOLERANCE = 1e-7
ERROR_TYPES = {"e"}
CONTENT_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/content-types"
REL_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/relationships"
CORE_RELATIONSHIP = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
CORE_CONTENT_TYPE = "application/vnd.openxmlformats-package.core-properties+xml"


def set_author():
    with ZipFile(WORKBOOK) as archive:
        contents = {name: archive.read(name) for name in archive.namelist()}
    core = (ET.fromstring(contents["docProps/core.xml"]) if "docProps/core.xml" in contents
            else ET.Element(f"{{{CORE_NAMESPACE}}}coreProperties"))
    for namespace, name in ((DC_NAMESPACE, "creator"), (CORE_NAMESPACE, "lastModifiedBy")):
        element = core.find(f"{{{namespace}}}{name}")
        if element is None:
            element = ET.SubElement(core, f"{{{namespace}}}{name}")
        element.text = AUTHOR
    contents["docProps/core.xml"] = ET.tostring(core, encoding="utf-8", xml_declaration=True)
    content_types = ET.fromstring(contents["[Content_Types].xml"])
    if not any(element.attrib.get("PartName") == "/docProps/core.xml" for element in content_types):
        ET.SubElement(content_types, f"{{{CONTENT_NAMESPACE}}}Override", PartName="/docProps/core.xml", ContentType=CORE_CONTENT_TYPE)
    contents["[Content_Types].xml"] = ET.tostring(content_types, encoding="utf-8", xml_declaration=True)
    relationships = ET.fromstring(contents["_rels/.rels"])
    if not any(element.attrib.get("Type") == CORE_RELATIONSHIP for element in relationships):
        existing_ids = {element.attrib["Id"] for element in relationships}
        relationship_id = "coreAuthor"
        while relationship_id in existing_ids:
            relationship_id += "x"
        ET.SubElement(relationships, f"{{{REL_NAMESPACE}}}Relationship", Id=relationship_id,
                      Type=CORE_RELATIONSHIP, Target="docProps/core.xml")
    contents["_rels/.rels"] = ET.tostring(relationships, encoding="utf-8", xml_declaration=True)
    workbook = ET.fromstring(contents["xl/workbook.xml"])
    calculation = workbook.find("s:calcPr", NAMESPACE)
    if calculation is None:
        calculation = ET.SubElement(workbook, f"{{{NAMESPACE['s']}}}calcPr")
    calculation.attrib.update({"calcMode": "auto", "fullCalcOnLoad": "1", "forceFullCalc": "1"})
    contents["xl/workbook.xml"] = ET.tostring(workbook, encoding="utf-8", xml_declaration=True)
    with ZipFile(WORKBOOK, "w", ZIP_DEFLATED) as archive:
        for name, raw in contents.items():
            archive.writestr(name, raw)


def verify():
    inputs = json.loads(INPUT.read_text(encoding="utf-8"))
    expected = {"B6": inputs["tax"]["realized_gain"], "B7": inputs["tax"]["realized_loss"],
                "B8": sum(trade["cash_flow"] for trade in inputs["tax"]["trades"] if trade["side"] == "SELL"),
                "B9": inputs["tax"]["cash"], "B10": sum(row["fee"] for row in inputs["billing"])}
    with ZipFile(WORKBOOK) as archive:
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        cells = {cell.attrib["r"]: cell for cell in sheet.findall(".//s:c", NAMESPACE)}
        checks = {}
        for address, value in expected.items():
            actual = float(cells[address].find("s:v", NAMESPACE).text)
            if abs(actual-value) > TOLERANCE:
                raise AssertionError(f"{address}: {actual} != {value}")
            checks[address] = {"cached_excel": actual, "python": value, "difference": actual-value}
        for name in archive.namelist():
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                root = ET.fromstring(archive.read(name))
                for cell in root.findall(".//s:c", NAMESPACE):
                    if cell.attrib.get("t") in ERROR_TYPES:
                        raise AssertionError(f"Formula error in {name}, {cell.attrib['r']}")
        core = ET.fromstring(archive.read("docProps/core.xml"))
        if core.find(f"{{{DC_NAMESPACE}}}creator").text != AUTHOR:
            raise AssertionError("Author metadata mismatch")
        styles = ET.fromstring(archive.read("xl/styles.xml"))
        if styles.findall(".//s:font/s:color", NAMESPACE):
            raise AssertionError("Font colors are not permitted")
        if any(element.attrib.get("fillId", "0") != "0" for element in styles.findall("s:cellXfs/s:xf", NAMESPACE)):
            raise AssertionError("Cell fills are not permitted")
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    report["saved_ooxml_reconciliation"] = checks
    report["author_verified"] = True
    report["plain_styles_verified"] = True
    report["recalculate_on_open"] = True
    REPORT.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("Saved workbook: five totals reconcile; formula error scan and author metadata pass.")


if __name__ == "__main__":
    set_author()
    verify()

