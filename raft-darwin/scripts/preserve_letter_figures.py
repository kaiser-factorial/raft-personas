"""Preserve audited Darwin Project inline figures with provenance."""
import argparse, hashlib, json, pathlib, urllib.parse, urllib.request
from datetime import datetime, timezone
from lxml import html

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = ROOT / "reports/1844-1846/review/inline-figures-audit.json"
DEST = ROOT / "data/raw/dcp/1844-1846/figures"
MANIFEST = DEST / "manifest.json"
HOST = "www.darwinproject.ac.uk"

def allowed_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != HOST:
        raise ValueError("refusing non-Darwin figure URL")
    return url

class RestrictedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def save(manifest):
    temp = MANIFEST.with_suffix('.json.tmp')
    temp.write_text(json.dumps(manifest, indent=2) + '\n')
    temp.replace(MANIFEST)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(row):
    source = ROOT / row["source_path"]
    if not source.exists() or digest(source) != row["source_sha256"]:
        raise ValueError("audited HTML missing or hash changed")
    doc = html.fromstring(source.read_bytes())
    nodes = doc.xpath(row["dom_locator"])
    if len(nodes) != 1 or nodes[0].tag != row["tag"]:
        raise ValueError("audited DOM locator no longer resolves uniquely")
    current = nodes[0].get("src") or nodes[0].get("data") or nodes[0].get("href")
    expected = row.get("src") or row.get("data") or row.get("href")
    if current != expected:
        raise ValueError("figure URL changed at audited locator")
    url = urllib.parse.urljoin("https://www.darwinproject.ac.uk/", current or "")
    return source, allowed_url(url)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", help="restrict fetching to letter IDs")
    args = ap.parse_args()
    wanted = {x if x.startswith('DCP-LETT-') else 'DCP-LETT-'+x for x in (args.ids or [])}
    audit_rows = json.loads(AUDIT.read_text())["nodes"]
    if wanted - {r['letter_id'] for r in audit_rows}:
        raise ValueError('Requested IDs are absent from figure inventory')
    rows = [r for r in audit_rows
            if not wanted or r["letter_id"] in wanted]
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"kind": "inline_letter_figures", "files": [], "errors": []}
    existing = {(r["letter_id"], r["dom_locator"]): r for r in manifest["files"]}
    errors = []
    opener = urllib.request.build_opener(RestrictedRedirect())
    for row in rows:
        try:
            source, url = check(row)
            key = (row["letter_id"], row["dom_locator"])
            old = existing.get(key)
            if old:
                path = ROOT / old["figure_path"]
                if not path.exists() or digest(path) != old["sha256"]:
                    raise ValueError("manifested figure hash failed")
                if old['source_url'] != url or old['source_html_sha256'] != row['source_sha256']:
                    raise ValueError('manifested source provenance changed')
                continue
            suffix = pathlib.Path(urllib.parse.urlparse(url).path).suffix or ".bin"
            out = DEST / f"{row['letter_id']}-{len([k for k in existing if k[0] == row['letter_id']]) + 1}{suffix}"
            if out.exists():
                raise ValueError('unmanifested figure already exists; preserve for separate recovery')
            request = urllib.request.Request(url, headers={"User-Agent": "Darwin-figure-preservation/1.0"})
            retrieved = datetime.now(timezone.utc).isoformat()
            with opener.open(request, timeout=40) as response:
                allowed_url(response.geturl())
                raw = response.read()
                status = response.status
                content_type = response.headers.get("Content-Type")
                final_url = response.geturl()
            if status != 200 or not raw or not (content_type or '').lower().startswith('image/'):
                raise ValueError('response is not a successful nonempty image')
            out.write_bytes(raw)
            existing[key] = {"letter_id": row["letter_id"], "dom_locator": row["dom_locator"],
                "source_path": row["source_path"], "source_html_sha256": digest(source),
                "source_url": url, "alt": row.get("alt"), "figure_path": str(out.relative_to(ROOT)),
                "retrieved_at": retrieved, "http_status": status, "content_type": content_type, "final_url": final_url,
                "bytes": len(raw), "sha256": digest(out)}
            manifest['files'] = list(existing.values())
            save(manifest)
        except Exception as exc:
            errors.append({"letter_id": row["letter_id"], "dom_locator": row["dom_locator"], "error": str(exc)})
    manifest["files"] = list(existing.values())
    manifest.setdefault('runs', []).append({'completed_at':datetime.now(timezone.utc).isoformat(),'requested_ids':sorted(wanted),'requested_rows':len(rows),'errors':errors})
    manifest["errors"] = errors
    save(manifest)
    print(json.dumps({"requested_rows": len(rows), "preserved": len(existing), "errors": len(errors), "manifest": str(MANIFEST)}, indent=2))
    if errors:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
