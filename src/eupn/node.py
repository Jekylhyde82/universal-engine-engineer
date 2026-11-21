"""Certificate-authenticated EUPN node transport."""
from __future__ import annotations
import asyncio
import json
import logging
import sqlite3
import ssl
import struct
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOG = logging.getLogger("eupn")
MAX_FRAME = 1_048_576

class ProtocolError(Exception):
    """Invalid or oversized network frame."""

class PeerRejected(Exception):
    """Peer identity is not explicitly trusted."""

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
    max_frame: int = MAX_FRAME
    read_timeout: float = 15.0

def encode_frame(value: dict[str, Any], max_frame: int = MAX_FRAME) -> bytes:
    payload = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    if not payload or len(payload) > max_frame:
        raise ProtocolError("frame outside permitted size")
    return struct.pack("!I", len(payload)) + payload

async def read_frame(reader: asyncio.StreamReader, max_frame: int = MAX_FRAME) -> dict[str, Any]:
    header = await reader.readexactly(4)
    size = struct.unpack("!I", header)[0]
    if size < 2 or size > max_frame:
        raise ProtocolError(f"invalid frame length: {size}")
    raw = await reader.readexactly(size)
    try:
        result = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("frame is not valid JSON") from exc
    if not isinstance(result, dict):
        raise ProtocolError("envelope must be a JSON object")
    return result

def _common_name(cert: dict[str, Any] | None) -> str | None:
    if not cert:
        return None
    for rdn in cert.get("subject", ()):
        for key, value in rdn:
            if key == "commonName":
                return value
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
    """SQLite inbox/outbox; inbox insertion is idempotent and committed before ACK."""
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS inbox(
            message_id TEXT PRIMARY KEY, sender TEXT NOT NULL, recipient TEXT NOT NULL,
            message_type TEXT NOT NULL, received_at REAL NOT NULL, body TEXT NOT NULL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS outbox(
            message_id TEXT PRIMARY KEY, recipient TEXT NOT NULL, created_at REAL NOT NULL,
            body TEXT NOT NULL, delivered_at REAL)""")
        self.db.commit()
        self.lock = asyncio.Lock()

    async def receive(self, msg: dict[str, Any]) -> bool:
        async with self.lock:
            cur = self.db.execute(
                "INSERT OR IGNORE INTO inbox VALUES(?,?,?,?,?,?)",
                (msg["id"], msg["from"], msg["to"], msg["type"], time.time(),
                 json.dumps(msg, separators=(",", ":"), sort_keys=True)))
            self.db.commit()
            return cur.rowcount == 1

    async def queue(self, msg: dict[str, Any]) -> None:
        async with self.lock:
            self.db.execute("INSERT INTO outbox VALUES(?,?,?,?,NULL)",
                (msg["id"], msg["to"], time.time(), json.dumps(msg)))
            self.db.commit()

    async def mark_delivered(self, message_id: str) -> None:
        async with self.lock:
            self.db.execute("UPDATE outbox SET delivered_at=? WHERE message_id=?",
                            (time.time(), message_id))
            self.db.commit()

    async def pending(self, limit: int = 100) -> list[dict[str, Any]]:
        async with self.lock:
            rows = self.db.execute(
                "SELECT body FROM outbox WHERE delivered_at IS NULL ORDER BY created_at LIMIT ?",
                (limit,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    async def close(self) -> None:
        async with self.lock:
            self.db.close()

class EUPNNode:
    def __init__(self, config: NodeConfig):
        if not config.node_id or not 1 <= config.port <= 65535:
            raise ValueError("node ID and valid TCP port are required")
        if config.node_id in config.allowed_peers:
            raise ValueError("node cannot allowlist itself")
        self.config = config
        self.store = MessageStore(config.database)
        self.server: asyncio.AbstractServer | None = None
        self.started_at: float | None = None

    async def start(self) -> None:
        self.server = await asyncio.start_server(
            self._handle, self.config.host, self.config.port,
            ssl=server_tls_context(self.config), ssl_handshake_timeout=10,
            limit=self.config.max_frame + 4)
        self.started_at = time.time()
        LOG.info("EUPN node %s listening on %s:%s",
                 self.config.node_id, self.config.host, self.config.port)

    async def serve_forever(self) -> None:
        if self.server is None:
            await self.start()
        assert self.server is not None
        async with self.server:
            await self.server.serve_forever()

    async def close(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        await self.store.close()

    def _validate(self, msg: dict[str, Any], peer_id: str) -> None:
        required = {"id", "from", "to", "type", "sent_at", "payload"}
        if not required.issubset(msg):
            raise ProtocolError("missing envelope fields")
        if msg["from"] != peer_id:
            raise PeerRejected("claimed sender differs from TLS identity")
        if msg["to"] != self.config.node_id:
            raise ProtocolError("message addressed to another node")
        if not isinstance(msg["id"], str) or not 1 <= len(msg["id"]) <= 128:
            raise ProtocolError("invalid message ID")
        if not isinstance(msg["type"], str) or not 1 <= len(msg["type"]) <= 64:
            raise ProtocolError("invalid message type")
        if not isinstance(msg["sent_at"], (int, float)):
            raise ProtocolError("invalid timestamp")

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        try:
            tls = writer.get_extra_info("ssl_object")
            peer_id = _common_name(tls.getpeercert() if tls else None)
            if not peer_id or peer_id not in self.config.allowed_peers:
                raise PeerRejected(f"unlisted peer: {peer}")
            async with asyncio.timeout(self.config.read_timeout):
                msg = await read_frame(reader, self.config.max_frame)
                self._validate(msg, peer_id)
                inserted = await self.store.receive(msg)
                writer.write(encode_frame({
                    "type": "ack", "id": msg["id"], "accepted": True,
                    "duplicate": not inserted, "by": self.config.node_id
                }, self.config.max_frame))
                await writer.drain()
        except (PeerRejected, ProtocolError, asyncio.IncompleteReadError,
                asyncio.TimeoutError, ConnectionError, ssl.SSLError) as exc:
            LOG.warning("Connection from %s rejected/failed: %s", peer, exc)
        except Exception:
            LOG.exception("Unexpected connection failure from %s", peer)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except (ConnectionError, ssl.SSLError):
                pass

    async def send(self, host: str, port: int, recipient: str, message_type: str,
                   payload: Any, tls_context: ssl.SSLContext) -> dict[str, Any]:
        msg = {"id": str(uuid.uuid4()), "from": self.config.node_id,
               "to": recipient, "type": message_type, "sent_at": time.time(),
               "payload": payload}
        await self.store.queue(msg)
        reader, writer = await asyncio.open_connection(
            host, port, ssl=tls_context, server_hostname=host, ssl_handshake_timeout=10)
        try:
            writer.write(encode_frame(msg, self.config.max_frame))
            await writer.drain()
            async with asyncio.timeout(self.config.read_timeout):
                ack = await read_frame(reader, self.config.max_frame)
            if ack.get("type") != "ack" or ack.get("id") != msg["id"] or ack.get("accepted") is not True:
                raise ProtocolError("missing or mismatched acceptance ACK")
            await self.store.mark_delivered(msg["id"])
            return ack
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except (ConnectionError, ssl.SSLError):
                pass

    def health(self) -> dict[str, Any]:
        return {"node_id": self.config.node_id,
                "status": "healthy" if self.server else "stopped",
                "listen": f"{self.config.host}:{self.config.port}",
                "uptime_seconds": max(0, time.time()-self.started_at) if self.started_at else 0,
                "allowed_peer_count": len(self.config.allowed_peers)}
