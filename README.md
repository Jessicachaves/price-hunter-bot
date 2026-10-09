# Radar de Preços - Comparador Multilojas

Aplicativo em Python, FastAPI e Web moderna para **pesquisar, comparar preços e encontrar onde qualquer produto está mais barato** em tempo real nas principais lojas do Brasil (Amazon Brasil, KaBuM!, Mercado Livre, Magazine Luiza, Zoom/Buscapé e agregadores).

Possui **interface web interativa**, **bot do Telegram integrado** e **filtro de relevância** para priorizar ofertas diretas do item pesquisado.

<p align="center">
  <img src="assets/preview.png" alt="Radar de Preços - Interface Web" width="100%" />
</p>

---

## Principais Recursos

1. **Busca Paralela Multilojas**: Consulta os principais e-commerces e agregadores do Brasil em segundos com requisições concorrentes.
2. **Destaque do Menor Preço**: Identifica automaticamente a melhor oferta, link direto de compra e a loja mais barata.
3. **Cálculo de Economia**: Exibe a economia em relação à média do mercado.
4. **Filtro de Palavras-chave**: Busca consistente baseada na consulta informada.
5. **Interface Visual (App Web)**:
   - Cards com foto do produto, selo da loja, preço à vista e descontos.
   - Filtros dinâmicos por loja e faixa de preço.
   - Sistema de favoritos (watchlist de produtos).
6. **Alertas de Preço**: Cadastro de preço-alvo para monitoramento contínuo.
7. **Bot do Telegram Integrado**: Pesquisa de preços e consulta de ofertas diretamente pelo Telegram.
8. **Pronto para Nuvem / Docker**: Execução contínua em container Linux.

---

## Instalação e Configuração

### 1. Clonar o repositório e instalar dependências
```bash
git clone https://github.com/Jessicachaves/price-hunter-bot.git
cd price-hunter-bot
pip install -r requirements.txt
playwright install chromium
```

### 2. (Opcional) Configurar Bot do Telegram
Se desejar usar o bot no Telegram:
1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```
2. Adicione o seu token do [@BotFather](https://t.me/BotFather) dentro do arquivo `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz
   ```

---

## Como Executar Localmente

### Opção A: Interface Web + Bot do Telegram Juntos
```bash
python app.py
```
Acesse no navegador: **`http://127.0.0.1:8080`**  
*(Se o token do Telegram estiver configurado no `.env`, o bot iniciará automaticamente em segundo plano).*

### Opção B: Bot do Telegram Standalone
```bash
python telegram_bot.py
```

### Opção C: Terminal (CLI)
```bash
python cli.py "controle ps5"
python cli.py "iphone 15"
```

---

## Como Rodar 24/7 em um Servidor (Docker)

O projeto inclui `Dockerfile` e `docker-compose.yml` otimizados para produção.

Para rodar em qualquer VPS (DigitalOcean, AWS, Hetzner, etc.):

```bash
# 1. Configurar variáveis de ambiente
cp .env.example .env

# 2. Subir em segundo plano
docker compose up -d --build
```

O container executa o Chromium e mantém o servidor web e o bot do Telegram ativos continuamente.

---

## Estrutura do Projeto

```text
├── scrapers/              # Módulos de busca por loja
│   ├── mercadolivre.py    # Mercado Livre
│   ├── amazon.py          # Amazon Brasil
│   ├── kabum.py           # KaBuM!
│   ├── buscape.py         # Zoom / Buscapé
│   └── bing_shopping.py   # MultiLojas / Agregador
├── templates/
│   └── index.html         # Interface visual (Tailwind CSS)
├── app.py                 # Backend FastAPI e rotas da API
├── engine.py              # Motor de busca paralela e cálculo de ofertas
├── relevance.py           # Filtro e pontuação de relevância
├── database.py            # SQLite para favoritos e alertas
├── cli.py                 # Busca rápida via linha de comando
├── telegram_bot.py        # Integração do bot no Telegram
├── Dockerfile             # Configuração de container Linux + Playwright
├── docker-compose.yml     # Orquestração do container
├── requirements.txt       # Dependências do projeto
└── .gitignore             # Arquivos ignorados pelo Git
```

---

## Licença
Distribuído sob a licença MIT. Livre para uso e modificação.
