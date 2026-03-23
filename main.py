"""
proxy_collector.py — coleta, deduplica e publica a lista bruta.
A verificação (TCP/HTTP) é feita pelo usuário via proxy_checker.py.
"""

import re
import time
import os
from typing import Set

from parses import FORMAT_PARSERS
from sources import SOURCES
import requests

OUTPUT_FILE = "proxies_all.txt"

def fetch(url: str) -> str | None:
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "proxy-collector/1.0"})
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"  [ERRO] {e}")
        return None

def overlap_report(source_map: dict[str, Set[str]]) -> None:
    print("\n" + "─" * 60)
    for name, proxies in source_map.items():
        print(f"  {name:<35} {len(proxies):>7,}")
    union_size = len(set().union(*source_map.values()))
    total_raw  = sum(len(v) for v in source_map.values())
    removed    = total_raw - union_size
    print(f"\n  Bruto: {total_raw:,}  Único: {union_size:,}  "
          f"Removidos: {removed:,} ({removed/total_raw*100:.1f}%)")
    print("─" * 60)

def main():
    t0         = time.monotonic()
    source_map : dict[str, Set[str]] = {}

    for src in SOURCES:
        name, fmt, url = src["name"], src["format"], src["url"]
        print(f"→ [{name}] {url[:80]}...")
        text = fetch(url)
        if not text:
            continue
        parser = FORMAT_PARSERS.get(fmt)
        if not parser:
            continue
        parsed = parser(text, src)
        source_map[name] = parsed
        print(f"  {len(parsed):,} proxies.")

    overlap_report(source_map)

    all_proxies = sorted(set().union(*source_map.values()))
    print(f"\n🗂  Total único: {len(all_proxies):,}")

    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(all_proxies) + "\n")

    elapsed = time.monotonic() - t0
    print(f"✅ Lista bruta salva em '{OUTPUT_FILE}'")
    print(f"⏱  Tempo total: {elapsed:.1f}s")

if __name__ == "__main__":
    main()
