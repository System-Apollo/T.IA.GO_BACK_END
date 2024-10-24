#utils.py
import pandas as pd
import os
import google.generativeai as genai
from ratelimit import limits, sleep_and_retry
from app.functions_ import *
import unicodedata
from app.map import categoria_perguntas

# Função para carregar e preparar os dados do Excel
def carregar_dados(file):
    df = pd.read_excel(file)

    # Converter colunas que são datas para o formato datetime
    colunas_data = ['Data de distribuição', 'Data de cadastro', 'Data de citação']
    
    for coluna in colunas_data:
        if coluna in df.columns:
            df[coluna] = pd.to_datetime(df[coluna], format='%d/%m/%Y', errors='coerce')
    
    return df

# Função para normalizar a pergunta, removendo acentos e pontuações
def normalizar_pergunta(pergunta):
    # Remover acentos
    pergunta = ''.join(
        c for c in unicodedata.normalize('NFD', pergunta) if unicodedata.category(c) != 'Mn'
    )
    # Remover pontuações
    pergunta = re.sub(r'[^\w\s]', '', pergunta)
    return pergunta.lower().strip()

# Função para remover acentos de uma string
def remover_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c))



def processar_pergunta(pergunta, dataframe):
    # Normalizar a pergunta para lidar com acentos, pontuação e maiúsculas
    pergunta_normalizada = normalizar_pergunta(pergunta)
    
    # Verificar se a pergunta é conversacional
    greetings = ["olá", "como você está", "oi", "bom dia", "boa tarde", "boa noite", "tudo bem"]
    if any(greeting in pergunta_normalizada.lower() for greeting in greetings):
        return "Como posso te ajudar hoje?", {}

    # Iterar sobre as categorias de perguntas
    for categoria, padroes in categoria_perguntas.items():
        for padrao in padroes:
            if re.search(padrao, pergunta_normalizada, re.IGNORECASE):
                # Chamar a função apropriada com base na categoria identificada
                if categoria == 'valor_total_acordos':
                    return processar_valor_acordo(dataframe)
                elif categoria == 'valor_condenacao_estado':
                    return processar_valor_condenacao_por_estado(dataframe)
                elif categoria == 'estado_maior_valor_causa':
                    return processar_maior_valor_causa_por_estado(dataframe)
                elif categoria == 'estado_maior_media_valor_causa':
                    return processar_media_valor_causa_por_estado(dataframe)
                elif categoria == 'divisao_resultados_processos':
                    return processar_sentenca(dataframe, pergunta)
                elif categoria == 'transitaram_julgado':
                    return processar_transito_julgado(dataframe)
                elif categoria == 'quantidade_processos_estado':
                    return processar_quantidade_processos_por_estado(dataframe)
                elif categoria == 'quantidade_total_processos':
                    return processar_quantidade_processos(dataframe)
                elif categoria == 'valor_total_causa':
                    return processar_valor_total_causa(dataframe)
                elif categoria == 'processos_ativos':
                    return processar_status(pergunta, dataframe, "ativo")
                elif categoria == 'processos_arquivados':
                    return processar_status(pergunta, dataframe, "arquivado")
                elif categoria == 'quantidade_recursos':
                    return processar_quantidade_recursos(dataframe)
                elif categoria == 'sentencas':
                    return processar_sentenca(dataframe, pergunta)
                elif categoria == 'assuntos_recorrentes':
                    return processar_assuntos_recorrentes(dataframe)
                elif categoria == 'tribunal_acoes_convencoes':
                    return processar_tribunal_acoes_convenções(dataframe)
                elif categoria == 'rito_sumarisimo':
                    return processar_rito(dataframe)
                elif categoria == 'divisao_fase':
                    return processar_fase(dataframe)
                elif categoria == 'reclamantes_multiplos':
                    return processar_reclamantes_multiplos(dataframe)
                elif categoria == 'estado_mais_ofensor':
                    return processar_estado_mais_ofensor(dataframe)
                elif categoria == 'comarca_mais_ofensora':
                    return processar_comarca_mais_preocupante(dataframe)
                elif categoria == 'melhor_estrategia':
                    return consultar_gemini_conversacional(pergunta, dataframe), "Essa pergunta envolve uma análise mais detalhada e política de acordo. Por favor, entre em contato com o setor responsável."
                elif categoria == 'beneficio_economico_carteira':
                    return consultar_gemini_conversacional(pergunta, dataframe), "Para calcular o benefício econômico, subtraia o valor da condenação do valor da causa."
                elif categoria == 'beneficio_economico_estado':
                    return consultar_gemini_conversacional(pergunta, dataframe), "Para calcular o benefício econômico por estado, subtraia o valor da condenação pelo valor da causa em cada estado."
                elif categoria == 'idade_carteira':
                    return consultar_gemini_conversacional(pergunta, dataframe), "Para determinar a idade da carteira, consulte os dados de abertura e finalização dos processos."
                elif categoria == 'maior_media_duracao_estado':
                    return processar_media_duracao_por_estado(dataframe)
                elif categoria == 'maior_media_duracao_comarca':
                    return processar_media_duracao_por_comarca(dataframe)
                elif categoria == 'processos_improcedentes':
                    return processar_sentencas_improcedentes(dataframe)
                elif categoria == 'processos_extintos_sem_custos':
                    return processar_sentencas_extinto_sem_custos(dataframe)
                elif categoria == 'processo_maior_tempo_sem_movimentacao':
                    return processar_maior_tempo_sem_movimentacao(dataframe)
                elif categoria == 'divisao_por_rito':
                    return processar_divisao_por_rito(dataframe)
                elif categoria == 'processos_nao_julgados':
                    return processar_nao_julgados(dataframe)
                elif categoria == 'processos_nao_citados':
                    return processar_nao_citados(dataframe)
                elif categoria == 'processo_mais_antigo':
                    return consultar_gemini_conversacional(pergunta, dataframe), "Para encontrar o processo mais antigo, verifique a data de distribuição mais antiga no banco de dados."

    # Se a pergunta não puder ser processada diretamente, enviar para o Gemini
    chatgemini_resposta = consultar_gemini_conversacional(pergunta, dataframe)
    return chatgemini_resposta, {}



# Limites da API do ChatGemini
RPM = 10  # 2 requisições por minuto
RPD = 800  # 50 requisições por dia

# Função para contar o número de tokens
def contar_tokens(texto):
    # Uma maneira simplificada de contar tokens é dividir o texto em palavras
    # Você pode ajustar isso para ser mais preciso com base no comportamento do modelo
    return len(texto.split())

# Configurar a API do Gemini
def configurar_gemini():
    genai.configure(api_key=os.environ["GEMINI_API_KEY"]) # Certifique-se de ter a chave de API do Gemini no seu .env
    
    
# Limitar a taxa de requisições a 2 por minuto (RPM) e 50 por dia (rPD)
@sleep_and_retry
@limits(calls=RPM, period=60)  # Limite de 2 chamadas por minuto
@limits(calls=RPD, period=86400)  # Limite de 50 chamadas por dia
def consultar_gemini(pergunta, dataframe):
    configurar_gemini() 
    model = genai.GenerativeModel("gemini-1.5-pro-001")

    # Converter todos os dados do DataFrame em uma string para fornecer contexto ao Gemini
    contexto = dataframe.to_string(index=False)
    prompt = f"Os dados a seguir são extraídos de um arquivo Excel:\n{contexto}\n\nPergunta: {pergunta}\n\nResponda de forma concisa, fornecendo resultado de terceira pessoa, por exemplo: Atualmente, há X processos ativos."

    # Contar tokens no prompt
    tokens_enviados = contar_tokens(prompt)
    print(f"Tokens enviados: {tokens_enviados}")

    try:
        # Enviar a pergunta com o contexto para o Gemini
        response = model.generate_content(prompt)
        # Contar tokens na resposta
        tokens_recebidos = contar_tokens(response.text)
        print(f"Tokens recebidos: {tokens_recebidos}")
        return response.text.strip()  # Extrair o texto da resposta
    
    except Exception as e:
        print(f"Erro ao consultar a API do Gemini: {e}")
        return "Desculpe, não conseguir processar sua solicitação. Mais irei melhora meu banco de dados."
    
# Função específica para perguntas conversacionais
# Conversações simples com limite de requisições
@sleep_and_retry
@limits(calls=RPM, period=60)
@limits(calls=RPD, period=86400)
def consultar_gemini_conversacional(pergunta, dataframe):
    # Configurar a API do Gemini para conversas genéricas
    configurar_gemini()  # Certifique-se de ter a chave de API do Gemini no seu .env
    model = genai.GenerativeModel("gemini-1.5-pro-001")
    
    # Converter todos os dados do DataFrame em uma string para fornecer contexto ao Gemini
    contexto = dataframe.to_string(index=False)
    prompt = f"Os dados a seguir são extraídos de um arquivo Excel:\n{contexto}\n\nConverse com o usuário e responda de maneira amigável e educada, nao me traga emojis: {pergunta}"
    # Contar tokens no prompt
    tokens_enviados = contar_tokens(prompt)
    print(f"Tokens enviados: {tokens_enviados}")
    try:
        # Enviar a pergunta para o Gemini e obter uma resposta
        response = model.generate_content(prompt)
        tokens_recebidos = contar_tokens(response.text)
        print(f"Tokens recebidos: {tokens_recebidos}")
        return response.text.strip()
    except Exception as e:
        print(f"Erro ao consultar a API do Gemini: {e}")
        return "Desculpe, Por eu ser novo aqui ainda estou aprimorando meu banco, pergunte novamente daqui alguns segundos."
    
# Conversações simples com limite de requisições
@sleep_and_retry
@limits(calls=RPM, period=60)
@limits(calls=RPD, period=86400)
def consultar_gemini_conversacional_simples(pergunta):
    # Configurar a API do Gemini para conversas genéricas
    configurar_gemini()  # Certifique-se de ter a chave de API do Gemini no seu .env
    model = genai.GenerativeModel("gemini-1.5-pro-001")
    
    # Converter todos os dados do DataFrame em uma string para fornecer contexto ao Gemini
    
    prompt = f"Converse com o usuário e responda de maneira amigável e educada e não me traga emojis: {pergunta}"
    
    # Contar tokens no prompt
    tokens_enviados = contar_tokens(prompt)
    print(f"Tokens enviados: {tokens_enviados}")

    try:
        # Enviar a pergunta para o Gemini e obter uma resposta
        response = model.generate_content(prompt)
        tokens_recebidos = contar_tokens(response.text)
        print(f"Tokens recebidos: {tokens_recebidos}")
        return response.text.strip()
    except Exception as e:
        print(f"Erro ao consultar a API do Gemini: {e}")
        return "Desculpe, Por eu ser novo aqui ainda estou aprimorando meu banco, pergunte novamente daqui alguns segundos."
