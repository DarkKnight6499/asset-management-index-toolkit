"""Optional network fetch. The analytical package never imports this script."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET

# Configuration
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "public" / "nport"
USER_AGENT_ENV = "SEC_USER_AGENT"
TIMEOUT_SECONDS = 60
MAX_BYTES = 20_000_000
PAUSE_SECONDS = .5
SEC_HOST = "www.sec.gov"
ARCHIVE_PREFIX = "/Archives/edgar/data/"
AUTHOR = "Yazad Madan"


def validate_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != SEC_HOST or not parsed.path.startswith(ARCHIVE_PREFIX):
        raise ValueError("Use an https://www.sec.gov/Archives/edgar/data/ filing document URL")
    return url


class SecRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        validate_url(new_url)
        return super().redirect_request(request, response, code, message, headers, new_url)


def fetch(url, user_agent):
    validate_url(url)
    if not user_agent or "@" not in user_agent:
        raise ValueError("Set SEC_USER_AGENT to an organization/project name and contact email")
    stamp = datetime.now(timezone.utc)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    identifier = hashlib.sha256(url.encode()).hexdigest()[:16]
    manifest_path = OUTPUT / f"{stamp.strftime('%Y%m%dT%H%M%S%fZ')}_{identifier}.manifest.json"
    manifest = {"author": AUTHOR, "url": url, "retrieved_at_utc": stamp.isoformat(),
                "document": "User-selected N-PORT filing XML", "section": "Part C holdings subset",
                "status": "failed", "synthetic": False}
    try:
        time.sleep(PAUSE_SECONDS)
        with build_opener(SecRedirect()).open(Request(url, headers={"User-Agent": user_agent, "Accept": "application/xml"}), timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_BYTES+1)
            manifest["http_status"] = response.status
            manifest["final_url"] = response.url
        if len(raw) > MAX_BYTES or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise ValueError("Oversized or unsafe XML")
        root = ET.fromstring(raw)
        count = sum(element.tag.rsplit("}", 1)[-1] == "invstOrSec" for element in root.iter())
        if not count:
            raise ValueError("No invstOrSec holdings; select the filing XML document, not HTML or the filing index")
        path = OUTPUT / f"{identifier}.xml"
        if path.exists() and path.read_bytes() != raw:
            path = OUTPUT / f"{identifier}_{stamp.strftime('%Y%m%dT%H%M%S%fZ')}.xml"
        path.write_bytes(raw)
        manifest.update({"status": "downloaded", "filename": path.name, "sha256": hashlib.sha256(raw).hexdigest(),
                         "bytes": len(raw), "holding_count": count})
    except Exception as error:
        manifest["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        manifest_path.write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    return manifest_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Exact SEC filing XML URL, selected manually")
    arguments = parser.parse_args()
    print(fetch(arguments.url, os.environ.get(USER_AGENT_ENV, "")))


if __name__ == "__main__":
    main()

