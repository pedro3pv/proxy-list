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
