"""Parse a narrow N-PORT XML holdings subset by local tag name."""

import math
import xml.etree.ElementTree as ET
from pathlib import Path

from .config import (ASSET, BALANCE, CURRENCY, ISSUER, REPORTED_PERCENT,
                     SECURITY, VALUE, WEIGHT)

# Configuration
HOLDING_TAG = "invstOrSec"
TAG_MAP = {ISSUER: "name", SECURITY: "cusip", BALANCE: "balance",
           VALUE: "valUSD", REPORTED_PERCENT: "pctVal", CURRENCY: "curCd",
           ASSET: "assetCat"}
REQUIRED = (ISSUER, BALANCE, VALUE, REPORTED_PERCENT, CURRENCY)
MAX_XML_BYTES = 20_000_000


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def parse_holdings(path, net_assets=None):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_XML_BYTES or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("Unsafe or oversized XML")
    if net_assets is not None and (not math.isfinite(net_assets) or net_assets <= 0):
        raise ValueError("Net assets must be positive")
    root = ET.fromstring(raw)
    rows = []
    for element in root.iter():
        if local_name(element.tag) != HOLDING_TAG:
            continue
        values = {local_name(child.tag): (child.text or "").strip() for child in element}
        row = {key: values.get(tag, "") for key, tag in TAG_MAP.items()}
        if any(not row[key] for key in REQUIRED):
            raise ValueError("Holding lacks required fields")
        for key in (BALANCE, VALUE, REPORTED_PERCENT):
            row[key] = float(row[key])
            if not math.isfinite(row[key]):
                raise ValueError("Nonfinite holding")
        row[WEIGHT] = row[VALUE] / net_assets if net_assets else row[REPORTED_PERCENT] / 100
        rows.append(row)
    if not rows:
        raise ValueError("No supported holdings found")
    return rows

