"""Safe, provider-neutral STARWIRE ingestion and SYPHON extraction primitives."""
from __future__ import annotations
import csv, hashlib, ipaddress, json, socket, sqlite3, time, urllib.parse, urllib.request, urllib.error
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

CRAWLER_CAPABILITIES = (
    "universal_web", "repository", "technology", "opportunity", "ai_model",
    "infrastructure", "research", "source_discovery", "change_monitoring",
)
IMPORTER_CAPABILITIES = (
    "api_payload", "repository_metadata", "json", "xml_rss_atom", "csv",
    "research_metadata", "opportunity_listing", "database_catalogue", "universal_structured",
)
SYPHON_CAPABILITIES = (
    "source_acquisition", "web_extraction", "document_text", "structured_data",
    "semantic_terms", "repository_metadata", "multimedia_metadata",
    "provenance_validation", "adaptive_format",
)

MAX_IMPORT_BYTES = 2 * 1024 * 1024
MAX_TEXT_CHARS = 250_000

@dataclass(frozen=True)
class Candidate:
    title: str
    source_url: str
    source_type: str
    summary: str = ""
    observed_at: str = ""
    content_sha256: str = ""
    eligibility: str = "unknown"
    restrictions: tuple[str, ...] = ()
    status: str = "discovered_unverified"

    def validated(self) -> "Candidate":
        title = self.title.strip()
        if not title or len(title) > 500:
            raise ValueError("title must contain 1..500 characters")
        if len(self.summary) > MAX_TEXT_CHARS:
            raise ValueError("summary exceeds limit")
        if self.status != "discovered_unverified":
            raise ValueError("STARWIRE cannot assign approval or verification states")
        parsed = urllib.parse.urlsplit(self.source_url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("source_url must be an absolute HTTP(S) URL without credentials")
        observed = self.observed_at or datetime.now(timezone.utc).isoformat()
        digest = self.content_sha256 or hashlib.sha256(self.summary.encode("utf-8")).hexdigest()
        return Candidate(title, self.source_url, self.source_type, self.summary, observed,
                         digest, self.eligibility, tuple(self.restrictions), "discovered_unverified")

class CandidateStore:
    """SQLite store preserving each observation and its provenance."""
    def __init__(self, path: str = "starwire.db"):
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS observations(
            id INTEGER PRIMARY KEY, title TEXT NOT NULL, source_url TEXT NOT NULL,
            source_type TEXT NOT NULL, summary TEXT NOT NULL, observed_at TEXT NOT NULL,
            content_sha256 TEXT NOT NULL, eligibility TEXT NOT NULL,
            restrictions_json TEXT NOT NULL, status TEXT NOT NULL,
            canonical_key TEXT NOT NULL, UNIQUE(canonical_key, content_sha256))""")
        self.db.commit()

    def add(self, candidate: Candidate) -> bool:
        c = candidate.validated()
        key = hashlib.sha256((c.source_url.split("#",1)[0].rstrip("/")).encode()).hexdigest()
        cur = self.db.execute("""INSERT OR IGNORE INTO observations
          (title,source_url,source_type,summary,observed_at,content_sha256,eligibility,
           restrictions_json,status,canonical_key) VALUES(?,?,?,?,?,?,?,?,?,?)""",
          (c.title,c.source_url,c.source_type,c.summary,c.observed_at,c.content_sha256,
           c.eligibility,json.dumps(c.restrictions),c.status,key))
        self.db.commit()
        return cur.rowcount == 1

    def report(self) -> dict[str, int]:
        rows = self.db.execute("SELECT status, COUNT(*) FROM observations GROUP BY status").fetchall()
        return {str(k): int(v) for k,v in rows}

    def close(self) -> None:
        self.db.close()

def _bounded_bytes(data: bytes) -> str:
    if len(data) > MAX_IMPORT_BYTES:
        raise ValueError("input exceeds 2 MiB limit")
    return data.decode("utf-8-sig")

def import_json(data: bytes, source_url: str) -> list[Candidate]:
    obj = json.loads(_bounded_bytes(data))
    records = obj if isinstance(obj, list) else [obj]
    if len(records) > 500: raise ValueError("maximum 500 records per import")
    result=[]
    for row in records:
        if not isinstance(row, dict): raise ValueError("each JSON record must be an object")
        result.append(Candidate(str(row.get("title","")), source_url, "json",
            str(row.get("summary", row.get("description",""))),
            eligibility=str(row.get("eligibility","unknown")),
            restrictions=tuple(map(str,row.get("restrictions",[])))).validated())
    return result

def import_csv(data: bytes, source_url: str) -> list[Candidate]:
    reader=csv.DictReader(_bounded_bytes(data).splitlines())
    if not reader.fieldnames or "title" not in reader.fieldnames: raise ValueError("CSV requires a title column")
    rows=[]
    for row in reader:
        if len(rows)>=500: raise ValueError("maximum 500 records per import")
        rows.append(Candidate((row.get("title") or ""),source_url,"csv",
            (row.get("summary") or row.get("description") or "")).validated())
    return rows

def import_xml(data: bytes, source_url: str) -> list[Candidate]:
    root=ET.fromstring(_bounded_bytes(data))
    out=[]
    for item in root.iter():
        if item.tag.rsplit("}",1)[-1].lower() in ("item","entry"):
            fields={child.tag.rsplit("}",1)[-1].lower():(child.text or "") for child in item}
            title=fields.get("title","").strip()
            link=fields.get("link","").strip()
            if link.startswith("http://") or link.startswith("https://"): url=link
            else: url=source_url
            if title: out.append(Candidate(title,url,"xml_rss_atom",fields.get("description",fields.get("summary",""))).validated())
            if len(out)>500: raise ValueError("maximum 500 records per import")
    return out

class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.parts=[]; self.hidden=0
    def handle_starttag(self, tag, attrs):
        if tag in ("script","style","noscript","svg"): self.hidden+=1
    def handle_endtag(self, tag):
        if tag in ("script","style","noscript","svg") and self.hidden: self.hidden-=1
    def handle_data(self, data):
        if not self.hidden and data.strip(): self.parts.append(data.strip())

def extract_html(html: str) -> str:
    parser=_TextExtractor(); parser.feed(html[:MAX_TEXT_CHARS]); return " ".join(parser.parts)[:MAX_TEXT_CHARS]

def extract_semantic_terms(text: str) -> list[str]:
    """Conservative keyword extraction; not a claim of semantic understanding."""
    import re
    words=re.findall(r"[A-Za-z][A-Za-z0-9+._-]{2,}", text.lower())
    stop={"the","and","for","with","from","this","that","are","was","were","you","your","into"}
    counts={}
    for word in words:
        if word not in stop: counts[word]=counts.get(word,0)+1
    return [w for w,_ in sorted(counts.items(),key=lambda x:(-x[1],x[0]))[:30]]

def _host_is_safe(host: str) -> bool:
    if host.lower() in ("localhost",): return False
    try:
        ip=ipaddress.ip_address(host)
        return ip.is_global
    except ValueError:
        try: addresses={item[4][0] for item in socket.getaddrinfo(host,None)}
        except OSError: return False
        return bool(addresses) and all(ipaddress.ip_address(a.split("%")[0]).is_global for a in addresses)

def validate_crawl_url(url: str, allowed_hosts: set[str]) -> str:
    p=urllib.parse.urlsplit(url)
    if p.scheme!="https" or not p.hostname or p.username or p.password or p.port not in (None,443):
        raise ValueError("crawler accepts HTTPS URLs on standard port only")
    host=p.hostname.lower()
    if host not in {h.lower() for h in allowed_hosts}: raise ValueError("host is not explicitly allowlisted")
    if not _host_is_safe(host): raise ValueError("host resolves to a non-public or invalid address")
    return urllib.parse.urlunsplit(("https",host,p.path or "/",p.query,""))

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

class SafeCrawler:
    """Small bounded fetcher. Run only in an egress-restricted worker in production."""
    def __init__(self, allowed_hosts: set[str], max_bytes: int=512_000, timeout: float=8.0, delay: float=2.0):
        if not allowed_hosts: raise ValueError("at least one explicit host allowlist entry is required")
        self.allowed_hosts=allowed_hosts; self.max_bytes=min(max_bytes,2_000_000); self.timeout=min(timeout,15.0)
        self.delay=max(delay,1.0); self._last={}
        self.opener=urllib.request.build_opener(_NoRedirect)
    def fetch(self,url: str) -> tuple[str,str]:
        safe=validate_crawl_url(url,self.allowed_hosts)
        host=urllib.parse.urlsplit(safe).hostname
        wait=self.delay-(time.monotonic()-self._last.get(host,0))
        if wait>0: time.sleep(wait)
        req=urllib.request.Request(safe,headers={"User-Agent":"STARWIRE-ResearchBot/0.1 (+contact required)","Accept":"text/html,application/json,text/plain"})
        self._last[host]=time.monotonic()
        try:
            with self.opener.open(req,timeout=self.timeout) as response:
                if response.status!=200: raise ValueError("only HTTP 200 responses are accepted")
                ctype=response.headers.get_content_type()
                if ctype not in ("text/html","text/plain","application/json","application/xml","text/xml"):
                    raise ValueError("unsupported response content type")
                raw=response.read(self.max_bytes+1)
        except urllib.error.HTTPError as exc:
            raise ValueError(f"HTTP response rejected: {exc.code}") from exc
        if len(raw)>self.max_bytes: raise ValueError("response exceeds configured byte limit")
        return safe,raw.decode("utf-8",errors="replace")

def classify_format(name: str, content_type: str="") -> str:
    ext=Path(name).suffix.lower()
    if ext in (".json",) or "json" in content_type: return "json"
    if ext in (".xml",".rss") or "xml" in content_type or "rss" in content_type: return "xml"
    if ext==".csv" or "csv" in content_type: return "csv"
    if ext in (".html",".htm") or "html" in content_type: return "html"
    if ext==".pdf" or "pdf" in content_type: return "pdf_metadata_only"
    return "unknown"

def candidate_from_extraction(title: str, source_url: str, source_type: str, text: str) -> Candidate:
    summary=text[:MAX_TEXT_CHARS]
    return Candidate(title,source_url,source_type,summary).validated()
