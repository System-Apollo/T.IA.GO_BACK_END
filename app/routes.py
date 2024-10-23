# routes.py
from flask import Blueprint, request, jsonify
import logging
from .utils import carregar_dados, processar_pergunta
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Updater, Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
import os
from flask_caching import Cache
from app import cache
import queue
from threading import Thread
from time import sleep
import time

main = Blueprint('main', __name__)
df = None 

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

df = carregar_dados('Processos_20240917131041.xlsx')  # Carregar dados do Excel

# Criar o dispatcher manualmente
dispatcher = Dispatcher(bot, None, workers=1)

# Fila para controlar requisições
fila_de_requisicoes = queue.Queue()

# Controle de requisições: Limitar 4 por minuto e 100 por dia
limite_por_minuto = 4
limite_por_dia = 100
requisicoes_no_minuto = 0
requisicoes_no_dia = 0
ultimo_minuto = time.time()
ultimo_dia = time.time()

# Função para controlar a taxa de requisições
def controlar_taxa():
    global requisicoes_no_minuto, requisicoes_no_dia, ultimo_minuto, ultimo_dia
    
    agora = time.time()

    # Resetar contador por minuto se necessário
    if agora - ultimo_minuto >= 60:
        requisicoes_no_minuto = 0
        ultimo_minuto = agora

    # Resetar contador por dia se necessário
    if agora - ultimo_dia >= 86400:
        requisicoes_no_dia = 0
        ultimo_dia = agora

    # Verificar se está dentro do limite
    if requisicoes_no_minuto >= limite_por_minuto:
        sleep(60 - (agora - ultimo_minuto))  # Aguardar até o próximo minuto
        requisicoes_no_minuto = 0
        ultimo_minuto = time.time()

    if requisicoes_no_dia >= limite_por_dia:
        raise Exception("Limite diário de requisições atingido.")  # Opcional: Retornar erro ou gerenciar de outra forma

    requisicoes_no_minuto += 1
    requisicoes_no_dia += 1

# Função para processar fila de requisições
def processar_fila():
    while True:
        pergunta, dataframe = fila_de_requisicoes.get()
        controlar_taxa()  # Controlar a taxa antes de processar a requisição
        resposta_texto, grafico_data = processar_pergunta(pergunta, dataframe)
        fila_de_requisicoes.task_done()  # Marcar como finalizada
        cache.set(pergunta, {"resposta": resposta_texto, "grafico": grafico_data})  # Armazenar no cache

# Iniciar uma thread para processar as requisições na fila
thread = Thread(target=processar_fila)
thread.daemon = True
thread.start()

# Adicionar pergunta na fila
def adicionar_pergunta_na_fila(pergunta, dataframe):
    fila_de_requisicoes.put((pergunta, dataframe))

# Função para iniciar o bot do Telegram
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Bem-vindo! Como posso facilitar seu dia hoje?\nFaça uma pergunta, como: Quantos processos ativos citam minha empresa?')

def handle_message(update: Update, context: CallbackContext) -> None:
    global df
    if df is None:
        update.message.reply_text('Nenhum arquivo carregado!')
        return

    pergunta_usuario = update.message.text

    if not pergunta_usuario:
        update.message.reply_text('Pergunta não fornecida!')
        return

    # Verificar se a resposta está no cache
    resposta_cache = cache.get(pergunta_usuario)
    
    if resposta_cache:
        update.message.reply_text(resposta_cache["resposta"])
        return

    # Adicionar a pergunta na fila para processamento
    adicionar_pergunta_na_fila(pergunta_usuario, df)
    
    # Aguarda a fila processar a pergunta
    while not cache.get(pergunta_usuario):
        sleep(1)  # Aguarda o processamento da fila
    
    # Retorna a resposta do cache após o processamento
    resposta_cache = cache.get(pergunta_usuario)
    update.message.reply_text(resposta_cache["resposta"])

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

@main.route('/', methods=['GET'])
def tela_inicial():
    return jsonify({"mensagem": "Bem-vindo à tela inicial!"}), 200

# Rota para processar perguntas via HTTP
@main.route('/pergunta', methods=['POST'])
def pergunta():
    global df
    if df is None:
        return jsonify({"erro": "Nenhum arquivo carregado!"}), 400

    dados = request.get_json()
    pergunta_usuario = dados.get('pergunta', '')

    if not pergunta_usuario:
        return jsonify({"erro": "Pergunta não fornecida!"}), 400

    # Verificar se a resposta para essa pergunta já está no cache
    resposta_cache = cache.get(pergunta_usuario)
    
    if resposta_cache:
        # Retornar a resposta do cache
        return jsonify(resposta_cache)

    # Adicionar a pergunta na fila para processamento
    adicionar_pergunta_na_fila(pergunta_usuario, df)
    
    # Aguarda a fila processar a pergunta
    while not cache.get(pergunta_usuario):
        sleep(1)  # Aguarda o processamento da fila
    
    # Retorna a resposta do cache após o processamento
    resposta_cache = cache.get(pergunta_usuario)
    return jsonify(resposta_cache)

