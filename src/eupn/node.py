"""Certificate-authenticated EUPN node transport."""
from __future__ import annotations
import asyncio, json, logging, sqlite3, ssl, struct, time, uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LOG = logging.getLogger("eupn")
MAX_FRAME = 1_048_576
IDENTITY_PREFIX = "spiffe://eupn/"

class ProtocolError(Exception): pass
class PeerRejected(Exception): pass

@dataclass(frozen=True)
class NodeConfig:
    node_id: str
    host: str
    port: int
    database: Path
    certificate: Path
    private_key: Path
    trusted_ca: Path
    allowed_peers: frozenset[str]
    peer_routes: dict[str, tuple[str, int]] = field(default_factory=dict)
    max_frame: int = MAX_FRAME
    read_timeout: float = 15.0
    retry_interval: float = 2.0
    retry_max_interval: float = 300.0

def encode_frame(value: dict[str, Any], max_frame: int = MAX_FRAME) -> bytes:
    try: payload = json.dumps(value, separators=(",", ":"), sort_keys=True, allow_nan=False).encode()
    except (TypeError, ValueError) as exc: raise ProtocolError("message is not finite JSON data") from exc
    if not payload or len(payload) > max_frame: raise ProtocolError("frame outside permitted size")
    return struct.pack("!I", len(payload)) + payload

async def read_frame(reader: asyncio.StreamReader, max_frame: int = MAX_FRAME) -> dict[str, Any]:
    header = await reader.readexactly(4)
    size = struct.unpack("!I", header)[0]
    if size < 2 or size > max_frame: raise ProtocolError(f"invalid frame length: {size}")
    try: result = json.loads(await reader.readexactly(size))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise ProtocolError("frame is not valid JSON") from exc
    if not isinstance(result, dict): raise ProtocolError("envelope must be a JSON object")
    return result

def peer_identity(cert: dict[str, Any] | None) -> str | None:
    if not cert: return None
    for kind, value in cert.get("subjectAltName", ()):
        if kind == "URI" and value.startswith(IDENTITY_PREFIX):
            identity = value[len(IDENTITY_PREFIX):]
            if identity and "/" not in identity and ".." not in identity: return identity
    return None

def server_tls_context(config: NodeConfig) -> ssl.SSLContext:
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=str(config.trusted_ca))
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_cert_chain(str(config.certificate), str(config.private_key))
    return ctx

def client_tls_context(certificate: Path, private_key: Path, trusted_ca: Path) -> ssl.SSLContext:
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=str(trusted_ca))
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.check_hostname = True
    ctx.load_cert_chain(str(certificate), str(private_key))
    return ctx

class MessageStore:
    """Durable inbox/outbox with idempotent receive and scheduled retry metadata."""
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("CREATE TABLE IF NOT EXISTS inbox(message_id TEXT PRIMARY KEY,sender TEXT NOT NULL,recipient TEXT NOT NULL,message_type TEXT NOT NULL,received_at REAL NOT NULL,body TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS outbox(message_id TEXT PRIMARY KEY,recipient TEXT NOT NULL,created_at REAL NOT NULL,body TEXT NOT NULL,delivered_at REAL,attempts INTEGER NOT NULL DEFAULT 0,next_attempt REAL NOT NULL DEFAULT 0,last_error TEXT)")
        cols={row[1] for row in self.db.execute("PRAGMA table_info(outbox)")}
        for name, decl in (("attempts","INTEGER NOT NULL DEFAULT 0"),("next_attempt","REAL NOT NULL DEFAULT 0"),("last_error","TEXT")):
            if name not in cols: self.db.execute(f"ALTER TABLE outbox ADD COLUMN {name} {decl}")
        self.db.execute("CREATE INDEX IF NOT EXISTS outbox_due ON outbox(delivered_at,next_attempt,created_at)")
        self.db.commit()
        self.lock=asyncio.Lock()

    async def receive(self,msg):
        async with self.lock:
            cur=self.db.execute("INSERT OR IGNORE INTO inbox VALUES(?,?,?,?,?,?)",(msg["id"],msg["from"],msg["to"],msg["type"],time.time(),json.dumps(msg,separators=(",",":"),sort_keys=True)))
            self.db.commit(); return cur.rowcount==1

    async def queue(self,msg):
        async with self.lock:
            self.db.execute("INSERT INTO outbox(message_id,recipient,created_at,body,next_attempt) VALUES(?,?,?,?,?)",(msg["id"],msg["to"],time.time(),json.dumps(msg,separators=(",",":"),sort_keys=True),time.time()))
            self.db.commit()

    async def pending(self,limit=100):
        async with self.lock:
            rows=self.db.execute("SELECT body FROM outbox WHERE delivered_at IS NULL AND next_attempt<=? ORDER BY created_at LIMIT ?",(time.time(),limit)).fetchall()
        return [json.loads(row[0]) for row in rows]

    async def failed_attempt(self,message_id,error,base_delay,max_delay):
        async with self.lock:
            row=self.db.execute("SELECT attempts FROM outbox WHERE message_id=? AND delivered_at IS NULL",(message_id,)).fetchone()
            if row is None: return
            delay=min(base_delay*(2**min(row[0],16)),max_delay)
            self.db.execute("UPDATE outbox SET attempts=attempts+1,last_error=?,next_attempt=? WHERE message_id=? AND delivered_at IS NULL",(str(error)[:1000],time.time()+delay,message_id)); self.db.commit()

    async def mark_delivered(self,message_id):
        async with self.lock:
            self.db.execute("UPDATE outbox SET delivered_at=?,last_error=NULL WHERE message_id=?",(time.time(),message_id)); self.db.commit()

    async def close(self):
        async with self.lock: self.db.close()

class EUPNNode:
    def __init__(self,config:NodeConfig):
        if not config.node_id or not 1<=config.port<=65535: raise ValueError("node ID and valid TCP port are required")
        if config.node_id in config.allowed_peers: raise ValueError("node cannot allowlist itself")
        if set(config.peer_routes)-config.allowed_peers: raise ValueError("routes may only be configured for allowlisted peers")
        if config.max_frame<2 or config.read_timeout<=0 or config.retry_interval<=0: raise ValueError("invalid frame or timeout configuration")
        self.config=config; self.store=MessageStore(config.database); self.server=None; self.started_at=None; self.retry_task=None; self.stopping=asyncio.Event()

    async def start(self):
        self.server=await asyncio.start_server(self._handle,self.config.host,self.config.port,ssl=server_tls_context(self.config),ssl_handshake_timeout=10,limit=self.config.max_frame+4)
        self.started_at=time.time(); self.stopping.clear()
        if self.config.peer_routes: self.retry_task=asyncio.create_task(self._retry_loop(),name=f"eupn-retry-{self.config.node_id}")
        LOG.info("EUPN node %s listening on %s:%s",self.config.node_id,self.config.host,self.config.port)

    async def serve_forever(self):
        if self.server is None: await self.start()
        async with self.server: await self.server.serve_forever()

    async def close(self):
        self.stopping.set()
        if self.retry_task:
            self.retry_task.cancel()
            try: await self.retry_task
            except asyncio.CancelledError: pass
        if self.server: self.server.close(); await self.server.wait_closed(); self.server=None
        await self.store.close()

    def _validate(self,msg,peer_id):
        required={"id","from","to","type","sent_at","payload"}
        if not required.issubset(msg): raise ProtocolError("missing envelope fields")
        if msg["from"]!=peer_id: raise PeerRejected("claimed sender differs from authenticated SAN identity")
        if msg["to"]!=self.config.node_id: raise ProtocolError("message addressed to another node")
        if not isinstance(msg["id"],str) or not 1<=len(msg["id"])<=128: raise ProtocolError("invalid message ID")
        if not isinstance(msg["type"],str) or not 1<=len(msg["type"])<=64: raise ProtocolError("invalid message type")
        if isinstance(msg["sent_at"],bool) or not isinstance(msg["sent_at"],(int,float)) or msg["sent_at"]<0: raise ProtocolError("invalid timestamp")
        encode_frame(msg,self.config.max_frame)

    async def _handle(self,reader,writer):
        peer=writer.get_extra_info("peername")
        try:
            tls=writer.get_extra_info("ssl_object"); peer_id=peer_identity(tls.getpeercert() if tls else None)
            if not peer_id or peer_id not in self.config.allowed_peers: raise PeerRejected(f"unlisted or identity-less peer: {peer}")
            async with asyncio.timeout(self.config.read_timeout):
                msg=await read_frame(reader,self.config.max_frame); self._validate(msg,peer_id); inserted=await self.store.receive(msg)
                writer.write(encode_frame({"type":"ack","id":msg["id"],"accepted":True,"duplicate":not inserted,"by":self.config.node_id},self.config.max_frame)); await writer.drain()
        except (PeerRejected,ProtocolError,asyncio.IncompleteReadError,asyncio.TimeoutError,ConnectionError,ssl.SSLError) as exc: LOG.warning("Connection from %s rejected/failed: %s",peer,exc)
        except Exception: LOG.exception("Unexpected connection failure from %s",peer)
        finally:
            writer.close()
            try: await writer.wait_closed()
            except (ConnectionError,ssl.SSLError): pass

    async def _deliver(self,msg,host,port):
        context=client_tls_context(self.config.certificate,self.config.private_key,self.config.trusted_ca)
        reader,writer=await asyncio.open_connection(host,port,ssl=context,server_hostname=host,ssl_handshake_timeout=10,limit=self.config.max_frame+4)
        try:
            writer.write(encode_frame(msg,self.config.max_frame)); await writer.drain()
            async with asyncio.timeout(self.config.read_timeout): ack=await read_frame(reader,self.config.max_frame)
            if ack.get("type")!="ack" or ack.get("id")!=msg["id"] or ack.get("accepted") is not True or ack.get("by")!=msg["to"]: raise ProtocolError("missing, mismatched or unauthenticated application ACK")
            await self.store.mark_delivered(msg["id"]); return ack
        finally:
            writer.close()
            try: await writer.wait_closed()
            except (ConnectionError,ssl.SSLError): pass

    async def send(self,host,port,recipient,message_type,payload,tls_context=None):
        if recipient not in self.config.allowed_peers: raise PeerRejected("recipient is not allowlisted")
        msg={"id":str(uuid.uuid4()),"from":self.config.node_id,"to":recipient,"type":message_type,"sent_at":time.time(),"payload":payload}
        encode_frame(msg,self.config.max_frame); await self.store.queue(msg)
        return await self._deliver(msg,host,port)

    async def retry_once(self):
        for msg in await self.store.pending():
            route=self.config.peer_routes.get(msg["to"])
            if not route: continue
            try: await self._deliver(msg,route[0],route[1])
            except asyncio.CancelledError: raise
            except Exception as exc:
                await self.store.failed_attempt(msg["id"],exc,self.config.retry_interval,self.config.retry_max_interval)
                LOG.warning("Deferred delivery %s to %s: %s",msg["id"],msg["to"],exc)

    async def _retry_loop(self):
        while not self.stopping.is_set():
            await self.retry_once()
            try: await asyncio.wait_for(self.stopping.wait(),timeout=self.config.retry_interval)
            except asyncio.TimeoutError: pass

    def health(self):
        return {"node_id":self.config.node_id,"status":"healthy" if self.server else "stopped","listen":f"{self.config.host}:{self.config.port}","uptime_seconds":max(0,time.time()-self.started_at) if self.started_at else 0,"allowed_peer_count":len(self.config.allowed_peers),"retry_worker":"running" if self.retry_task and not self.retry_task.done() else "disabled"}
