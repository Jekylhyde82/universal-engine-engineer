"""Minimal offline-first STARWIRE CLI."""
import argparse, json
from pathlib import Path
from .core import CandidateStore, import_json, import_csv, import_xml

def main():
    p=argparse.ArgumentParser(prog="starwire")
    sub=p.add_subparsers(dest="command",required=True)
    for name in ("import-json","import-csv","import-xml"):
        q=sub.add_parser(name); q.add_argument("file"); q.add_argument("--source-url",default="https://local.invalid/import")
        q.add_argument("--db",default="starwire.db")
    r=sub.add_parser("report"); r.add_argument("--db",default="starwire.db")
    a=p.parse_args(); store=CandidateStore(a.db)
    try:
        if a.command=="report": print(json.dumps(store.report(),indent=2)); return
        data=Path(a.file).read_bytes()
        fn={"import-json":import_json,"import-csv":import_csv,"import-xml":import_xml}[a.command]
        candidates=fn(data,a.source_url)
        added=sum(store.add(c) for c in candidates)
        print(json.dumps({"received":len(candidates),"new_observations":added,"status":"discovered_unverified"},indent=2))
    finally: store.close()

if __name__=="__main__": main()
