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
TCP_CONCURRENCY   = 3000
TCP_TIMEOUT_S     = 1.5
HTTP_CONCURRENCY  = 300
HTTP_TIMEOUT_S    = 4.0
HTTP_TEST_URL     = "http://httpbin.org/ip"

NUM_WORKERS       = max(1, os.cpu_count())
CHUNK_SIZE        = 50_000

SKIP_HTTP_VERIFY  = False
OUTPUT_FILE       = "proxies_all.txt"

_IP_PORT_RE = re.compile(r"[a-z0-9+]+://(\d{1,3}(?:\.\d{1,3}){3}):(\d+)")

# ─────────────────────────────────────────────
# HELPERS DE PROGRESSO
# ─────────────────────────────────────────────
def fmt_time(seconds: float) -> str:
    """Formata segundos em mm:ss ou hh:mm:ss."""
    seconds = max(0, int(seconds))
    h, rem  = divmod(seconds, 3600)
    m, s    = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    return f"{m:02d}m{s:02d}s"

def print_progress(
    phase: str,
    done: int,
    total_chunks: int,
    alive: int,
    dead: int,
    elapsed: float,
    phase_start: float,
) -> None:
    pct      = done / total_chunks * 100
    eta_s    = (elapsed / done) * (total_chunks - done) if done else 0
    speed    = alive / elapsed if elapsed > 0 else 0          # vivos/s
    bar_len  = 30
    filled   = int(bar_len * done / total_chunks)
    bar      = "█" * filled + "░" * (bar_len - filled)

    print(
        f"\r  {phase} [{bar}] {pct:5.1f}%  "
        f"chunk {done}/{total_chunks}  "
        f"✅ {alive:,}  ❌ {dead:,}  "
        f"⚡ {speed:.0f} vivos/s  "
        f"⏱ {fmt_time(elapsed)} decorrido  "
        f"ETA {fmt_time(eta_s)}",
        end="",
        flush=True,
    )

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
# FASE 1 — TCP CONNECT
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
    sem     = asyncio.Semaphore(TCP_CONCURRENCY)
    results = await asyncio.gather(*[tcp_check(p, sem) for p in chunk])
    return [url for url, ok in results if ok]

def worker_tcp(chunk: list[str]) -> list[str]:
    return asyncio.run(run_tcp_chunk(chunk))

# ─────────────────────────────────────────────
# FASE 2 — HTTP VERIFY
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
                    async with s.get(
                        HTTP_TEST_URL,
                        timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S),
                        allow_redirects=False,
                    ) as resp:
                        await resp.read()
                        return proxy_url, resp.status < 500, (time.monotonic() - t0) * 1000
            else:
                async with session.get(
                    HTTP_TEST_URL,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S),
                    allow_redirects=False,
                ) as resp:
                    await resp.read()
                    return proxy_url, resp.status < 500, (time.monotonic() - t0) * 1000
        except Exception:
            return proxy_url, False, (time.monotonic() - t0) * 1000

async def run_http_chunk(chunk: list[str]) -> list[tuple[str, float]]:
    import aiohttp
    sem       = asyncio.Semaphore(HTTP_CONCURRENCY)
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
    chunks       = list(chunked(all_proxies, CHUNK_SIZE))
    total        = len(all_proxies)
    total_chunks = len(chunks)

    print(f"\n⚡ Fase 1 — TCP connect")
    print(f"   {total:,} proxies  |  {total_chunks} chunks  |  "
          f"{NUM_WORKERS} workers  |  timeout {TCP_TIMEOUT_S}s")
    print(f"   Estimativa inicial: ~{fmt_time(total / (NUM_WORKERS * TCP_CONCURRENCY / TCP_TIMEOUT_S))}")
    print()

    t0    = time.monotonic()
    alive = []
    dead  = 0

    with mp.Pool(processes=NUM_WORKERS) as pool:
        for i, result in enumerate(pool.imap_unordered(worker_tcp, chunks), 1):
            chunk_alive = len(result)
            chunk_dead  = CHUNK_SIZE - chunk_alive  # aproximado
            alive.extend(result)
            dead  += chunk_dead
            elapsed = time.monotonic() - t0
            print_progress("TCP", i, total_chunks, len(alive), dead, elapsed, t0)

    elapsed = time.monotonic() - t0
    total_dead = total - len(alive)
    print(f"\n\n  ✅ Fase 1 concluída em {fmt_time(elapsed)}")
    print(f"  Portas abertas : {len(alive):,} ({len(alive)/total*100:.1f}%)")
    print(f"  Fechadas/timeout: {total_dead:,} ({total_dead/total*100:.1f}%)")
    return alive

def parallel_http(tcp_alive: list[str]) -> list[tuple[str, float]]:
    chunks       = list(chunked(tcp_alive, CHUNK_SIZE))
    total        = len(tcp_alive)
    total_chunks = len(chunks)

    print(f"\n🌐 Fase 2 — HTTP verify")
    print(f"   {total:,} proxies  |  {total_chunks} chunks  |  "
          f"{NUM_WORKERS} workers  |  timeout {HTTP_TIMEOUT_S}s")
    print(f"   Estimativa inicial: ~{fmt_time(total / (NUM_WORKERS * HTTP_CONCURRENCY / HTTP_TIMEOUT_S))}")
    print()

    t0    = time.monotonic()
    alive = []
    dead  = 0

    with mp.Pool(processes=NUM_WORKERS) as pool:
        for i, result in enumerate(pool.imap_unordered(worker_http, chunks), 1):
            chunk_alive = len(result)
            chunk_dead  = CHUNK_SIZE - chunk_alive
            alive.extend(result)
            dead  += chunk_dead
            elapsed = time.monotonic() - t0
            print_progress("HTTP", i, total_chunks, len(alive), dead, elapsed, t0)

    elapsed    = time.monotonic() - t0
    total_dead = total - len(alive)
    avg_lat    = sum(l for _, l in alive) / len(alive) if alive else 0
    print(f"\n\n  ✅ Fase 2 concluída em {fmt_time(elapsed)}")
    print(f"  Vivos  : {len(alive):,} ({len(alive)/total*100:.1f}%)")
    print(f"  Mortos : {total_dead:,} ({total_dead/total*100:.1f}%)")
    print(f"  Latência média: {avg_lat:.0f}ms")
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
    t_global = time.monotonic()
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

    tcp_alive = parallel_tcp(all_proxies)

    if SKIP_HTTP_VERIFY:
        valid_proxies = tcp_alive
    else:
        alive_list = parallel_http(tcp_alive)
        alive_list.sort(key=lambda x: x[1])
        valid_proxies = [url for url, _ in alive_list]

    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(valid_proxies) + "\n")

    total_elapsed = time.monotonic() - t_global
    print(f"\n✅ {len(valid_proxies):,} proxies gravados em '{OUTPUT_FILE}'")
    print(f"⏱  Tempo total: {fmt_time(total_elapsed)}")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
