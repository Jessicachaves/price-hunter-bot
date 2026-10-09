import os
import sys
import telebot
from dotenv import load_dotenv
from dataclasses import asdict
from engine import engine
import database

load_dotenv()

# Obtenha o token do @BotFather no Telegram e adicione em um arquivo .env ou variável de ambiente
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

DUMMY_TOKENS = {"COLOQUE_SEU_TOKEN_AQUI", "123456789:ABCdefGhIJKlmNoPQRstuVWXyz", ""}

bot = None
if TELEGRAM_BOT_TOKEN and ":" in TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN not in DUMMY_TOKENS:
    try:
        bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    except Exception as e:
        print(f"⚠️ Erro ao instanciar bot do Telegram: {e}")

def setup_handlers(bot_instance):
    @bot_instance.message_handler(commands=['start', 'help', 'ajuda'])
    def send_welcome(message):
        welcome_text = (
            "👋 *Olá! Eu sou o seu Radar de Preços.*\n\n"
            "Me diga o que você quer comprar e eu vou procurar onde está mais barato em tempo real!\n\n"
            "📌 *Como usar:*\n"
            "• Digite o nome do produto: `controle ps5`\n"
            "• Ou use: `/buscar iphone 15`\n"
            "• Alerta de preço: `/alerta controle ps5 350`\n"
            "• Ver alertas: `/meusalertas`\n"
        )
        bot_instance.reply_to(message, welcome_text, parse_mode='Markdown')

    @bot_instance.message_handler(commands=['alerta'])
    def handle_alert(message):
        parts = message.text.split()
        if len(parts) < 3:
            bot_instance.reply_to(message, "⚠️ Uso correto: `/alerta <nome do produto> <preco_alvo>`\nExemplo: `/alerta controle ps5 350`", parse_mode='Markdown')
            return
        try:
            price_target = float(parts[-1].replace(',', '.'))
            product_query = " ".join(parts[1:-1])
            database.add_price_alert(product_query, price_target, notify_channel="telegram", user_identifier=str(message.chat.id))
            bot_instance.reply_to(message, f"✅ *Alerta Criado!*\nVou monitorar *{product_query}* e te aviso assim que estiver abaixo de *R$ {price_target:,.2f}*.", parse_mode='Markdown')
        except Exception as e:
            bot_instance.reply_to(message, f"Erro ao criar alerta: {e}")

    @bot_instance.message_handler(commands=['meusalertas'])
    def handle_my_alerts(message):
        alerts = database.get_alerts()
        user_alerts = [a for a in alerts if str(a.get('user_identifier')) == str(message.chat.id)]
        if not user_alerts:
            bot_instance.reply_to(message, "Você ainda não possui alertas cadastrados.")
            return
        text = "🔔 *Seus Alertas Ativos:*\n\n"
        for a in user_alerts:
            text += f"• *{a['query']}* ➔ até R$ {a['target_price']:,.2f}\n"
        bot_instance.reply_to(message, text, parse_mode='Markdown')

    @bot_instance.message_handler(commands=['buscar'])
    def handle_search_cmd(message):
        query = message.text.replace('/buscar', '').strip()
        if not query:
            bot_instance.reply_to(message, "Por favor, digite o nome do produto após /buscar.")
            return
        process_search(message, query)

    @bot_instance.message_handler(func=lambda msg: True)
    def handle_all_messages(message):
        query = message.text.strip()
        if query.startswith('/'):
            return
        process_search(message, query)

    def process_search(message, query: str):
        msg_wait = bot_instance.reply_to(message, f"🔍 *Pesquisando '{query}' nas lojas e filtrando acessórios...*", parse_mode='Markdown')
        
        try:
            res = engine.search_all_sync(query)
            if not res or res.get('total_found', 0) == 0:
                bot_instance.edit_message_text(f"❌ Não encontrei ofertas para *'{query}'*.", chat_id=message.chat.id, message_id=msg_wait.message_id, parse_mode='Markdown')
                return
                
            cheapest = res['cheapest']
            
            reply = (
                f"🛒 *Resultado da Busca:* `{query}`\n"
                f"⏱️ Encontradas {res['total_found']} ofertas em {res['search_time_sec']}s\n\n"
                f"🏆 *ONDE ESTÁ MAIS BARATO:*\n"
                f"📦 *{cheapest.title}*\n"
                f"💰 *Preço:* `{cheapest.price_formatted}`\n"
                f"🏬 *Loja:* {cheapest.store}\n"
                f"🔗 [Clique aqui para Comprar]({cheapest.link})\n\n"
            )
            
            if res.get('savings_vs_avg', 0) > 0:
                reply += f"💡 *Economia de {res['savings_vs_avg_formatted']}* em relação à média de mercado ({res['average_price_formatted']})\n\n"
                
            reply += "📋 *Outras opções mais baratas:*\n"
            for i, offer in enumerate(res['offers'][1:6], start=2):
                reply += f"{i}. [{offer.store}] {offer.title[:40]}... ➔ *{offer.price_formatted}* [Link]({offer.link})\n"
                
            bot_instance.edit_message_text(reply, chat_id=message.chat.id, message_id=msg_wait.message_id, parse_mode='Markdown', disable_web_page_preview=True)
        except Exception as e:
            bot_instance.edit_message_text(f"Erro na busca: {e}", chat_id=message.chat.id, message_id=msg_wait.message_id)

if bot:
    setup_handlers(bot)

if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    if not bot:
        print("⚠️ Token do Telegram não configurado!")
        print("1. Abra o Telegram e fale com @BotFather para criar seu bot e pegar o TOKEN")
        print("2. Cole seu TOKEN na linha 9 do arquivo telegram_bot.py ou rode no terminal:")
        print("   $env:TELEGRAM_BOT_TOKEN=\"seu_token_aqui\"")
        print("3. Depois rode novamente: python telegram_bot.py")
    else:
        print("🤖 Bot do Telegram iniciado com sucesso! Aguardando mensagens...")
        bot.infinity_polling()
