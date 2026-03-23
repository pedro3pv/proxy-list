"""
proxy_collector.py — pipeline para 1.8M proxies
"""

import re
import asyncio
import time
import os
import multiprocessing as mp
from itertools import islice
from typing import Set

from parses import FORMAT_PARSERS
from sources import SOURCES
import requests

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
TCP_CONCURRENCY   = 3000       # por processo/worker
TCP_TIMEOUT_S     = 1.5        # agressivo — proxies ruins caem rápido
HTTP_CONCURRENCY  = 300        # por worker, fase 2
HTTP_TIMEOUT_S    = 4.0
HTTP_TEST_URL     = "http://httpbin.org/ip"

NUM_WORKERS       = max(1, os.cpu_count())   # 1 processo por CPU
CHUNK_SIZE        = 50_000     # proxies por worker por rodada

SKIP_HTTP_VERIFY  = False
OUTPUT_FILE       = "proxies_all.txt"

_IP_PORT_RE = re.compile(r"[a-z0-9+]+://(\d{1,3}(?:\.\d{1,3}){3}):(\d+)")

# ─────────────────────────────────────────────
# COLETA
# ─────────────────────────────────────────────
def fetch(url: str) -> str | None:
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "proxy-collector/1.0"})
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"  [ERRO] {e}")
        return None

# ─────────────────────────────────────────────
# FASE 1 — TCP CONNECT (roda dentro de cada worker)
# ─────────────────────────────────────────────
async def tcp_check(proxy_url: str, sem: asyncio.Semaphore) -> tuple[str, bool]:
    async with sem:
        m = _IP_PORT_RE.match(proxy_url)
        if not m:
            return proxy_url, False
        host, port = m.group(1), int(m.group(2))
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=TCP_TIMEOUT_S,
            )
            writer.close()
            await writer.wait_closed()
            return proxy_url, True
        except Exception:
            return proxy_url, False

async def run_tcp_chunk(chunk: list[str]) -> list[str]:
    sem = asyncio.Semaphore(TCP_CONCURRENCY)
    results = await asyncio.gather(*[tcp_check(p, sem) for p in chunk])
    return [url for url, ok in results if ok]

def worker_tcp(chunk: list[str]) -> list[str]:
    """Função executada em processo separado."""
    return asyncio.run(run_tcp_chunk(chunk))

# ─────────────────────────────────────────────
# FASE 2 — HTTP VERIFY (roda dentro de cada worker)
# ─────────────────────────────────────────────
async def http_check(proxy_url: str, session, sem: asyncio.Semaphore) -> tuple[str, bool, float]:
    proto = proxy_url.split("://")[0].lower()
    async with sem:
        t0 = time.monotonic()
        try:
            if proto in ("socks4", "socks5"):
                from aiohttp_socks import ProxyConnector
                import aiohttp
                conn = ProxyConnector.from_url(proxy_url, ssl=False)
                async with aiohttp.ClientSession(connector=conn) as s:
                    async with s.get(HTTP_TEST_URL,
                                     timeout=__import__("aiohttp").ClientTimeout(total=HTTP_TIMEOUT_S),
                                     allow_redirects=False) as resp:
                        await resp.read()
                        return proxy_url, resp.status < 500, (time.monotonic() - t0) * 1000
            else:
                async with session.get(
                    HTTP_TEST_URL,
                    proxy=proxy_url,
                    timeout=__import__("aiohttp").ClientTimeout(total=HTTP_TIMEOUT_S),
                    allow_redirects=False,
                ) as resp:
                    await resp.read()
                    return proxy_url, resp.status < 500, (time.monotonic() - t0) * 1000
        except Exception:
            return proxy_url, False, (time.monotonic() - t0) * 1000

async def run_http_chunk(chunk: list[str]) -> list[tuple[str, float]]:
    import aiohttp
    sem = asyncio.Semaphore(HTTP_CONCURRENCY)
    connector = aiohttp.TCPConnector(ssl=False, limit=HTTP_CONCURRENCY)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = await asyncio.gather(*[http_check(p, session, sem) for p in chunk])
    return [(url, lat) for url, ok, lat in results if ok]

def worker_http(chunk: list[str]) -> list[tuple[str, float]]:
    return asyncio.run(run_http_chunk(chunk))

# ─────────────────────────────────────────────
# CHUNKER
# ─────────────────────────────────────────────
def chunked(lst: list, size: int):
    it = iter(lst)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk

# ─────────────────────────────────────────────
# PIPELINE PARALELO
# ─────────────────────────────────────────────
def parallel_tcp(all_proxies: list[str]) -> list[str]:
    chunks = list(chunked(all_proxies, CHUNK_SIZE))
    total  = len(all_proxies)
    print(f"\n⚡ Fase 1 — TCP connect: {total:,} proxies em {len(chunks)} chunks "
          f"× {NUM_WORKERS} workers (timeout={TCP_TIMEOUT_S}s)...")
    t0 = time.monotonic()

    alive = []
    with mp.Pool(processes=NUM_WORKERS) as pool:
        for i, result in enumerate(pool.imap_unordered(worker_tcp, chunks), 1):
            alive.extend(result)
            pct = i / len(chunks) * 100
            elapsed = time.monotonic() - t0
            eta = (elapsed / i) * (len(chunks) - i)
            print(f"  chunk {i}/{len(chunks)} ({pct:.0f}%)  "
                  f"vivos até agora: {len(alive):,}  "
                  f"ETA: {eta:.0f}s", end="\r")

    elapsed = time.monotonic() - t0
    print(f"\n  ✅ {len(alive):,} portas abertas  |  ❌ {total - len(alive):,} fechadas")
    print(f"  ⏱  Fase 1: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    return alive

def parallel_http(tcp_alive: list[str]) -> list[tuple[str, float]]:
    chunks = list(chunked(tcp_alive, CHUNK_SIZE))
    total  = len(tcp_alive)
    print(f"\n🌐 Fase 2 — HTTP verify: {total:,} proxies em {len(chunks)} chunks "
          f"× {NUM_WORKERS} workers (timeout={HTTP_TIMEOUT_S}s)...")
    t0 = time.monotonic()

    alive = []
    with mp.Pool(processes=NUM_WORKERS) as pool:
        for i, result in enumerate(pool.imap_unordered(worker_http, chunks), 1):
            alive.extend(result)
            elapsed = time.monotonic() - t0
            eta = (elapsed / i) * (len(chunks) - i)
            print(f"  chunk {i}/{len(chunks)}  vivos: {len(alive):,}  ETA: {eta:.0f}s", end="\r")

    elapsed = time.monotonic() - t0
    print(f"\n  ✅ {len(alive):,} vivos  |  ❌ {total - len(alive):,} mortos")
    print(f"  ⏱  Fase 2: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    return alive

# ─────────────────────────────────────────────
# OVERLAP REPORT
# ─────────────────────────────────────────────
def overlap_report(source_map: dict[str, Set[str]]) -> None:
    from itertools import combinations
    print("\n" + "─" * 60)
    for name, proxies in source_map.items():
        print(f"  {name:<35} {len(proxies):>7,}")
    union_size = len(set().union(*source_map.values()))
    total_raw  = sum(len(v) for v in source_map.values())
    removed    = total_raw - union_size
    print(f"\n  Bruto: {total_raw:,}  Único: {union_size:,}  "
          f"Removidos: {removed:,} ({removed/total_raw*100:.1f}%)")
    print("─" * 60)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    source_map: dict[str, Set[str]] = {}

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

    # Fase 1
    tcp_alive = parallel_tcp(all_proxies)

    # Fase 2 (opcional)
    if SKIP_HTTP_VERIFY:
        valid_proxies = tcp_alive
    else:
        alive_list = parallel_http(tcp_alive)
        alive_list.sort(key=lambda x: x[1])
        valid_proxies = [url for url, _ in alive_list]

    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(valid_proxies) + "\n")

    print(f"\n✅ {len(valid_proxies):,} proxies em '{OUTPUT_FILE}'")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)  # compatível com macOS/Windows
    main()
