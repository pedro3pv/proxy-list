"""
proxy_collector.py  — com análise de sobreposição entre fontes
"""

import re
import json
import csv
import io
import requests
from typing import Set
from itertools import combinations

SOURCES = [
    {"url": "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Https.txt",                           "format": "txt_ip_port",      "protocol": "https",  "name": "r00tee/Https"},
    {"url": "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks4.txt",                           "format": "txt_ip_port",      "protocol": "socks4", "name": "r00tee/Socks4"},
    {"url": "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks5.txt",                           "format": "txt_ip_port",      "protocol": "socks5", "name": "r00tee/Socks5"},
    {"url": "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/http.txt",                "format": "txt_ip_port",      "protocol": "http",   "name": "databay/http"},
    {"url": "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/socks5.txt",              "format": "txt_ip_port",      "protocol": "socks5", "name": "databay/socks5"},
    {"url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",                        "format": "txt_ip_port",      "protocol": "http",   "name": "TheSpeedX/http"},
    {"url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",                      "format": "txt_ip_port",      "protocol": "socks4", "name": "TheSpeedX/socks4"},
    {"url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",                      "format": "txt_ip_port",      "protocol": "socks5", "name": "TheSpeedX/socks5"},
    {"url": "https://raw.githubusercontent.com/stormsia/proxy-list/main/working_proxies.txt",                "format": "txt_proto_prefix", "protocol": None,     "name": "stormsia/all"},
    {"url": "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt",          "format": "txt_proto_prefix", "protocol": None,     "name": "proxifly/all"},
    {
        "url": (
            "https://api.proxyscrape.com/v4/free-proxy-list/get"
            "?request=display_proxies&proxy_format=protocolipport&format=json&limit=10000"
        ),
        "format": "json_proxyscrape",
        "protocol": None,
        "name": "proxyscrape/api",
    },
]

OUTPUT_FILE = "proxies_all.txt"

IP_PORT_RE     = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}$")
PROTO_PREFIX_RE = re.compile(r"^(https?|socks[45])://(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})$", re.IGNORECASE)
VALID_PROTOCOLS = {"http", "https", "socks4", "socks5"}


def normalize_protocol(proto: str) -> str:
    return proto.lower().strip()


def parse_txt_ip_port(text: str, protocol: str) -> Set[str]:
    proxies = set()
    for line in text.splitlines():
        line = line.strip()
        if IP_PORT_RE.match(line):
            proxies.add(f"{protocol}://{line}")
    return proxies


def parse_txt_proto_prefix(text: str) -> Set[str]:
    proxies = set()
    for line in text.splitlines():
        line = line.strip()
        m = PROTO_PREFIX_RE.match(line)
        if m:
            proto = normalize_protocol(m.group(1))
            if proto in VALID_PROTOCOLS:
                proxies.add(f"{proto}://{m.group(2)}:{m.group(3)}")
    return proxies


def parse_csv_proxifly(text: str) -> Set[str]:
    proxies = set()
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        try:
            norm = {k.lower().strip(): v for k, v in row.items()}
            ip    = norm.get("ip", "").strip()
            port  = norm.get("port", "").strip()
            proto = normalize_protocol(norm.get("protocol", norm.get("type", "")))
            if ip and port and proto in VALID_PROTOCOLS:
                proxies.add(f"{proto}://{ip}:{port}")
        except Exception:
            continue
    return proxies


def parse_json_proxyscrape(text: str) -> Set[str]:
    proxies = set()
    try:
        data  = json.loads(text)
        items = data if isinstance(data, list) else data.get("proxies", [])
        for item in items:
            raw = (item.get("proxy") or f"{item.get('ip','')}:{item.get('port','')}").strip()
            m   = PROTO_PREFIX_RE.match(raw)
            if m:
                proto = normalize_protocol(m.group(1))
                if proto in VALID_PROTOCOLS:
                    proxies.add(f"{proto}://{m.group(2)}:{m.group(3)}")
    except json.JSONDecodeError as e:
        print(f"  [ERRO JSON] {e}")
    return proxies


FORMAT_PARSERS = {
    "txt_ip_port":      lambda text, src: parse_txt_ip_port(text, src["protocol"]),
    "txt_proto_prefix": lambda text, src: parse_txt_proto_prefix(text),
    "csv_proxifly":     lambda text, src: parse_csv_proxifly(text),
    "json_proxyscrape": lambda text, src: parse_json_proxyscrape(text),
}


def fetch(url: str) -> str | None:
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "proxy-collector/1.0"})
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"  [ERRO DOWNLOAD] {e}")
        return None


# ─────────────────────────────────────────────
# ANÁLISE DE SOBREPOSIÇÃO
# ─────────────────────────────────────────────
def overlap_report(source_map: dict[str, Set[str]]) -> None:
    names = list(source_map.keys())
    print("\n" + "─" * 60)
    print("📊 RELATÓRIO DE SOBREPOSIÇÃO ENTRE FONTES")
    print("─" * 60)

    # Total por fonte
    print("\n[Tamanho de cada fonte]")
    for name, proxies in source_map.items():
        print(f"  {name:<30} {len(proxies):>7,} proxies")

    # Sobreposições pares (só imprime se > 0)
    print("\n[Sobreposições entre pares de fontes]")
    has_overlap = False
    for a, b in combinations(names, 2):
        inter = source_map[a] & source_map[b]
        if inter:
            has_overlap = True
            pct_a = len(inter) / len(source_map[a]) * 100 if source_map[a] else 0
            pct_b = len(inter) / len(source_map[b]) * 100 if source_map[b] else 0
            print(f"  {a:<30} ∩  {b:<30} = {len(inter):>5,}  "
                  f"({pct_a:.1f}% de A | {pct_b:.1f}% de B)")
    if not has_overlap:
        print("  Nenhuma sobreposição encontrada entre pares.")

    # Total de duplicatas removidas
    union_size = len(set().union(*source_map.values()))
    total_raw  = sum(len(v) for v in source_map.values())
    removed    = total_raw - union_size
    print(f"\n[Resumo]")
    print(f"  Total bruto (com repetições) : {total_raw:>8,}")
    print(f"  Total após deduplicação      : {union_size:>8,}")
    print(f"  Entradas removidas           : {removed:>8,}  ({removed/total_raw*100:.1f}% do total)")
    print("─" * 60)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    source_map: dict[str, Set[str]] = {}  # name → set de proxies

    for src in SOURCES:
        name = src["name"]
        fmt  = src["format"]
        url  = src["url"]
        print(f"→ [{name}] {url[:80]}...")

        text = fetch(url)
        if not text:
            print("  Pulando (sem resposta).")
            continue

        parser = FORMAT_PARSERS.get(fmt)
        if not parser:
            print(f"  Parser '{fmt}' não encontrado, pulando.")
            continue

        parsed = parser(text, src)
        source_map[name] = parsed
        print(f"  {len(parsed):,} proxies carregados.")

    # ── Relatório de sobreposição ANTES de gravar
    overlap_report(source_map)

    # ── Merge final sem duplicatas
    all_proxies = set().union(*source_map.values())
    sorted_proxies = sorted(all_proxies)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted_proxies) + "\n")

    print(f"\n✅ {len(sorted_proxies):,} proxies únicos gravados em '{OUTPUT_FILE}'")


if __name__ == "__main__":
    main()
