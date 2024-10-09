# routes.py

from flask import Blueprint, request, jsonify
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
import logging
from io import BytesIO
from .utils import carregar_dados, consultar_chatgpt
from dotenv import load_dotenv
import os



main = Blueprint('main', __name__)
df = None  # Variável global para armazenar o DataFrame carregado

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração do token do Telegram Bot
TELEGRAM_TOKEN = '7422503595:AAEuFBudgo31nMt-xcvctj83x5vAWQDqs-0'
bot = Bot(token=TELEGRAM_TOKEN)

# Configuração do log
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Inicializa o dispatcher para o bot
dispatcher = Dispatcher(bot, None, use_context=True)

@main.route('/inicial', methods=['GET'])
def tela_inicial():
    return jsonify({"mensagem": "Bem-vindo à tela inicial!"}), 200

@main.route('/upload', methods=['POST'])
def upload_file():
    global df
    if 'file' not in request.files:
        return jsonify({"erro": "Nenhum arquivo anexado!"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"erro": "Nenhum arquivo selecionado!"}), 400

    df = carregar_dados(file)
    return jsonify({"mensagem": "Arquivo carregado com sucesso!"}), 200

@main.route('/pergunta', methods=['POST'])
def pergunta():
    global df
    if df is None:
        return jsonify({"erro": "Nenhum arquivo carregado!"}), 400

    dados = request.get_json()
    pergunta_usuario = dados.get('pergunta', '')
    
    if not pergunta_usuario:
        return jsonify({"erro": "Pergunta não fornecida!"}), 400
    
    resposta = consultar_chatgpt(pergunta_usuario, df)
    return jsonify({"resposta": resposta})

# Função para lidar com mensagens de texto recebidas do Telegram
def handle_message(update, context):
    global df
    chat_id = update.message.chat_id
    texto = update.message.text

    # Verifique se o DataFrame df foi carregado
    if df is None:
        resposta = "Nenhum arquivo carregado! Por favor, faça o upload de um arquivo primeiro."
    else:
        resposta = consultar_chatgpt(texto, df)

    # Envie a resposta de volta para o usuário do Telegram
    bot.send_message(chat_id=chat_id, text=resposta)

# Função para lidar com uploads de arquivo (documento) no Telegram
def handle_document(update, context):
    global df
    chat_id = update.message.chat_id
    document = update.message.document

    # Baixe o arquivo enviado
    file = bot.get_file(document.file_id)
    file_bytes = BytesIO(file.download_as_bytearray())

    # Carregue o DataFrame usando a função 'carregar_dados'
    df = carregar_dados(file_bytes)

    bot.send_message(chat_id=chat_id, text="Arquivo carregado com sucesso!")

# Configurar handlers para mensagens de texto e documentos
message_handler = MessageHandler(Filters.text & ~Filters.command, handle_message)
document_handler = MessageHandler(Filters.document.mime_type("application/vnd.ms-excel") | Filters.document.mime_type("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"), handle_document)
dispatcher.add_handler(message_handler)
dispatcher.add_handler(document_handler)

@main.route('/telegram_webhook', methods=['POST'])
def telegram_webhook():
    """Endpoint para o webhook do Telegram"""
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok", 200
