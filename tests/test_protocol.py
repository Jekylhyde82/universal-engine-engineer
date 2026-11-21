import asyncio
import json
import tempfile
import unittest
import subprocess
import socket
from pathlib import Path
from eupn.node import EUPNNode, NodeConfig, MessageStore, ProtocolError, encode_frame, read_frame, peer_identity

class EUPNProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_round_trip(self):
        msg = {"id": "m1", "type": "ping"}
        reader = asyncio.StreamReader()
        reader.feed_data(encode_frame(msg)); reader.feed_eof()
        self.assertEqual(await read_frame(reader), msg)

    async def test_oversized_frame_rejected(self):
        reader = asyncio.StreamReader()
        reader.feed_data((100).to_bytes(4, "big")); reader.feed_eof()
        with self.assertRaises(ProtocolError): await read_frame(reader, max_frame=32)

    async def test_non_object_json_rejected(self):
        raw = json.dumps(["not", "an", "envelope"]).encode()
        reader = asyncio.StreamReader()
        reader.feed_data(len(raw).to_bytes(4, "big") + raw); reader.feed_eof()
        with self.assertRaises(ProtocolError): await read_frame(reader)

    async def test_non_finite_json_rejected(self):
        with self.assertRaises(ProtocolError): encode_frame({"value": float("nan")})

    async def test_peer_identity_requires_uri_san(self):
        self.assertEqual(peer_identity({"subjectAltName": [("URI", "spiffe://eupn/node-a")]}), "node-a")
        self.assertIsNone(peer_identity({"subject": ((("commonName", "node-a"),),)}))
        self.assertIsNone(peer_identity({"subjectAltName": [("URI", "spiffe://other/node-a")]}))

    async def test_inbox_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MessageStore(Path(tmp) / "node.db")
            msg = {"id":"m1","from":"peer-a","to":"peer-b","type":"event","sent_at":123.0,"payload":{"n":9}}
            self.assertTrue(await store.receive(msg))
            self.assertFalse(await store.receive(msg))
            await store.close()

    async def test_outbox_survives_restart_and_failed_attempt_is_deferred(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "node.db"
            msg = {"id":"m2","from":"node-a","to":"node-b","type":"event","sent_at":123.0,"payload":{"n":9}}
            store = MessageStore(path)
            await store.queue(msg)
            await store.failed_attempt("m2", "connection refused", 60, 300)
            self.assertEqual(await store.pending(), [])
            await store.close()
            store = MessageStore(path)
            rows = store.db.execute("SELECT attempts,last_error FROM outbox WHERE message_id='m2'").fetchone()
            self.assertEqual(rows, (1, "connection refused"))
            store.db.execute("UPDATE outbox SET next_attempt=0 WHERE message_id='m2'"); store.db.commit()
            self.assertEqual(await store.pending(), [msg])
            await store.mark_delivered("m2")
            self.assertEqual(await store.pending(), [])
            await store.close()


    async def test_real_two_node_mutual_tls_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def run(*args):
                subprocess.run(args, check=True, capture_output=True, text=True)
            run("openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                "-keyout", str(root/"ca.key"), "-out", str(root/"ca.crt"),
                "-subj", "/CN=EUPN Test CA", "-days", "2",
                "-addext", "basicConstraints=critical,CA:TRUE",
                "-addext", "keyUsage=critical,keyCertSign,cRLSign",
                "-addext", "subjectKeyIdentifier=hash")
            for node_id in ("node-a", "node-b"):
                key, csr, cert = root/f"{node_id}.key", root/f"{node_id}.csr", root/f"{node_id}.crt"
                ext = root/f"{node_id}.ext"
                ext.write_text("subjectAltName=DNS:localhost,URI:spiffe://eupn/"+node_id+"\nextendedKeyUsage=serverAuth,clientAuth\n")
                run("openssl", "req", "-new", "-newkey", "rsa:2048", "-nodes",
                    "-keyout", str(key), "-out", str(csr), "-subj", f"/CN={node_id}")
                run("openssl", "x509", "-req", "-in", str(csr), "-CA", str(root/"ca.crt"),
                    "-CAkey", str(root/"ca.key"), "-CAcreateserial", "-out", str(cert),
                    "-days", "2", "-extfile", str(ext))
            def free_port():
                with socket.socket() as sock:
                    sock.bind(("127.0.0.1", 0)); return sock.getsockname()[1]
            receiver_port, sender_port = free_port(), free_port()
            receiver = EUPNNode(NodeConfig("node-b", "127.0.0.1", receiver_port,
                root/"b.db", root/"node-b.crt", root/"node-b.key", root/"ca.crt",
                frozenset({"node-a"})))
            sender = EUPNNode(NodeConfig("node-a", "127.0.0.1", sender_port,
                root/"a.db", root/"node-a.crt", root/"node-a.key", root/"ca.crt",
                frozenset({"node-b"}), peer_routes={"node-b": ("localhost", receiver_port)},
                retry_interval=0.1))
            try:
                await sender.start()
                msg = {"id":"retry-proof","from":"node-a","to":"node-b",
                       "type":"integration.retry","sent_at":123.0,"payload":{"proof":True}}
                await sender.store.queue(msg)
                await sender.retry_once()  # receiver is offline: message remains queued
                self.assertEqual(sender.store.db.execute(
                    "SELECT attempts FROM outbox WHERE message_id='retry-proof'").fetchone()[0], 1)
                await receiver.start()
                sender.store.db.execute("UPDATE outbox SET next_attempt=0 WHERE message_id='retry-proof'")
                sender.store.db.commit()
                await sender.retry_once()  # receiver online: queued message is delivered
                row = receiver.store.db.execute(
                    "SELECT sender,recipient,message_type FROM inbox WHERE message_id='retry-proof'").fetchone()
                self.assertEqual(row, ("node-a", "node-b", "integration.retry"))
                self.assertIsNotNone(sender.store.db.execute(
                    "SELECT delivered_at FROM outbox WHERE message_id='retry-proof'").fetchone()[0])
            finally:
                await sender.close()
                await receiver.close()

if __name__ == "__main__": unittest.main()
