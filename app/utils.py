#utils.py
import pandas as pd
import os
import google.generativeai as genai
from app.functions_ import *
import unicodedata

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
    
    hoje = pd.Timestamp.now()
    pergunta_lower = pergunta.lower().strip()
    

    # Perguntas genéricas ou conversacionais
    if any(greeting in pergunta_lower for greeting in ["olá", "como você está", "oi", "bom dia", "boa tarde", "boa noite"]):
        chatgemini_resposta = consultar_gemini_conversacional(pergunta)
        return chatgemini_resposta, {}

    # Perguntas sobre valor total de acordos
    if "valor total de acordos" in pergunta_normalizada:
        return processar_valor_acordo(dataframe)

    # Perguntas sobre valor de condenação por estado
    elif "valor de condenacao por estado" in pergunta_normalizada:
        return processar_valor_condenacao_por_estado(dataframe)

    # Perguntas sobre qual estado tem o maior valor de causa
    elif "estado com maior valor de causa" in pergunta_normalizada:
        return processar_maior_valor_causa_por_estado(dataframe)

    # Perguntas sobre qual estado tem a maior média de valor de causa
    elif "estado com maior media de valor de causa" in pergunta_normalizada:
        return processar_media_valor_causa_por_estado(dataframe)

    # Perguntas sobre divisão dos resultados dos processos
    elif "divididos os resultados dos processos" in pergunta_normalizada:
        return processar_sentenca(dataframe, pergunta)

    # Perguntas sobre processos que transitaram em julgado
    elif "transitaram em julgado" in pergunta_normalizada:
        return processar_transito_julgado(dataframe)
    
    # Perguntas sobre quantidade de processos por estado
    elif "quantidade de processos por estado" in pergunta_normalizada:
        return processar_quantidade_processos_por_estado(dataframe)

    # Perguntas sobre quantidade total de processos
    elif "quantidade de processos" in pergunta_normalizada:
        return processar_quantidade_processos(dataframe)


    # Perguntas sobre valor total da causa
    elif "valor total da causa" in pergunta_normalizada:
        return processar_valor_total_causa(dataframe)

    # Perguntas sobre quantidade de processos ativos
    elif "quantos processos ativos" in pergunta_normalizada:
        return processar_status(pergunta, dataframe, "ativo")

    # Perguntas sobre quantidade de processos arquivados
    elif "quantos processos arquivados" in pergunta_normalizada:
        return processar_status(pergunta, dataframe, "arquivado")

    # Perguntas sobre quantidade de recursos interpostos
    elif "quantos recursos foram interpostos" in pergunta_normalizada:
        return processar_quantidade_recursos(dataframe)

    # Perguntas sobre a divisão dos resultados das sentenças
    elif "divisao dos resultados das sentencas" in pergunta_normalizada:
        return processar_sentenca(dataframe, pergunta)

    # Perguntas sobre os assuntos mais recorrentes
    elif "assuntos mais recorrentes" in pergunta_normalizada:
        return processar_assuntos_recorrentes(dataframe)

    # Perguntas sobre tribunal com mais ações sobre convenções coletivas
    elif "tribunal tem mais acoes sobre convencoes coletivas" in pergunta_normalizada:
        return processar_tribunal_acoes_convenções(dataframe)

    # Perguntas sobre processos no rito sumaríssimo
    elif "rito sumarisimo" in pergunta_normalizada:
        return processar_rito(dataframe)

    # Perguntas sobre a divisão por fase
    elif "divisao por fase" in pergunta_normalizada:
        return processar_fase(dataframe)

    # Perguntas sobre reclamantes com mais de um processo
    elif "algum reclamante tem mais de um processo" in pergunta_normalizada:
        return processar_reclamantes_multiplos(dataframe)

    # Perguntas sobre qual estado devo ter mais preocupação ou qual estado mais ofensor
    elif "estado devo ter mais preocupacao" in pergunta_normalizada or "estado mais ofensor" in pergunta_normalizada:
        return processar_estado_mais_ofensor(dataframe)

    # Perguntas sobre qual comarca devo ter mais preocupação ou qual comarca mais ofensora
    elif "comarca devo ter mais preocupacao" in pergunta_normalizada or "comarca mais ofensora" in pergunta_normalizada:
        return processar_comarca_mais_preocupante(dataframe)

    # Perguntas sobre melhor estratégia para aplicar nesse estado
    elif "melhor estrategia para aplicar nesse estado" in pergunta_normalizada:
        return consultar_gemini_conversacional(pergunta, dataframe), "Essa pergunta envolve uma análise mais detalhada e política de acordo. Por favor, entre em contato com o setor responsável."

    # Perguntas sobre o benefício econômico da carteira
    elif "beneficio economico da carteira" in pergunta_normalizada:
        return consultar_gemini_conversacional(pergunta, dataframe), "Para calcular o benefício econômico, subtraia o valor da condenação do valor da causa."

    # Perguntas sobre o benefício econômico por estado
    elif "beneficio economico por estado" in pergunta_normalizada:
        return consultar_gemini_conversacional(pergunta, dataframe), "Para calcular o benefício econômico por estado, subtraia o valor da condenação pelo valor da causa em cada estado."

    # Perguntas sobre a idade da carteira
    elif "idade da carteira" in pergunta_normalizada:
        return consultar_gemini_conversacional(pergunta, dataframe),"Para determinar a idade da carteira, consulte os dados de abertura e finalização dos processos."

    # Perguntas sobre o estado com maior média de duração
    elif "estado com maior media de duracao" in pergunta_normalizada:
        return processar_media_duracao_por_estado(dataframe)

    # Perguntas sobre a comarca com maior média de duração
    elif "comarca com maior media de duracao" in pergunta_normalizada:
        return processar_media_duracao_por_comarca(dataframe)

    # Perguntas sobre processos improcedentes
    elif "quantos processos improcedentes" in pergunta_normalizada:
        return processar_sentencas_improcedentes(dataframe)

    # Perguntas sobre processos extintos sem custos
    elif "quantos processos extinto sem custos" in pergunta_normalizada:
        return processar_sentencas_extinto_sem_custos(dataframe)

    # Perguntas sobre processo com maior tempo sem movimentação
    elif "processo com maior tempo sem movimentacao" in pergunta_normalizada:
        return processar_maior_tempo_sem_movimentacao(dataframe)

    # Perguntas sobre divisão por rito
    elif "como esta a divisao por rito" in pergunta_normalizada:
        return processar_divisao_por_rito(dataframe)

    # Perguntas sobre processos ainda não julgados
    elif "quantos processos ainda nao foram julgados" in pergunta_normalizada:
        return processar_nao_julgados(dataframe)

    # Perguntas sobre processos ainda não citados
    elif "quantos processos ainda nao foram citados" in pergunta_normalizada:
        return processar_nao_citados(dataframe)

    # Perguntas sobre o processo mais antigo da base
    elif "processo mais antigo da base" in pergunta_normalizada:
        return consultar_gemini_conversacional(pergunta, dataframe), "Para encontrar o processo mais antigo, verifique a data de distribuição mais antiga no banco de dados."

    # Se a pergunta não puder ser processada diretamente, enviar para o Gemini
    chatgemini_resposta = consultar_gemini(pergunta, dataframe)
    return chatgemini_resposta, {}




# Função para contar o número de tokens
def contar_tokens(texto):
    # Uma maneira simplificada de contar tokens é dividir o texto em palavras
    # Você pode ajustar isso para ser mais preciso com base no comportamento do modelo
    return len(texto.split())

# Função para consultar o Gemini com o contexto dos dados do Excel
def consultar_gemini(pergunta, dataframe):
    # Configurar a API do Gemini
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])  # Certifique-se de ter a chave de API do Gemini no seu .env
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
def consultar_gemini_conversacional(pergunta, dataframe):
    # Configurar a API do Gemini para conversas genéricas
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])  # Certifique-se de ter a chave de API do Gemini no seu .env
    model = genai.GenerativeModel("gemini-1.5-pro-001")
    
    # Converter todos os dados do DataFrame em uma string para fornecer contexto ao Gemini
    contexto = dataframe.to_string(index=False)


    prompt = f"Os dados a seguir são extraídos de um arquivo Excel:\n{contexto}\n\nConverse com o usuário e responda de maneira amigável e educada: {pergunta}"

    try:
        # Enviar a pergunta para o Gemini e obter uma resposta
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erro ao consultar a API do Gemini: {e}")
        return "Desculpe, não conseguir processar sua solicitação. Mais irei melhora mais meu banco de dados."
