# 🌐 Massive Free Proxy List

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/pedro3pv/proxy-list/collect-proxies.yml?label=Proxy%20Collection&style=flat-square)](https://github.com/pedro3pv/proxy-list/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)

Este repositório coleta, deduplica e **testa automaticamente** dezenas de milhares de proxies públicos (`HTTP`, `HTTPS`, `SOCKS4`, `SOCKS5`) extraídos das maiores fontes open-source do GitHub e APIs de proxy. 

Todos os dias, um [GitHub Action](.github/workflows/collect-proxies.yml) percorre mais de 25 fontes massivas, unifica as listas, testa a conexão de forma assíncrona (mantendo apenas proxies com latência < 500ms) e publica um arquivo `proxies_all.txt` limpo e recém-verificado.

---

## 📦 Download da Lista Mais Recente

Você pode baixar a lista atualizada automaticamente (gerada diariamente) acessando a página de Releases:

👉 **[Baixar proxies_all.txt (Latest Release)](https://github.com/pedro3pv/proxy-list/releases/latest)**

O arquivo exportado possui o seguinte formato (`protocolo://ip:porta`):
```text
http://1.2.3.4:8080
https://5.6.7.8:3128
socks4://9.10.11.12:1080
socks5://13.14.15.16:4145
```

---

## ⚙️ Como o script funciona?

1. **Coleta Bruta:** Baixa listas de proxies de TXTs, JSONs, APIs e repositórios em tempo real.
2. **Deduplicação:** Remove milhares de IPs repetidos usando _Sets_ em Python.
3. **Verificação Assíncrona:** Utiliza `aiohttp` e `aiohttp-socks` com 500 workers simultâneos para testar se cada IP está realmente vivo e respondendo em menos de 500ms.
4. **Publicação:** Gera um relatório de sobreposição entre as fontes e lança a lista final validada no GitHub Releases.

---

## 🚀 Como rodar localmente

Caso queira rodar o script de coleta e validação na sua própria máquina:

1. Clone o repositório:
   ```bash
   git clone https://github.com/pedro3pv/proxy-list.git
   cd proxy-list
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
   *(Dependências: `requests`, `aiohttp`, `aiohttp-socks`)*
3. Rode o validador:
   ```bash
   python main.py
   ```
   O script irá verificar os milhares de proxies e salvar apenas os vivos no arquivo `proxies_all.txt`.

---

## 🤝 Agradecimentos e Fontes (Credits)

Este projeto **não existiria** sem o incrível trabalho da comunidade open-source e das plataformas que mantêm essas listas atualizadas gratuitamente na internet. 

Um agradecimento gigantesco aos mantenedores dos repositórios e APIs originais que fornecem os dados brutos usados neste projeto:

### Repositórios do GitHub
- [TheSpeedX/PROXY-List](https://github.com/TheSpeedX/PROXY-List)
- [proxifly/free-proxy-list](https://github.com/proxifly/free-proxy-list)
-[ErcinDedeoglu/proxies](https://github.com/ErcinDedeoglu/proxies)
-[proxygenerator1/ProxyGenerator](https://github.com/proxygenerator1/ProxyGenerator)
-[gfpcom/free-proxy-list](https://github.com/gfpcom/free-proxy-list)
-[iplocate/free-proxy-list](https://github.com/iplocate/free-proxy-list)
- [clarketm/proxy-list](https://github.com/clarketm/proxy-list)
- [r00tee/Proxy-List](https://github.com/r00tee/Proxy-List)
- [databay-labs/free-proxy-list](https://github.com/databay-labs/free-proxy-list)
- [stormsia/proxy-list](https://github.com/stormsia/proxy-list)
- [jetkai/proxy-list](https://github.com/jetkai/proxy-list)
- [MuRongPIG/Proxy-Master](https://github.com/MuRongPIG/Proxy-Master)
-[yemixzy/proxy-list](https://github.com/yemixzy/proxy-list)
-[casa-ls/proxy-list](https://github.com/casa-ls/proxy-list)
-[hookzof/socks5_list](https://github.com/hookzof/socks5_list)
-[roosterkid/openproxylist](https://github.com/roosterkid/openproxylist)
- [zloi-user/hideip.me](https://github.com/zloi-user/hideip.me)
- [vakhov/fresh-proxy-list](https://github.com/vakhov/fresh-proxy-list)
-[Zaeem20/FREE_PROXIES_LIST](https://github.com/Zaeem20/FREE_PROXIES_LIST)
- [rdavydov/proxy-list](https://github.com/rdavydov/proxy-list)
- [fate0/proxylist](https://github.com/fate0/proxylist)
- [a2u/free-proxy-list](https://github.com/a2u/free-proxy-list)

### APIs de Proxy Públicas
- [ProxyScrape](https://proxyscrape.com/)
- [Databay API](https://databay.com/)
- [PubProxy](http://pubproxy.com/)

*(Se você é o dono de algum desses repositórios e deseja ser removido da coleta, por favor, abra uma issue).*

---

## ⚠️ Aviso Legal e Ético

- **Privacidade e Segurança:** Proxies públicos gratuitos podem ser inseguros. Evite enviar dados sensíveis, senhas, tokens ou dados bancários através de proxies de terceiros sem criptografia forte (HTTPS).
- **Finalidade:** Este projeto tem fins puramente educacionais e de pesquisa de redes. O uso dos proxies coletados para atividades ilícitas, ataques DDoS ou sobrecarga de servidores não é aprovado e é de inteira responsabilidade do usuário final.
- **Volatilidade:** Proxies públicos têm um tempo de vida (TTL) muito curto. Um proxy que está vivo no momento da coleta pode ficar offline minutos depois.

---

## 📄 Licença

Este projeto está sob a **Licença MIT**. Sinta-se à vontade para clonar, modificar, distribuir e usar em seus projetos pessoais ou comerciais, desde que mantenha os créditos aos respectivos autores.

Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
