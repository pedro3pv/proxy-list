import re
import json
import csv
import io
from typing import Set
from itertools import combinations

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
