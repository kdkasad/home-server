#!/usr/bin/env python3
"""Prometheus exporter for nftables named counters."""

import json
import subprocess
import sys
from time import sleep
from prometheus_client.core import CounterMetricFamily, REGISTRY
from prometheus_client.registry import Collector
from prometheus_client import start_http_server


LISTEN_PORT = 9101


# Sample data:
# {
#   "nftables": [
#     {
#       "metainfo": {
#         "version": "1.0.6",
#         "release_name": "Lester Gooch #5",
#         "json_schema_version": 1
#       }
#     },
#     {
#       "counter": {
#         "family": "bridge",
#         "name": "box_rx",
#         "table": "accounting",
#         "handle": 4,
#         "packets": 158611,
#         "bytes": 142920056
#       }
#     }
#   ]
# }


class NftablesCollector(Collector):
    def collect(self):
        try:
            result = subprocess.check_output(
                ["nft", "-j", "list", "counters"],
                text=True,
                timeout=5,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"nft command failed: {e}", file=sys.stderr)
            return

        try:
            data = json.loads(result)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"nft command returned invalid JSON: {e}", file=sys.stderr)
            return

        packets = CounterMetricFamily(
            "nftables_counter_packets",
            "Packets matched by nftables named counter",
            labels=["table", "family", "name"],
        )
        bytes_ = CounterMetricFamily(
            "nftables_counter_bytes",
            "Bytes matched by nftables named counter",
            labels=["table", "family", "name"],
        )

        for entry in data.get("nftables", []):
            counter = entry.get("counter")
            if not counter:
                continue
            labels = (counter["table"], counter["family"], counter["name"])
            packets.add_metric(labels, counter["packets"])
            bytes_.add_metric(labels, counter["bytes"])

        yield packets
        yield bytes_


def main():
    REGISTRY.register(NftablesCollector())
    start_http_server(LISTEN_PORT)
    while True:
        sleep(3600)


if __name__ == "__main__":
    main()
