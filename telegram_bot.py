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
        print(f"[ERROR] Erro ao instanciar bot do Telegram: {e}")

def setup_handlers(bot_instance):
    @bot_instance.message_handler(commands=['start', 'help', 'ajuda'])
    def send_welcome(message):
        welcome_text = (
            "*Radar de Preços*\n\n"
            "Digite o produto que procura para comparar precos em tempo real nas principais lojas do Brasil.\n\n"
            "*Comandos:*\n"
            "• Digite o nome do produto: `controle ps5`\n"
            "• Buscar: `/buscar iphone 15`\n"
            "• Criar alerta: `/alerta controle ps5 350`\n"
            "• Ver alertas: `/meusalertas`\n"
        )
        bot_instance.reply_to(message, welcome_text, parse_mode='Markdown')

    @bot_instance.message_handler(commands=['alerta'])
    def handle_alert(message):
        parts = message.text.split()
        if len(parts) < 3:
            bot_instance.reply_to(message, "Uso correto: `/alerta <nome do produto> <preco_alvo>`\nExemplo: `/alerta controle ps5 350`", parse_mode='Markdown')
            return
        try:
            price_target = float(parts[-1].replace(',', '.'))
            product_query = " ".join(parts[1:-1])
            database.add_price_alert(product_query, price_target, notify_channel="telegram", user_identifier=str(message.chat.id))
            bot_instance.reply_to(message, f"*Alerta cadastrado.*\nMonitorando *{product_query}* para avisar quando atingir *R$ {price_target:,.2f}*.", parse_mode='Markdown')
        except Exception as e:
            bot_instance.reply_to(message, f"Erro ao criar alerta: {e}")

    @bot_instance.message_handler(commands=['meusalertas'])
    def handle_my_alerts(message):
        alerts = database.get_alerts()
        user_alerts = [a for a in alerts if str(a.get('user_identifier')) == str(message.chat.id)]
        if not user_alerts:
            bot_instance.reply_to(message, "Nenhum alerta cadastrado no momento.")
            return
        text = "*Alertas ativos:*\n\n"
        for a in user_alerts:
            text += f"• *{a['query']}* -> ate R$ {a['target_price']:,.2f}\n"
        bot_instance.reply_to(message, text, parse_mode='Markdown')

    @bot_instance.message_handler(commands=['buscar'])
    def handle_search_cmd(message):
        query = message.text.replace('/buscar', '').strip()
        if not query:
            bot_instance.reply_to(message, "Digite o nome do produto apos /buscar.")
            return
        process_search(message, query)

    @bot_instance.message_handler(func=lambda msg: True)
    def handle_all_messages(message):
        query = message.text.strip()
        if query.startswith('/'):
            return
        process_search(message, query)

    def process_search(message, query: str):
        msg_wait = bot_instance.reply_to(message, f"*Pesquisando '{query}' nas lojas...*", parse_mode='Markdown')
        
        try:
            res = engine.search_all_sync(query)
            if not res or res.get('total_found', 0) == 0:
                bot_instance.edit_message_text(f"Nenhuma oferta encontrada para *'{query}'*.", chat_id=message.chat.id, message_id=msg_wait.message_id, parse_mode='Markdown')
                return
                
            cheapest = res['cheapest']
            
            reply = (
                f"*Resultado da Busca:* `{query}`\n"
                f"Total de {res['total_found']} ofertas em {res['search_time_sec']}s\n\n"
                f"*MELHOR PRECO:*\n"
                f"*{cheapest.title}*\n"
                f"Preco: `{cheapest.price_formatted}`\n"
                f"Loja: {cheapest.store}\n"
                f"[Acessar Loja]({cheapest.link})\n\n"
            )
            
            if res.get('savings_vs_avg', 0) > 0:
                reply += f"Economia de {res['savings_vs_avg_formatted']} em relacao a media ({res['average_price_formatted']})\n\n"
                
            reply += "*Outras opcoes:*\n"
            for i, offer in enumerate(res['offers'][1:6], start=2):
                reply += f"{i}. [{offer.store}] {offer.title[:45]}... -> *{offer.price_formatted}* [Link]({offer.link})\n"
                
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
        print("[AVISO] Token do Telegram nao configurado no arquivo .env")
    else:
        print("[INFO] Bot do Telegram ativo. Aguardando mensagens...")
        bot.infinity_polling()
