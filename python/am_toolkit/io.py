"""Small file helpers, without network access."""

import csv
import hashlib
import json
from pathlib import Path

# Configuration
ENCODING = "utf-8"


def read_json(path):
    return json.loads(Path(path).read_text(encoding=ENCODING))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding=ENCODING)


def read_csv(path):
    with Path(path).open(encoding=ENCODING, newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields=None):
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0]) if rows else [])
    with path.open("w", encoding=ENCODING, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

