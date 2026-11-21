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
            await store.failed_attempt("m2", "connection refused", 60)
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
                "-subj", "/CN=EUPN Test CA", "-days", "2")
            for node_id in ("node-a", "node-b"):
                key, csr, cert = root/f"{node_id}.key", root/f"{node_id}.csr", root/f"{node_id}.crt"
                ext = root/f"{node_id}.ext"
                ext.write_text("subjectAltName=DNS:localhost,URI:spiffe://eupn/"+node_id+"\\nextendedKeyUsage=serverAuth,clientAuth\\n")
                run("openssl", "req", "-new", "-newkey", "rsa:2048", "-nodes",
                    "-keyout", str(key), "-out", str(csr), "-subj", f"/CN={node_id}")
                run("openssl", "x509", "-req", "-in", str(csr), "-CA", str(root/"ca.crt"),
                    "-CAkey", str(root/"ca.key"), "-CAcreateserial", "-out", str(cert),
                    "-days", "2", "-extfile", str(ext))
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
            common = dict(host="127.0.0.1", port=port, trusted_ca=root/"ca.crt")
            receiver = EUPNNode(NodeConfig("node-b", database=root/"b.db",
                certificate=root/"node-b.crt", private_key=root/"node-b.key",
                allowed_peers=frozenset({"node-a"}), **common))
            sender = EUPNNode(NodeConfig("node-a", database=root/"a.db",
                certificate=root/"node-a.crt", private_key=root/"node-a.key",
                allowed_peers=frozenset({"node-b"}), **common))
            try:
                await receiver.start()
                ack = await sender.send("localhost", port, "node-b", "integration.test", {"proof": True})
                self.assertTrue(ack["accepted"])
                self.assertEqual(ack["by"], "node-b")
                row = receiver.store.db.execute("SELECT sender,recipient,message_type FROM inbox").fetchone()
                self.assertEqual(row, ("node-a", "node-b", "integration.test"))
            finally:
                await sender.close()
                await receiver.close()
\nif __name__ == "__main__": unittest.main()
