#utils.py
import pandas as pd
import os
import google.generativeai as genai
from app.functions_ import *

# Função para carregar e preparar os dados do Excel
def carregar_dados(file):
    df = pd.read_excel(file)

    # Converter colunas que são datas para o formato datetime
    colunas_data = ['Data de distribuição', 'Data de cadastro', 'Data de citação']
    
    for coluna in colunas_data:
        if coluna in df.columns:
            df[coluna] = pd.to_datetime(df[coluna], format='%d/%m/%Y', errors='coerce')
    
    return df

# Variável global para manter o contexto anterior
contexto_anterior = {"pergunta": None, "tipo": None}

def processar_pergunta(pergunta, dataframe):
    global contexto_anterior  # Usar a variável global de contexto
    
    hoje = pd.Timestamp.now()
    pergunta_lower = pergunta.lower().strip()
    
    # Função auxiliar para verificar o contexto
    def verificar_contexto(pergunta_atual):
        # Exemplo de contexto: perguntar sobre arquivados após valor de causa
        if "arquivados" in pergunta_atual and contexto_anterior['tipo'] == "valor_causa":
            return processar_status(pergunta_atual, dataframe, "arquivado")
        # Adicionar mais verificações de contexto conforme necessário
        return None

    # Verificar se a pergunta atual está relacionada ao contexto anterior
    resposta_contextual = verificar_contexto(pergunta_lower)
    if resposta_contextual:
        # Limpar o contexto após a resposta ser processada, se necessário
        contexto_anterior = {"pergunta": None, "tipo": None}
        return resposta_contextual

    # Perguntas genéricas ou conversacionais
    if any(greeting in pergunta_lower for greeting in ["olá", "como você está", "oi", "bom dia", "boa tarde", "boa noite"]):
        contexto_anterior = {"pergunta": pergunta, "tipo": "conversacional"}  # Atualizar o contexto
        chatgemini_resposta = consultar_gemini_conversacional(pergunta)
        return chatgemini_resposta, {}

    # Perguntas sobre status (ativos, arquivados, etc.)
    if any(status in pergunta_lower for status in ["quantos processos ativos", "processos ativos", "quantos ativos"]):
        contexto_anterior = {"pergunta": pergunta, "tipo": "status"}  # Atualizar o contexto
        return processar_status(pergunta, dataframe, "ativo")
    
    elif any(status in pergunta_lower for status in ["quantos processos arquivados", "processos arquivados", "quantos arquivados"]):
        contexto_anterior = {"pergunta": pergunta, "tipo": "status"}  # Atualizar o contexto
        return processar_status(pergunta, dataframe, "arquivado")
    # Perguntas sobre status do caso ou processo de um autor específico
    elif "status do caso" in pergunta_lower or "status do processo" in pergunta_lower:
        return processar_status_autor(pergunta, dataframe)
    
    # Perguntas sobre órgãos
    elif "órgão" in pergunta_lower or "orgao" in pergunta_lower:
        return processar_orgao(dataframe)

    # Perguntas sobre cadastros
    elif "cadastrados" in pergunta_lower or "cadastrado" in pergunta_lower:
        return processar_datas(dataframe, "Data de cadastro", pergunta)
    
    # Perguntas sobre distribuidos
    elif "distribuídos" in pergunta_lower or "distribuido" in pergunta_lower:
        return processar_datas(dataframe, "Data de distribuição", pergunta)
    
    # Perguntas sobre valor total de acordos
    elif "valor total de acordos" in pergunta_lower or "acordo" in pergunta_lower:
        contexto_anterior = {"pergunta": pergunta, "tipo": "valor_acordo"}  # Atualizar o contexto
        return processar_valor_acordo(dataframe)

    # Perguntas sobre processos ainda não citados
    elif any(term in pergunta_lower for term in ["não foram citados", "não citado"]):
        contexto_anterior = {"pergunta": pergunta, "tipo": "nao_citados"}  # Atualizar o contexto
        return processar_nao_citados(dataframe)

    # Perguntas sobre valores de condenação por estado
    elif any(term in pergunta_lower for term in ["valor de condenação por estado", "total de condenação por estado"]):
        contexto_anterior = {"pergunta": pergunta, "tipo": "valor_condenacao_estado"}  # Atualizar o contexto
        return processar_valor_condenacao_por_estado(dataframe)
    
    # Pergunta sobre qual estado tem o maior valor de causa
    elif "estado com maior valor de causa" in pergunta_lower or "maior valor de causa" in pergunta_lower:
        contexto_anterior = {"pergunta": pergunta, "tipo": "valor_causa"}  # Atualizar o contexto
        return processar_maior_valor_causa_por_estado(dataframe)
    
    # Perguntas sobre maior média de valor de causa
    elif "maior média de valor de causa" in pergunta_lower:
        contexto_anterior = {"pergunta": pergunta, "tipo": "media_valor_causa"}  # Atualizar o contexto
        return processar_media_valor_causa_por_estado(dataframe)
    
    # Perguntas sobre valor total da causa
    elif "valor total da causa" in pergunta_lower:
        return processar_valor_total_causa(dataframe)

    # Perguntas sobre trânsito em julgado
    elif any(term in pergunta_lower for term in ["transitado em julgado", "transitaram em julgado"]):
        return processar_transito_julgado(dataframe)
    
    # Perguntas sobre sentença e resultados dos processos
    elif any(term in pergunta_lower for term in ["resultados dos processos", "divididos"]):
        return processar_sentenca(dataframe, pergunta)
    
    # Perguntas sobre quantidade de processos por estado
    elif any(term in pergunta_lower for term in ["quantidade de processos por estado", "quantidade de processos em cada estado"]):
        return processar_quantidade_processos_por_estado(dataframe)

    # Perguntas gerais sobre quantidade de processos
    elif "quantidade de processos" in pergunta_lower and "estado" not in pergunta_lower:
        return processar_quantidade_processos(dataframe)
    
    # Perguntas sobre recursos interpostos
    elif any(term in pergunta_lower for term in ["quantos recursos", "recursos interpostos"]):
        return processar_quantidade_recursos(dataframe)
    
    # Perguntas sobre os assuntos mais recorrentes
    elif any(term in pergunta_lower for term in ["assuntos mais recorrentes", "assuntos recorrentes"]):
        return processar_assuntos_recorrentes(dataframe)
    
    # Perguntas sobre tribunal com mais ações sobre convenções coletivas
    elif "tribunal" in pergunta_lower and "convenções coletivas" in pergunta_lower:
        return processar_tribunal_acoes_convenções(dataframe)
        
    # Perguntas sobre rito sumaríssimo
    elif any(term in pergunta_lower for term in ["rito sumaríssimo", "sumaríssimo"]):
        return processar_rito(dataframe)
    
    # Perguntas sobre fases dos processos
    elif "fase" in pergunta_lower or "fases" in pergunta_lower:
        return processar_fase(dataframe)
    
    # Perguntas sobre reclamantes com múltiplos processos
    elif "mais de um processo" in pergunta_lower:
        return processar_reclamantes_multiplos(dataframe)
    
    # Perguntas sobre o estado com maior valor de condenação
    elif any(term in pergunta_lower for term in ["estado mais ofensor", "estado devo ter mais preocupação"]):
        return processar_estado_mais_ofensor(dataframe)
    
    # Perguntas sobre comarca com maior valor de condenação
    elif "comarca" in pergunta_lower and any(term in pergunta_lower for term in ["preocupação", "mais ofensora"]):
        return processar_comarca_mais_preocupante(dataframe)
    
    # Perguntas sobre média de duração dos processos arquivados
    elif "média de duração" in pergunta_lower and "arquivado" in pergunta_lower:
        return processar_media_duracao_processos_arquivados(dataframe)

    # Perguntas sobre a média de duração por estado
    elif "média de duração" in pergunta_lower and "estado" in pergunta_lower:
        return processar_media_duracao_por_estado(dataframe)

    # Perguntas sobre a média de duração por comarca
    elif "média de duração" in pergunta_lower and "comarca" in pergunta_lower:
        return processar_media_duracao_por_comarca(dataframe)

    # Perguntas sobre quantidade de processos improcedentes
    elif any(term in pergunta_lower for term in ["quantos processos improcedentes", "quantidade de processos improcedentes"]):
        return processar_sentencas_improcedentes(dataframe)

    # Perguntas sobre processos extintos sem custos
    elif "quantos processos extinto sem custos" in pergunta_lower:
        return processar_sentencas_extinto_sem_custos(dataframe)

    # Perguntas sobre o processo com maior tempo sem movimentação
    elif "maior tempo sem movimentação" in pergunta_lower and "processo" in pergunta_lower:
        return processar_maior_tempo_sem_movimentacao(dataframe)
    
    # Perguntas sobre divisão de ritos
    elif "divisão por rito" in pergunta_lower:
        return processar_divisao_por_rito(dataframe)

    # Perguntas sobre processos ainda não julgados
    elif any(term in pergunta_lower for term in ["não foram julgados", "não julgado"]):
        return processar_nao_julgados(dataframe)

    # Se a pergunta não puder ser processada diretamente, enviar para o Gemini
    contexto_anterior = {"pergunta": pergunta, "tipo": "desconhecido"}  # Atualizar o contexto com pergunta desconhecida
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
        return "Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde."
    
# Função específica para perguntas conversacionais
def consultar_gemini_conversacional(pergunta):
    # Configurar a API do Gemini para conversas genéricas
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])  # Certifique-se de ter a chave de API do Gemini no seu .env
    model = genai.GenerativeModel("gemini-1.5-pro-001")

    prompt = f"Converse com o usuário e responda de maneira amigável e educada: {pergunta}"

    try:
        # Enviar a pergunta para o Gemini e obter uma resposta
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erro ao consultar a API do Gemini: {e}")
        return "Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde."
