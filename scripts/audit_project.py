"""Check deliverable integrity without network access or third-party packages."""

import ast
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

# Configuration
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "synthetic"
OUTPUT = ROOT / "examples" / "output"
REPORT = OUTPUT / "project_audit.json"
TEXT_SUFFIXES = {".md", ".py", ".mjs", ".ps1", ".toml"}
SKIP_PARTS = {".work", ".git", "__pycache__"}
FORBIDDEN_PROSE = ("\u2014", "\u2013", "Co-Authored-By", "job search", "skill gaps", "employer applications")
NETWORK_IMPORTS = {"requests", "urllib", "http", "socket", "aiohttp"}
NAMESPACE = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
TOLERANCE = 1e-10
DATE_COLUMN = "date"
SECURITY_COLUMN = "security"
RETURN_COLUMN = "return"
WEIGHT_COLUMN = "weight"
RETURN_DATE_COLUMN = "return_date"
CLIENT_COLUMN = "client"


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    checks = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or set(path.relative_to(ROOT).parts) & SKIP_PARTS:
            continue
        if path.suffix in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            for term in FORBIDDEN_PROSE:
                # The audit configuration names the forbidden terms explicitly.
                if path != Path(__file__).resolve() and term in text:
                    raise AssertionError(f"Forbidden text in {path.relative_to(ROOT)}: {term}")
            if path.suffix == ".md":
                for target in re.findall(r"\]\(([^)]+)\)", text):
                    if "://" not in target and not target.startswith("#"):
                        if not (path.parent/target.split("#", 1)[0]).exists():
                            raise AssertionError(f"Broken local link: {path}: {target}")
    checks.append("local Markdown links and prose constraints")
    for path in (ROOT/"python"/"am_toolkit").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            imported = ([name.name for name in node.names] if isinstance(node, ast.Import)
                        else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            if any(name.split(".")[0] in NETWORK_IMPORTS for name in imported):
                raise AssertionError("Runtime network import in " + path.name)
    checks.append("no network imports in analytical package")
    for name in ("manifest.json",):
        manifest = json.loads((DATA/name).read_text(encoding="utf-8"))
        for filename, expected in manifest["files"].items():
            if digest(DATA/filename) != expected:
                raise AssertionError("Snapshot hash mismatch: " + filename)
    run_manifest = json.loads((OUTPUT/"run_manifest.json").read_text(encoding="utf-8"))
    for filename, expected in run_manifest["outputs"].items():
        if digest(OUTPUT/filename) != expected:
            raise AssertionError("Output hash mismatch: " + filename)
    checks.append("snapshot and analytical output hashes")
    ddq = (ROOT/"docs"/"rfp_ddq.md").read_text(encoding="utf-8")
    pitch = (ROOT/"docs"/"pitch_outline.md").read_text(encoding="utf-8")
    if len(re.findall(r"^## \d+\.", ddq, flags=re.M)) != 25 or len(re.findall(r"^## \d+\.", pitch, flags=re.M)) != 6:
        raise AssertionError("DDQ or pitch count incorrect")
    checks.append("25 DDQ answers and six pitch slides")
    bonds = {(row[DATE_COLUMN], row[SECURITY_COLUMN]): row for row in read_csv(DATA/"bonds.csv")}
    constituents = read_csv(OUTPUT/"index_constituents.csv")
    grouped = defaultdict(list)
    for row in constituents:
        grouped[row[RETURN_DATE_COLUMN]].append(row)
    for row in read_csv(OUTPUT/"index_monthly.csv"):
        weights = grouped[row[DATE_COLUMN]]
        if abs(sum(float(item[WEIGHT_COLUMN]) for item in weights)-1)>TOLERANCE:
            raise AssertionError("Weights do not sum to one")
        gross = sum(float(item[WEIGHT_COLUMN])*float(bonds[(row[DATE_COLUMN], item[SECURITY_COLUMN])][RETURN_COLUMN]) for item in weights)
        if abs(gross-float(row["gross_return"]))>TOLERANCE:
            raise AssertionError("Gross index return does not reconcile")
    checks.append("all 36 monthly weights and gross returns independently reconciled")
    workflow = json.loads((OUTPUT/"sma_workflows.json").read_text(encoding="utf-8"))
    held = {item[CLIENT_COLUMN] for item in workflow if item["status"] == "HOLD"}
    for filename in ("billing.csv", "custodian_trade_instructions.csv", "custodian_cash_instructions.csv"):
        if any(row[CLIENT_COLUMN] in held for row in read_csv(OUTPUT/filename)):
            raise AssertionError("Held account received an instruction or invoice")
    checks.append("onboarding-held accounts excluded from instructions and billing")
    with ZipFile(ROOT/"excel"/"asset_management_toolkit.xlsx") as archive:
        for filename in archive.namelist():
            if filename.startswith("xl/worksheets/sheet") and filename.endswith(".xml"):
                root = ET.fromstring(archive.read(filename))
                if root.findall(".//s:tabColor", NAMESPACE):
                    raise AssertionError("Tab colors are not permitted")
    checks.append("workbook has no tab colors")
    REPORT.write_text(json.dumps({"author": "Yazad Madan", "status": "passed", "checks": checks,
                                  "network_used": False}, indent=2)+"\n", encoding="utf-8")
    print(f"Project audit: {len(checks)} checks passed.")


if __name__ == "__main__":
    audit()

