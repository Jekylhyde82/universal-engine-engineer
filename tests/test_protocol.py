import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from eupn.node import MessageStore, ProtocolError, encode_frame, read_frame, peer_identity

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

if __name__ == "__main__": unittest.main()
