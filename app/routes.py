# routes.py
from flask import Blueprint, request, jsonify
import logging
from .utils import carregar_dados, processar_pergunta
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Updater, Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
import os


main = Blueprint('main', __name__)
df = None 

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = Bot(token=TELEGRAM_TOKEN)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)



df = carregar_dados('Processos_20240917131041.xlsx')  

# Criar o dispatcher manualmente
dispatcher = Dispatcher(bot, None, workers=1)

# Função para iniciar o bot do Telegram
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Bem-vindo! Como posso facilitar seu dia hoje?\nFaça uma pergunta, como: Quantos processos ativos citam minha empresa?')

# Função para processar perguntas via Telegram
def handle_message(update: Update, context: CallbackContext) -> None:
    global df
    if df is None:
        update.message.reply_text('Nenhum arquivo carregado!')
        return

    pergunta_usuario = update.message.text

    if not pergunta_usuario:
        update.message.reply_text('Pergunta não fornecida!')
        return

    # Processar a pergunta
    resposta_texto, _ = processar_pergunta(pergunta_usuario, df)  # Ignorar os dados de gráfico para o Telegram

    # Enviar apenas a resposta de texto
    update.message.reply_text(resposta_texto)

# Registrar os handlers no dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Rota para receber as atualizações do webhook do Telegram
@main.route('/telegram_webhook', methods=['POST'])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    
    # Processar a atualização com o dispatcher
    dispatcher.process_update(update)
    
    return 'ok'

# Função para configurar e iniciar o webhook do Telegram
def iniciar_bot_telegram(token, webhook_url):
    bot.set_webhook(url=webhook_url)
    logging.info(f"Webhook configurado para: {webhook_url}")

@main.route('/inicial', methods=['GET'])
def tela_inicial():
    return jsonify({"mensagem": "Bem-vindo à tela inicial!"}), 200

@main.route('/pergunta', methods=['POST'])
def pergunta():
    global df
    if df is None:
        return jsonify({"erro": "Nenhum arquivo carregado!"}), 400

    dados = request.get_json()
    pergunta_usuario = dados.get('pergunta', '')

    if not pergunta_usuario:
        return jsonify({"erro": "Pergunta não fornecida!"}), 400

     # Chamar a função processar_pergunta para obter a resposta e os dados do gráfico
    resposta_texto, grafico_data = processar_pergunta(pergunta_usuario, df)

    # Retornar a resposta e os dados do gráfico
    response_data = {
        "resposta": resposta_texto,
        "grafico": grafico_data
    }
    return jsonify(response_data)
