"""
proxy_checker.py — verifica proxies localmente (TCP + HTTP).

Uso:
    # verifica o arquivo padrão (proxies_all.txt) e salva em proxies_verified.txt
    python proxy_checker.py

    # verifica um arquivo customizado
    python proxy_checker.py --input minha_lista.txt --output verificados.txt

    # só TCP (mais rápido, sem HTTP verify)
    python proxy_checker.py --tcp-only

    # ajusta concorrência e timeout
    python proxy_checker.py --concurrency 5000 --timeout 2.0

    # baixa a lista do GitHub antes de verificar
    python proxy_checker.py --fetch https://github.com/SEU_USUARIO/SEU_REPO/releases/latest/download/proxies_all.txt
"""

import re
import asyncio
import time
import os
import multiprocessing as mp
import argparse
import sys
import urllib.request
from itertools import islice


# ─────────────────────────────────────────────
# DEFAULTS (sobrescrevíveis via CLI)
# ─────────────────────────────────────────────
DEFAULT_INPUT = "proxies_all.txt"
DEFAULT_OUTPUT = "proxies_verified.txt"
DEFAULT_CONCURRENCY = 3000
DEFAULT_TIMEOUT_TCP = 1.5
DEFAULT_CONCURRENCY_HTTP = 300
DEFAULT_TIMEOUT_HTTP = 4.0
HTTP_TEST_URL = "http://httpbin.org/ip"


_IP_PORT_RE = re.compile(r"[a-z0-9+]+://(\d{1,3}(?:\.\d{1,3}){3}):(\d+)")


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    return f"{m:02d}m{s:02d}s"


def print_progress(phase, done, total_chunks, alive, dead, elapsed):
    pct = done / total_chunks * 100
    eta_s = (elapsed / done) * (total_chunks - done) if done else 0
    speed = alive / elapsed if elapsed > 0 else 0
    bar_len = 30
    filled = int(bar_len * done / total_chunks)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(
        f"\r  {phase} [{bar}] {pct:5.1f}%  "
        f"chunk {done}/{total_chunks}  "
        f"✅ {alive:,}  ❌ {dead:,}  "
        f"⚡ {speed:.0f} vivos/s  "
        f"⏱ {fmt_time(elapsed)} decorrido  "
        f"ETA {fmt_time(eta_s)}",
        end="", flush=True,
    )


def chunked(lst: list, size: int):
    it = iter(lst)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk


# ─────────────────────────────────────────────
# FASE 1 — TCP
# ─────────────────────────────────────────────
class TCPWorker:
    def __init__(self, timeout: float, concurrency: int):
        self.timeout = timeout
        self.concurrency = concurrency

    def __call__(self, chunk):
        try:
            return asyncio.run(self.run_chunk(chunk))
        except Exception as e:
            print(f"\n  [WORKER TCP ERRO] {e}")
            return []

    async def run_chunk(self, chunk):
        sem = asyncio.Semaphore(self.concurrency)
        results = await asyncio.gather(*[self.tcp_check(p, sem) for p in chunk])
        return [url for url, ok in results if ok]

    async def tcp_check(self, proxy_url: str, sem: asyncio.Semaphore) -> tuple[str, bool]:
        async with sem:
            m = _IP_PORT_RE.match(proxy_url)
            if not m:
                return proxy_url, False
            host, port = m.group(1), int(m.group(2))
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=self.timeout,
                )
                writer.close()
                await writer.wait_closed()
                return proxy_url, True
            except Exception:
                return proxy_url, False


# ─────────────────────────────────────────────
# FASE 2 — HTTP
# ─────────────────────────────────────────────
class HTTPWorker:
    def __init__(self, timeout: float, concurrency: int, test_url: str):
        self.timeout = timeout
        self.concurrency = concurrency
        self.test_url = test_url

    def __call__(self, chunk):
        try:
            return asyncio.run(self.run_chunk(chunk))
        except Exception as e:
            print(f"\n  [WORKER HTTP ERRO] {e}")
            return []

    async def run_chunk(self, chunk):
        import aiohttp
        sem = asyncio.Semaphore(self.concurrency)
        connector = aiohttp.TCPConnector(ssl=False, limit=self.concurrency)
        async with aiohttp.ClientSession(connector=connector) as session:
            results = await asyncio.gather(*[self.http_check(p, session, sem) for p in chunk])
        return [(url, lat) for url, ok, lat in results if ok]

    async def http_check(self, proxy_url: str, session, sem: asyncio.Semaphore):
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
                            self.test_url,
                            timeout=aiohttp.ClientTimeout(total=self.timeout),
                            allow_redirects=False,
                        ) as resp:
                            await resp.read()
                            return proxy_url, resp.status < 500, (time.monotonic() - t0) * 1000
                else:
                    import aiohttp
                    async with session.get(
                        self.test_url,
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                        allow_redirects=False,
                    ) as resp:
                        await resp.read()
                        return proxy_url, resp.status < 500, (time.monotonic() - t0) * 1000
            except Exception:
                return proxy_url, False, (time.monotonic() - t0) * 1000


# ─────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────
def run_phase(label: str, proxies: list, worker_fn, chunk_size: int,
              num_workers: int, timeout: float, concurrency: int) -> list:
    chunks = list(chunked(proxies, chunk_size))
    total = len(proxies)
    total_chunks = len(chunks)

    est = fmt_time(total / (num_workers * concurrency / timeout)) if total else "00m00s"
    print(f"\n{'⚡' if label == 'TCP' else '🌐'} Fase {label}")
    print(f"  {total:,} proxies  |  {total_chunks} chunks  |  "
          f"{num_workers} workers  |  timeout {timeout}s")
    print(f"  Estimativa inicial: ~{est}\n")

    t0 = time.monotonic()
    alive = []
    dead = 0

    with mp.Pool(processes=num_workers) as pool:
        for i, result in enumerate(pool.imap_unordered(worker_fn, chunks), 1):
            real_size = len(chunks[i - 1]) if i <= len(chunks) else chunk_size
            alive.extend(result)
            dead += real_size - len(result)
            elapsed = time.monotonic() - t0
            print_progress(label, i, total_chunks, len(alive), dead, elapsed)

    elapsed = time.monotonic() - t0
    total_dead = total - len(alive)
    print(f"\n\n  ✅ Fase {label} concluída em {fmt_time(elapsed)}")
    print(f"  Vivos  : {len(alive):,} ({len(alive)/total*100:.1f}%)" if total else "")
    print(f"  Mortos : {total_dead:,} ({total_dead/total*100:.1f}%)" if total else "")
    return alive


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(
        description="Verifica proxies localmente via TCP e HTTP.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--input", default=DEFAULT_INPUT,
                   help=f"Arquivo de entrada (padrão: {DEFAULT_INPUT})")
    p.add_argument("--output", default=DEFAULT_OUTPUT,
                   help=f"Arquivo de saída (padrão: {DEFAULT_OUTPUT})")
    p.add_argument("--fetch", default=None, metavar="URL",
                   help="Baixa a lista desta URL antes de verificar")
    p.add_argument("--tcp-only", action="store_true",
                   help="Pula a fase HTTP (mais rápido, menos preciso)")
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                   help=f"Conexões TCP simultâneas por worker (padrão: {DEFAULT_CONCURRENCY})")
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_TCP,
                   help=f"Timeout TCP em segundos (padrão: {DEFAULT_TIMEOUT_TCP})")
    p.add_argument("--http-concurrency", type=int, default=DEFAULT_CONCURRENCY_HTTP,
                   help=f"Conexões HTTP simultâneas por worker (padrão: {DEFAULT_CONCURRENCY_HTTP})")
    p.add_argument("--http-timeout", type=float, default=DEFAULT_TIMEOUT_HTTP,
                   help=f"Timeout HTTP em segundos (padrão: {DEFAULT_TIMEOUT_HTTP})")
    p.add_argument("--http-url", default=HTTP_TEST_URL,
                   help=f"URL de teste HTTP (padrão: {HTTP_TEST_URL})")
    p.add_argument("--workers", type=int, default=max(1, os.cpu_count()),
                   help="Número de processos paralelos (padrão: nº de CPUs)")
    p.add_argument("--chunk-size", type=int, default=50_000,
                   help="Proxies por chunk por worker (padrão: 50000)")
    return p.parse_args()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    args = parse_args()
    t_global = time.monotonic()

    # ── Download opcional ──────────────────────────────────────────────
    if args.fetch:
        print(f"⬇️  Baixando lista de {args.fetch} ...")
        try:
            urllib.request.urlretrieve(args.fetch, args.input)
            print(f"  Salvo em '{args.input}'")
        except Exception as e:
            print(f"  [ERRO] {e}")
            sys.exit(1)

    # ── Leitura ────────────────────────────────────────────────────────
    if not os.path.exists(args.input):
        print(f"❌ Arquivo '{args.input}' não encontrado.")
        print(f"  Use --fetch URL para baixar, ou --input para especificar o caminho.")
        sys.exit(1)

    with open(args.input) as f:
        proxies = [l.strip() for l in f if l.strip()]

    print(f"📂 {len(proxies):,} proxies carregados de '{args.input}'")
    print(f"⚙️  Workers: {args.workers}  |  Chunk: {args.chunk_size:,}  |  "
          f"TCP timeout: {args.timeout}s  |  HTTP timeout: {args.http_timeout}s")

    # ── Fase 1: TCP ────────────────────────────────────────────────────
    tcp_worker = TCPWorker(args.timeout, args.concurrency)
    tcp_alive = run_phase(
        "TCP", proxies, tcp_worker,
        args.chunk_size, args.workers, args.timeout, args.concurrency,
    )

    # ── Fase 2: HTTP ───────────────────────────────────────────────────
    if args.tcp_only or not tcp_alive:
        valid_proxies = tcp_alive
    else:
        http_worker = HTTPWorker(args.http_timeout, args.http_concurrency, args.http_url)
        http_results = run_phase(
            "HTTP", tcp_alive, http_worker,
            args.chunk_size, args.workers, args.http_timeout, args.http_concurrency,
        )
        # ordena por latência
        http_results.sort(key=lambda x: x[1])
        valid_proxies = [url for url, _ in http_results]

        avg_lat = sum(l for _, l in http_results) / len(http_results) if http_results else 0
        print(f"  Latência média: {avg_lat:.0f}ms")

    # ── Saída ──────────────────────────────────────────────────────────
    with open(args.output, "w") as f:
        f.write("\n".join(valid_proxies) + "\n")

    total_elapsed = time.monotonic() - t_global
    print(f"\n✅ {len(valid_proxies):,} proxies verificados salvos em '{args.output}'")
    print(f"⏱  Tempo total: {fmt_time(total_elapsed)}")


if __name__ == "__main__":
    main()
