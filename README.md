# 🏷️ Radar de Preços - Comparador Inteligente Multilojas

Um aplicativo completo em Python, FastAPI e Web moderna para **pesquisar, comparar preços e encontrar onde qualquer produto está mais barato** em tempo real em dezenas de lojas brasileiras (Amazon Brasil, KaBuM!, Mercado Livre, Magazine Luiza, Zoom/Buscapé e mais).

Possui **interface web interativa**, **bot do Telegram integrado** e **filtro inteligente de relevância** para não confundir o produto buscado com acessórios.

---

## ✨ Principais Recursos

1. ⚡ **Busca Paralela Multilojas**: Consulta os principais e-commerces e agregadores do Brasil em segundos com requisições assíncronas concorrentes.
2. 🏆 **Destaque do Menor Preço**: Identifica automaticamente a melhor oferta, link direto de compra e a loja mais barata.
3. 💡 **Cálculo de Economia**: Exibe quanto você economiza em relação à média do mercado.
4. 🎯 **Filtro Inteligente de Palavras-chave**: Busca puramente baseada no que você digitar, sem bloquear produtos legítimos.
5. 🎨 **Interface Visual Moderna (App Web)**:
   - Cards com foto do produto, selo da loja, preço à vista e descontos.
   - Filtros dinâmicos por loja e faixa de preço.
   - Sistema de favoritos (watchlist de produtos).
6. 🔔 **Alertas de Preço**: Cadastre seu preço-alvo para monitoramento.
7. 🤖 **Bot do Telegram Integrado**: Pesquise preços e receba as melhores ofertas diretamente no celular.
8. 🐳 **Pronto para Nuvem / Docker**: Execução 24/7 em qualquer servidor ou VPS com um único comando.

---

## 🛠️ Instalação e Configuração

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

## 🚀 Como Executar Localmente

### Opção A: Interface Web + Bot do Telegram Juntos
```bash
python app.py
```
Acesse no navegador: **`http://127.0.0.1:8000`**  
*(Se o token do Telegram estiver configurado no `.env`, o bot iniciará automaticamente em segundo plano).*

*(No Windows, você também pode dar um duplo clique em `Iniciar_Radar_Precos.bat`)*

### Opção B: Bot do Telegram Standalone
```bash
python telegram_bot.py
```

### Opção C: Terminal (CLI Rápido)
```bash
python cli.py "controle ps5"
python cli.py "cabo para controle"
python cli.py "iphone 15"
```

---

## ☁️ Como Rodar 24/7 em um Servidor (Docker)

O projeto já inclui `Dockerfile` e `docker-compose.yml` otimizados para produção.

Para rodar em qualquer VPS (DigitalOcean, AWS, Oracle Cloud Free Tier, Hetzner) ou serviço de container:

```bash
# 1. Configurar variáveis de ambiente
cp .env.example .env

# 2. Subir em segundo plano
docker compose up -d --build
```

O container subirá automaticamente com o navegador Chromium e manterá tanto o servidor web quanto o bot do Telegram funcionando 24 horas por dia, reiniciando sozinho se o servidor reiniciar.

---

## 📁 Estrutura do Projeto

```text
├── scrapers/              # Módulos de busca por loja
│   ├── mercadolivre.py    # Mercado Livre (Playwright Stealth)
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

## 📄 Licença
Distribuído sob a licença MIT. Sinta-se livre para usar e modificar!
