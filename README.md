# 🌐 Massive Free Proxy List

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/pedro3pv/proxy-list/collect-proxies.yml?label=Proxy%20Collection&style=flat-square)](https://github.com/pedro3pv/proxy-list/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)

Este repositório coleta e deduplica automaticamente mais de **1.8 milhão de proxies públicos** (`HTTP`, `HTTPS`, `SOCKS4`, `SOCKS5`) extraídos das maiores fontes open-source do GitHub e APIs de proxy.

A cada 3 horas, um [GitHub Action](.github/workflows/collect-proxies.yml) percorre mais de 25 fontes massivas, unifica e deduplica as listas, e publica o arquivo `proxies_all.txt` atualizado. A **verificação de proxies ativos é feita localmente pelo usuário** com o `proxy_checker.py` — assim você verifica com a sua própria rede, sem depender de infraestrutura externa.

---

## 📦 Download da Lista Mais Recente

👉 **[Baixar proxies_all.txt (Latest Release)](https://github.com/pedro3pv/proxy-list/releases/latest)**

> Lista atualizada automaticamente a cada 3 horas. Formato `protocolo://ip:porta`:
> ```
> http://1.2.3.4:8080
> https://5.6.7.8:3128
> socks4://9.10.11.12:1080
> socks5://13.14.15.16:4145
> ```

---

## ✅ Verificando Proxies Ativos

A lista bruta contém todos os proxies coletados — vivos e mortos. Para filtrar apenas os que estão **respondendo na sua rede**, use o `proxy_checker.py` incluído no repositório.

### Instalação rápida

```bash
git clone https://github.com/pedro3pv/proxy-list.git
cd proxy-list
pip install -r requirements.txt
```

### Uso

```bash
# Baixa a lista mais recente e verifica automaticamente
python proxy_checker.py --fetch https://github.com/pedro3pv/proxy-list/releases/latest/download/proxies_all.txt

# Verifica um arquivo local
python proxy_checker.py --input proxies_all.txt --output proxies_verified.txt

# Só TCP (2x mais rápido, sem HTTP verify)
python proxy_checker.py --fetch URL --tcp-only

# Ajusta concorrência e timeout (para máquinas mais potentes)
python proxy_checker.py --fetch URL --concurrency 8000 --timeout 1.0 --workers 16
```

### Parâmetros disponíveis

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `--fetch URL` | — | Baixa a lista desta URL antes de verificar |
| `--input` | `proxies_all.txt` | Arquivo de entrada |
| `--output` | `proxies_verified.txt` | Arquivo de saída |
| `--tcp-only` | `false` | Pula a fase HTTP (mais rápido) |
| `--concurrency` | `3000` | Conexões TCP simultâneas por worker |
| `--timeout` | `1.5` | Timeout TCP em segundos |
| `--http-concurrency` | `300` | Conexões HTTP simultâneas por worker |
| `--http-timeout` | `4.0` | Timeout HTTP em segundos |
| `--workers` | nº de CPUs | Processos paralelos |

> **Por que verificar localmente?** Proxies são sensíveis à localização de rede. Um proxy acessível de São Paulo pode estar inacessível de Frankfurt. Verificar na sua própria máquina garante resultados relevantes para o seu caso de uso.

---

## ⚙️ Como funciona a coleta

1. **Coleta bruta** — Baixa listas de proxies de TXTs, JSONs, APIs e repositórios em tempo real
2. **Deduplicação** — Remove duplicatas usando *Sets* em Python (de ~2.2M brutos para ~1.8M únicos)
3. **Publicação** — Gera relatório de sobreposição entre fontes e publica no GitHub Releases
4. **Frequência** — Roda automaticamente **a cada 3 horas** via GitHub Actions

---

## 🤝 Fontes (Credits)

Este projeto não existiria sem o trabalho da comunidade open-source. Agradecimento aos mantenedores:

### Repositórios do GitHub

- [TheSpeedX/PROXY-List](https://github.com/TheSpeedX/PROXY-List)
- [proxifly/free-proxy-list](https://github.com/proxifly/free-proxy-list)
- [ErcinDedeoglu/proxies](https://github.com/ErcinDedeoglu/proxies)
- [proxygenerator1/ProxyGenerator](https://github.com/proxygenerator1/ProxyGenerator)
- [gfpcom/free-proxy-list](https://github.com/gfpcom/free-proxy-list)
- [iplocate/free-proxy-list](https://github.com/iplocate/free-proxy-list)
- [clarketm/proxy-list](https://github.com/clarketm/proxy-list)
- [r00tee/Proxy-List](https://github.com/r00tee/Proxy-List)
- [databay-labs/free-proxy-list](https://github.com/databay-labs/free-proxy-list)
- [stormsia/proxy-list](https://github.com/stormsia/proxy-list)
- [jetkai/proxy-list](https://github.com/jetkai/proxy-list)
- [MuRongPIG/Proxy-Master](https://github.com/MuRongPIG/Proxy-Master)
- [yemixzy/proxy-list](https://github.com/yemixzy/proxy-list)
- [casa-ls/proxy-list](https://github.com/casa-ls/proxy-list)
- [hookzof/socks5_list](https://github.com/hookzof/socks5_list)
- [roosterkid/openproxylist](https://github.com/roosterkid/openproxylist)
- [zloi-user/hideip.me](https://github.com/zloi-user/hideip.me)
- [vakhov/fresh-proxy-list](https://github.com/vakhov/fresh-proxy-list)
- [Zaeem20/FREE_PROXIES_LIST](https://github.com/Zaeem20/FREE_PROXIES_LIST)
- [rdavydov/proxy-list](https://github.com/rdavydov/proxy-list)
- [fate0/proxylist](https://github.com/fate0/proxylist)
- [a2u/free-proxy-list](https://github.com/a2u/free-proxy-list)

### APIs Públicas

- [ProxyScrape](https://proxyscrape.com/)
- [Databay API](https://databay.com/)
- [PubProxy](http://pubproxy.com/)

> Se você é o dono de algum desses repositórios e deseja ser removido da coleta, por favor abra uma [issue](https://github.com/pedro3pv/proxy-list/issues).

---

## ⚠️ Aviso Legal e Ético

- **Segurança** — Proxies públicos gratuitos podem ser inseguros. Evite enviar dados sensíveis através de proxies de terceiros sem criptografia forte (HTTPS)
- **Finalidade** — Este projeto tem fins puramente educacionais e de pesquisa de redes. O uso dos proxies para atividades ilícitas é de inteira responsabilidade do usuário final
- **Volatilidade** — Proxies públicos têm TTL muito curto. Um proxy vivo no momento da coleta pode ficar offline minutos depois. Use o `proxy_checker.py` para verificar em tempo real

---

## 📄 Licença

Este projeto está sob a **Licença MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.