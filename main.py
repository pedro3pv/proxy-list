"""
proxy_collector.py  — com verificação assíncrona de proxies (timeout 500ms)
"""

import re
import json
import csv
import io
import asyncio
import time
import requests
import aiohttp
from typing import Set
from itertools import combinations

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
VERIFY_TIMEOUT_MS  = 3000          # proxies com latência > 500ms são descartados
VERIFY_CONCURRENCY = 30000          # conexões simultâneas
VERIFY_TEST_URL    = "https://httpbin.org/ip"  # URL usada para testar o proxy

SOURCES = [
    # ── Zaeem20/FREE_PROXIES_LIST  (atualizado a cada 10 min)
    {"url": "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",    "format": "txt_ip_port", "protocol": "http",   "name": "Zaeem20/http"},
    {"url": "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/https.txt",   "format": "txt_ip_port", "protocol": "https",  "name": "Zaeem20/https"},
    {"url": "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks4.txt",  "format": "txt_ip_port", "protocol": "socks4", "name": "Zaeem20/socks4"},

    # ── iplocate/free-proxy-list  (verificados, atualizado a cada 30 min)
    {"url": "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/protocols/http.txt",   "format": "txt_ip_port", "protocol": "http",   "name": "iplocate/http"},
    {"url": "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/protocols/https.txt",  "format": "txt_ip_port", "protocol": "https",  "name": "iplocate/https"},
    {"url": "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/protocols/socks4.txt", "format": "txt_ip_port", "protocol": "socks4", "name": "iplocate/socks4"},
    {"url": "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/protocols/socks5.txt", "format": "txt_ip_port", "protocol": "socks5", "name": "iplocate/socks5"},
    # all-proxies.txt tem formato proto://ip:port
    {"url": "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/all-proxies.txt",      "format": "txt_proto_prefix", "protocol": None, "name": "iplocate/all"},

    # ── rdavydov/proxy-list  (atualizado a cada 30 min, tem pasta proxies_anonymous também)
    {"url": "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",    "format": "txt_ip_port", "protocol": "http",   "name": "rdavydov/http"},
    {"url": "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt",  "format": "txt_ip_port", "protocol": "socks4", "name": "rdavydov/socks4"},
    {"url": "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt",  "format": "txt_ip_port", "protocol": "socks5", "name": "rdavydov/socks5"},
    # versão anônimos somente
    {"url": "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous/http.txt",   "format": "txt_ip_port", "protocol": "http",   "name": "rdavydov/anon-http"},
    {"url": "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous/socks4.txt", "format": "txt_ip_port", "protocol": "socks4", "name": "rdavydov/anon-socks4"},
    {"url": "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous/socks5.txt", "format": "txt_ip_port", "protocol": "socks5", "name": "rdavydov/anon-socks5"},

    # ── proxygenerator1/ProxyGenerator  (ALL.txt = proto://ip:port, atualizado a cada hora)
    # ALL/ALL.txt tem 160 KB — proto://ip:port
    {"url": "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/main/ALL/ALL.txt",          "format": "txt_proto_prefix", "protocol": None, "name": "ProxyGenerator/all"},
    # MostStable — verificados e mais estáveis
    {"url": "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/main/MostStable/http.txt",  "format": "txt_ip_port", "protocol": "http",   "name": "ProxyGenerator/stable-http"},
    {"url": "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/main/MostStable/https.txt", "format": "txt_ip_port", "protocol": "https",  "name": "ProxyGenerator/stable-https"},
    {"url": "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/main/MostStable/socks4.txt","format": "txt_ip_port", "protocol": "socks4", "name": "ProxyGenerator/stable-socks4"},
    {"url": "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/main/MostStable/socks5.txt","format": "txt_ip_port", "protocol": "socks5", "name": "ProxyGenerator/stable-socks5"},

    # ── ProxyScrape API — variantes extras (diferentes filtros)
    {
        "url": (
            "https://api.proxyscrape.com/v4/free-proxy-list/get"
            "?request=display_proxies&proxy_format=protocolipport&format=json"
            "&anonymity=elite,anonymous&limit=10000"
        ),
        "format": "json_proxyscrape", "protocol": None, "name": "proxyscrape/anonymous",
    },
    {
        "url": (
            "https://api.proxyscrape.com/v4/free-proxy-list/get"
            "?request=display_proxies&proxy_format=protocolipport&format=json"
            "&protocol=socks5&limit=10000"
        ),
        "format": "json_proxyscrape", "protocol": None, "name": "proxyscrape/socks5-only",
    },

    # ── fate0/proxylist  (JSON com estrutura própria — ver parser abaixo)
    {"url": "https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list",
    "format": "json_fate0", "protocol": None, "name": "fate0/all"},

    # ── a2u/free-proxy-list  (TXT simples ip:port, atualizado a cada hora)
    {"url": "https://raw.githubusercontent.com/a2u/free-proxy-list/master/proxy-list.txt",
    "format": "txt_ip_port", "protocol": "http", "name": "a2u/http"},

    # ── clarketm/proxy-list  (TXT: ip:port -- country -- type -- latency)
    # O proxy-list-raw.txt tem só ip:port, ideal para parse simples
    {"url": "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",   "format": "txt_ip_port",      "protocol": "http",   "name": "clarketm/http"},

    # ── hookzof/socks5_list  (TXT simples: ip:port — atualizado constantemente)
    {"url": "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",            "format": "txt_ip_port",      "protocol": "socks5", "name": "hookzof/socks5"},

    # ── roosterkid/openproxylist  (TXT simples: ip:port — atualizado a cada hora)
    {"url": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",     "format": "txt_ip_port",      "protocol": "https",  "name": "roosterkid/https"},
    {"url": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",    "format": "txt_ip_port",      "protocol": "socks4", "name": "roosterkid/socks4"},
    {"url": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",    "format": "txt_ip_port",      "protocol": "socks5", "name": "roosterkid/socks5"},

    # ── ErcinDedeoglu/proxies  (TXT simples: ip:port — pasta proxies/, ~100k+)
    {"url": "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",     "format": "txt_ip_port",      "protocol": "http",   "name": "ErcinDedeoglu/http"},
    {"url": "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt",    "format": "txt_ip_port",      "protocol": "https",  "name": "ErcinDedeoglu/https"},
    {"url": "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks4.txt",   "format": "txt_ip_port",      "protocol": "socks4", "name": "ErcinDedeoglu/socks4"},
    {"url": "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5.txt",   "format": "txt_ip_port",      "protocol": "socks5", "name": "ErcinDedeoglu/socks5"},

    # ── zloi-user/hideip.me  (TXT simples: ip:port — atualizado a cada 10 min)
    {"url": "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt",               "format": "txt_ip_port",      "protocol": "http",   "name": "hideip.me/http"},
    {"url": "https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt",              "format": "txt_ip_port",      "protocol": "https",  "name": "hideip.me/https"},
    {"url": "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks4.txt",             "format": "txt_ip_port",      "protocol": "socks4", "name": "hideip.me/socks4"},
    {"url": "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt",             "format": "txt_ip_port",      "protocol": "socks5", "name": "hideip.me/socks5"},

    # ── vakhov/fresh-proxy-list  (TXT simples: ip:port — atualizado diariamente)
    {"url": "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",         "format": "txt_ip_port",      "protocol": "http",   "name": "vakhov/http"},
    {"url": "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/https.txt",        "format": "txt_ip_port",      "protocol": "https",  "name": "vakhov/https"},
    {"url": "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks4.txt",       "format": "txt_ip_port",      "protocol": "socks4", "name": "vakhov/socks4"},
    {"url": "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks5.txt",       "format": "txt_ip_port",      "protocol": "socks5", "name": "vakhov/socks5"},

    # ── vakhov/fresh-proxy-list  (JSON: [{"ip":...,"port":...,"type":...}])
    {"url": "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/proxylist.json",   "format": "json_vakhov",      "protocol": None,     "name": "vakhov/json"},

    # ── MuRongPIG/Proxy-Master  (TXT simples: ip:port)
    {"url": "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",            "format": "txt_ip_port",      "protocol": "http",   "name": "MuRongPIG/http"},
    {"url": "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4.txt",          "format": "txt_ip_port",      "protocol": "socks4", "name": "MuRongPIG/socks4"},
    {"url": "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt",          "format": "txt_ip_port",      "protocol": "socks5", "name": "MuRongPIG/socks5"},
    # ── gfpcom/free-proxy-list  (GitHub Wiki — TXT proto://ip:port, +400k proxies!)
    {"url": "https://raw.githubusercontent.com/wiki/gfpcom/free-proxy-list/lists/http.txt",   "format": "txt_proto_prefix", "protocol": None, "name": "gfpcom/http"},
    {"url": "https://raw.githubusercontent.com/wiki/gfpcom/free-proxy-list/lists/https.txt",  "format": "txt_proto_prefix", "protocol": None, "name": "gfpcom/https"},
    {"url": "https://raw.githubusercontent.com/wiki/gfpcom/free-proxy-list/lists/socks4.txt", "format": "txt_proto_prefix", "protocol": None, "name": "gfpcom/socks4"},
    {"url": "https://raw.githubusercontent.com/wiki/gfpcom/free-proxy-list/lists/socks5.txt", "format": "txt_proto_prefix", "protocol": None, "name": "gfpcom/socks5"},

    # ── jetkai/proxy-list  (TXT simples ip:port, atualizado a cada hora)
    {"url": "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",   "format": "txt_ip_port", "protocol": "http",   "name": "jetkai/http"},
    {"url": "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",  "format": "txt_ip_port", "protocol": "https",  "name": "jetkai/https"},
    {"url": "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt", "format": "txt_ip_port", "protocol": "socks4", "name": "jetkai/socks4"},
    {"url": "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt", "format": "txt_ip_port", "protocol": "socks5", "name": "jetkai/socks5"},

    # ── MuRongPIG/Proxy-Master  (TXT simples ip:port)
    {"url": "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",   "format": "txt_ip_port", "protocol": "http",   "name": "MuRongPIG/http"},
    {"url": "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4.txt", "format": "txt_ip_port", "protocol": "socks4", "name": "MuRongPIG/socks4"},
    {"url": "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt", "format": "txt_ip_port", "protocol": "socks5", "name": "MuRongPIG/socks5"},

    # ── yemixzy/proxy-list  (TXT simples ip:port, atualizado a cada 3h)
    {"url": "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/http.txt",   "format": "txt_ip_port", "protocol": "http",   "name": "yemixzy/http"},
    {"url": "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/socks4.txt", "format": "txt_ip_port", "protocol": "socks4", "name": "yemixzy/socks4"},
    {"url": "https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/socks5.txt", "format": "txt_ip_port", "protocol": "socks5", "name": "yemixzy/socks5"},

    # ── casa-ls/proxy-list  (TXT simples ip:port, atualização diária)
    {"url": "https://raw.githubusercontent.com/casa-ls/proxy-list/main/http",   "format": "txt_ip_port", "protocol": "http",   "name": "casa-ls/http"},
    {"url": "https://raw.githubusercontent.com/casa-ls/proxy-list/main/socks4", "format": "txt_ip_port", "protocol": "socks4", "name": "casa-ls/socks4"},
    {"url": "https://raw.githubusercontent.com/casa-ls/proxy-list/main/socks5", "format": "txt_ip_port", "protocol": "socks5", "name": "casa-ls/socks5"},

    # ── Databay API  (JSON: {"data": [{"ip":..., "port":..., "protocol":...}]})
    {"url": "https://databay.com/api/v1/proxy-list?format=json&limit=1000",                   "format": "json_databay", "protocol": None, "name": "databay-api/all"},
    {"url": "https://databay.com/api/v1/proxy-list?protocol=socks5&format=json&limit=1000",   "format": "json_databay", "protocol": None, "name": "databay-api/socks5"},

    # ── PubProxy API  (JSON simples, 1 proxy aleatório por request — sem limite declarado)
    {"url": "http://pubproxy.com/api/proxy?limit=20&format=json&type=http",   "format": "json_pubproxy", "protocol": "http",   "name": "pubproxy/http"},
    {"url": "http://pubproxy.com/api/proxy?limit=20&format=json&type=socks5", "format": "json_pubproxy", "protocol": "socks5", "name": "pubproxy/socks5"},
    {"url": "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Https.txt",                  "format": "txt_ip_port",      "protocol": "https",  "name": "r00tee/Https"},
    {"url": "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks4.txt",                  "format": "txt_ip_port",      "protocol": "socks4", "name": "r00tee/Socks4"},
    {"url": "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks5.txt",                  "format": "txt_ip_port",      "protocol": "socks5", "name": "r00tee/Socks5"},
    {"url": "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/http.txt",       "format": "txt_ip_port",      "protocol": "http",   "name": "databay/http"},
    {"url": "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/socks5.txt",     "format": "txt_ip_port",      "protocol": "socks5", "name": "databay/socks5"},
    {"url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",               "format": "txt_ip_port",      "protocol": "http",   "name": "TheSpeedX/http"},
    {"url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",             "format": "txt_ip_port",      "protocol": "socks4", "name": "TheSpeedX/socks4"},
    {"url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",             "format": "txt_ip_port",      "protocol": "socks5", "name": "TheSpeedX/socks5"},
    {"url": "https://raw.githubusercontent.com/stormsia/proxy-list/main/working_proxies.txt",       "format": "txt_proto_prefix", "protocol": None,     "name": "stormsia/all"},
    {"url": "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt", "format": "txt_proto_prefix", "protocol": None,     "name": "proxifly/all"},
    {
        "url": (
            "https://api.proxyscrape.com/v4/free-proxy-list/get"
            "?request=display_proxies&proxy_format=protocolipport&format=json&limit=900000"
        ),
        "format": "json_proxyscrape",
        "protocol": None,
        "name": "proxyscrape/api",
    },
]

OUTPUT_FILE = "proxies_all.txt"

# ─────────────────────────────────────────────
# REGEX & CONSTANTES
# ─────────────────────────────────────────────
IP_PORT_RE      = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}$")
PROTO_PREFIX_RE = re.compile(r"^(https?|socks[45])://(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})$", re.IGNORECASE)
VALID_PROTOCOLS = {"http", "https", "socks4", "socks5"}


def normalize_protocol(proto: str) -> str:
    return proto.lower().strip()


# ─────────────────────────────────────────────
# PARSERS
# ─────────────────────────────────────────────
def parse_json_fate0(text: str) -> Set[str]:
    """
    fate0/proxylist — formato JSONL: uma linha = um JSON object.
    Estrutura: {"host": "1.2.3.4", "port": 8080, "type": "http"}
    """
    proxies = set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item  = json.loads(line)
            ip    = item.get("host", "").strip()
            port  = str(item.get("port", "")).strip()
            proto = normalize_protocol(item.get("type", ""))
            if ip and port and proto in VALID_PROTOCOLS:
                proxies.add(f"{proto}://{ip}:{port}")
        except json.JSONDecodeError:
            continue
    return proxies

def parse_json_vakhov(text: str) -> Set[str]:
    """
    vakhov/fresh-proxy-list proxylist.json
    Estrutura: [{"ip": "1.2.3.4", "port": "8080", "type": "http", ...}]
    """
    proxies = set()
    try:
        items = json.loads(text)
        if not isinstance(items, list):
            items = items.get("data", [])
        for item in items:
            ip    = item.get("ip", "").strip()
            port  = str(item.get("port", "")).strip()
            proto = normalize_protocol(item.get("type", ""))
            if ip and port and proto in VALID_PROTOCOLS:
                proxies.add(f"{proto}://{ip}:{port}")
    except json.JSONDecodeError as e:
        print(f"  [ERRO JSON] {e}")
    return proxies

def parse_json_databay(text: str) -> Set[str]:
    """
    Databay API.
    Estrutura: {"data": [{"ip": "1.2.3.4", "port": 8080, "protocol": "http"}]}
    """
    proxies = set()
    try:
        data  = json.loads(text)
        items = data.get("data", [])
        for item in items:
            ip    = item.get("ip", "").strip()
            port  = str(item.get("port", "")).strip()
            proto = normalize_protocol(item.get("protocol", ""))
            if ip and port and proto in VALID_PROTOCOLS:
                proxies.add(f"{proto}://{ip}:{port}")
    except json.JSONDecodeError as e:
        print(f"  [ERRO JSON] {e}")
    return proxies


def parse_json_pubproxy(text: str, protocol: str) -> Set[str]:
    """
    PubProxy API.
    Estrutura: {"data": [{"ipPort": "1.2.3.4:8080", "type": "http"}]}
    """
    proxies = set()
    try:
        data  = json.loads(text)
        items = data.get("data", [])
        for item in items:
            ip_port = item.get("ipPort", "").strip()
            proto   = normalize_protocol(item.get("type", protocol))
            if ip_port and proto in VALID_PROTOCOLS:
                proxies.add(f"{proto}://{ip_port}")
    except json.JSONDecodeError as e:
        print(f"  [ERRO JSON] {e}")
    return proxies

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
            norm  = {k.lower().strip(): v for k, v in row.items()}
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
    "json_databay":     lambda text, src: parse_json_databay(text),
    "json_pubproxy":    lambda text, src: parse_json_pubproxy(text, src["protocol"]),
    "json_vakhov": lambda text, src: parse_json_vakhov(text),
    "json_fate0": lambda text, src: parse_json_fate0(text),
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
# VERIFICAÇÃO ASSÍNCRONA
# ─────────────────────────────────────────────
async def check_proxy(
    proxy_url: str,
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    timeout_s: float,
) -> tuple[str, bool, float]:
    """
    Retorna (proxy_url, is_alive, latency_ms).
    Testa HTTP e HTTPS via connector de proxy do aiohttp.
    SOCKS4/5 requer aiohttp-socks.
    """
    async with semaphore:
        t0 = time.monotonic()
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as s:
                async with s.get(
                    VERIFY_TEST_URL,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=timeout_s),
                    allow_redirects=False,
                ) as resp:
                    await resp.read()
                    latency = (time.monotonic() - t0) * 1000
                    return proxy_url, resp.status < 500, latency
        except Exception:
            latency = (time.monotonic() - t0) * 1000
            return proxy_url, False, latency


async def verify_all(proxies: list[str]) -> list[tuple[str, float]]:
    """
    Verifica todos os proxies em paralelo.
    Retorna lista de (proxy_url, latency_ms) dos que passaram.
    """
    timeout_s  = VERIFY_TIMEOUT_MS / 1000
    semaphore  = asyncio.Semaphore(VERIFY_CONCURRENCY)
    total      = len(proxies)

    print(f"\n🔍 Verificando {total:,} proxies (timeout={VERIFY_TIMEOUT_MS}ms, "
          f"concorrência={VERIFY_CONCURRENCY})...")

    # aiohttp não suporta socks nativamente — usa aiohttp-socks se disponível
    try:
        from aiohttp_socks import ProxyConnector  # noqa: F401
        socks_available = True
    except ImportError:
        socks_available = False
        print("  ⚠️  aiohttp-socks não instalado — proxies SOCKS4/5 serão pulados na verificação.")

    tasks = []
    skipped_socks = 0

    async with aiohttp.ClientSession() as session:
        for proxy in proxies:
            proto = proxy.split("://")[0].lower()
            if proto in ("socks4", "socks5") and not socks_available:
                skipped_socks += 1
                continue
            tasks.append(check_proxy(proxy, session, semaphore, timeout_s))

        results_raw = await asyncio.gather(*tasks)

    if skipped_socks:
        print(f"  ℹ️  {skipped_socks:,} proxies SOCKS pulados (instale aiohttp-socks para verificá-los).")

    alive   = [(url, lat) for url, ok, lat in results_raw if ok]
    dead    = total - len(alive) - skipped_socks
    avg_lat = sum(l for _, l in alive) / len(alive) if alive else 0

    print(f"  ✅ {len(alive):,} vivos  |  ❌ {dead:,} mortos  |  ⏭️  {skipped_socks:,} pulados")
    print(f"  📶 Latência média dos vivos: {avg_lat:.0f}ms")

    return alive


# ─────────────────────────────────────────────
# ANÁLISE DE SOBREPOSIÇÃO
# ─────────────────────────────────────────────
def overlap_report(source_map: dict[str, Set[str]]) -> None:
    names = list(source_map.keys())
    print("\n" + "─" * 60)
    print("📊 RELATÓRIO DE SOBREPOSIÇÃO ENTRE FONTES")
    print("─" * 60)

    print("\n[Tamanho de cada fonte]")
    for name, proxies in source_map.items():
        print(f"  {name:<30} {len(proxies):>7,} proxies")

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
async def amain():
    source_map: dict[str, Set[str]] = {}

    # ── 1. Coleta e parse
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

    # ── 2. Relatório de sobreposição
    overlap_report(source_map)

    # ── 3. Merge sem duplicatas
    all_proxies = sorted(set().union(*source_map.values()))
    print(f"\n🗂  Total único antes da verificação: {len(all_proxies):,}")

    # ── 4. Verificação de disponibilidade (≤ 500ms)
    alive_list = await verify_all(all_proxies)

    # Ordena por latência crescente
    alive_list.sort(key=lambda x: x[1])
    valid_proxies = [url for url, _ in alive_list]

    # ── 5. Grava apenas os proxies vivos
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_proxies) + "\n")

    print(f"\n✅ {len(valid_proxies):,} proxies vivos gravados em '{OUTPUT_FILE}' "
          f"(ordenados por latência)")


def main():
    asyncio.run(amain())


if __name__ == "__main__":
    main()
