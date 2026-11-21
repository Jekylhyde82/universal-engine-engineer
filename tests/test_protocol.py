import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from eupn.node import MessageStore, ProtocolError, encode_frame, read_frame

class EUPNProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_round_trip(self):
        msg = {"id": "m1", "type": "ping"}
        reader = asyncio.StreamReader()
        reader.feed_data(encode_frame(msg))
        reader.feed_eof()
        self.assertEqual(await read_frame(reader), msg)

    async def test_oversized_frame_rejected(self):
        reader = asyncio.StreamReader()
        reader.feed_data((100).to_bytes(4, "big"))
        reader.feed_eof()
        with self.assertRaises(ProtocolError):
            await read_frame(reader, max_frame=32)

    async def test_non_object_json_rejected(self):
        raw = json.dumps(["not", "an", "envelope"]).encode()
        reader = asyncio.StreamReader()
        reader.feed_data(len(raw).to_bytes(4, "big") + raw)
        reader.feed_eof()
        with self.assertRaises(ProtocolError):
            await read_frame(reader)

    async def test_inbox_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MessageStore(Path(tmp) / "node.db")
            msg = {"id":"m1","from":"peer-a","to":"peer-b","type":"event",
                   "sent_at":123.0,"payload":{"n":9}}
            self.assertTrue(await store.receive(msg))
            self.assertFalse(await store.receive(msg))
            await store.close()

if __name__ == "__main__":
    unittest.main()
