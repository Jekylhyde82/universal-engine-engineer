"""EUPN node CLI."""
import argparse
import asyncio
import json
import logging
import os
from pathlib import Path
from .node import EUPNNode, NodeConfig

def main() -> None:
    p = argparse.ArgumentParser(description="Run a Universal Private Network node")
    p.add_argument("--node-id", default=os.getenv("EUPN_NODE_ID"))
    p.add_argument("--host", default=os.getenv("EUPN_HOST", "0.0.0.0"))
    p.add_argument("--port", type=int, default=int(os.getenv("EUPN_PORT", "7443")))
    p.add_argument("--database", type=Path, default=Path(os.getenv("EUPN_DATABASE", "./var/eupn.db")))
    p.add_argument("--cert", type=Path, default=Path(os.getenv("EUPN_CERT", "./certs/node.crt")))
    p.add_argument("--key", type=Path, default=Path(os.getenv("EUPN_KEY", "./certs/node.key")))
    p.add_argument("--ca", type=Path, default=Path(os.getenv("EUPN_CA", "./certs/ca.crt")))
    p.add_argument("--allowed-peers", default=os.getenv("EUPN_ALLOWED_PEERS", ""))
    p.add_argument("--log-level", default=os.getenv("EUPN_LOG_LEVEL", "INFO"))
    a = p.parse_args()
    if not a.node_id:
        p.error("--node-id or EUPN_NODE_ID is required")
    logging.basicConfig(level=getattr(logging, a.log_level.upper(), logging.INFO))
    config = NodeConfig(a.node_id, a.host, a.port, a.database, a.cert, a.key, a.ca,
                        frozenset(x.strip() for x in a.allowed_peers.split(",") if x.strip()))
    async def run():
        node = EUPNNode(config)
        await node.start()
        print(json.dumps(node.health(), sort_keys=True), flush=True)
        try:
            await node.serve_forever()
        finally:
            await node.close()
    asyncio.run(run())

if __name__ == "__main__":
    main()
