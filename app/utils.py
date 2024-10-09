#utils.py
import pandas as pd
import os
import google.generativeai as genai

# Função para carregar e preparar os dados do Excel
def carregar_dados(file):
    df = pd.read_excel(file)

    # Converter colunas que são datas para o formato datetime
    colunas_data = ['Data de distribuição', 'Data de cadastro', 'Data de citação']
    
    for coluna in colunas_data:
        if coluna in df.columns:
            df[coluna] = pd.to_datetime(df[coluna], format='%d/%m/%Y', errors='coerce')
    
    return df

def processar_pergunta(pergunta, dataframe):
    hoje = pd.Timestamp.now()

    # Perguntas sobre status (ativos, arquivados, etc.)
    if "ativos" in pergunta.lower() or "ativo" in pergunta.lower():
        return processar_status(pergunta, dataframe, "ativo")
    
    elif "arquivados" in pergunta.lower() or "arquivado" in pergunta.lower():
        return processar_status(pergunta, dataframe, "arquivado")
    
    # Perguntas sobre fases
    elif "fase" in pergunta.lower() or "fases" in pergunta.lower():
        return processar_fase(dataframe)
    
    # Perguntas sobre órgãos
    elif "órgão" in pergunta.lower() or "orgao" in pergunta.lower():
        return processar_orgao(dataframe)


    # Perguntas sobre cadastros
    elif "cadastrados" in pergunta.lower() or "cadastrado" in pergunta.lower():
        return processar_datas(dataframe, "Data de cadastro", pergunta)
    
    # Perguntas sobre distribuidos
    elif "distribuidos" in pergunta.lower() or "distribuido" in pergunta.lower():
        return processar_datas(dataframe, "Data de distribuição", pergunta)
    
    # Perguntas sobre citações
    elif "citação" in pergunta.lower() or "citados" in pergunta.lower():
        return processar_datas(dataframe, "Data de citação", pergunta)




     # Se a pergunta não puder ser processada diretamente, enviar para o Gemini
    chatgemini = consultar_gemini(pergunta, dataframe)
     # Se a pergunta não puder ser processada diretamente, enviar para o Gemini
    return chatgemini

# Função auxiliar para processar perguntas sobre status (ativos, arquivados, etc.)
def processar_status(pergunta, dataframe, status):
    status_lower = status.lower()
    processos_status = dataframe[dataframe['Status'].str.lower() == status_lower]
    quantidade = processos_status.shape[0]
    
    # Retornar a chave correta dependendo do status
    if status_lower == 'ativo':
        return f"Atualmente, há {quantidade} processos ativos.", {
            "ativos": quantidade,
            "arquivados": dataframe[dataframe['Status'].str.lower() == 'arquivado'].shape[0]  # Adicionar arquivados para gráfico comparativo
        }
    elif status_lower == 'arquivado':
        return f"Atualmente, há {quantidade} processos arquivados.", {
            "ativos": dataframe[dataframe['Status'].str.lower() == 'ativo'].shape[0],  # Adicionar ativos para gráfico comparativo
            "arquivados": quantidade
        }
    else:
        return f"Atualmente, há {quantidade} processos {status}.", {
            "status": quantidade
        }
    
# Função auxiliar para processar perguntas sobre órgãos
def processar_orgao(dataframe):
    orgaos = dataframe['Órgão'].str.lower().value_counts().to_dict()
    orgaos_texto = ", ".join([f"{orgao}: {quantidade}" for orgao, quantidade in orgaos.items()])
    return f"Os órgãos estão distribuídos da seguinte forma: {orgaos_texto}.", {
        "orgaos": orgaos
    }

# Função auxiliar para processar perguntas sobre fases
def processar_fase(dataframe):
    fases = dataframe['Fase'].str.lower().value_counts().to_dict()
    fases_texto = ", ".join([f"{fase}: {quantidade}" for fase, quantidade in fases.items()])
    return f"As fases estão distribuídas da seguinte forma: {fases_texto}.", {
        "fases": fases
    }


# Função auxiliar para processar perguntas sobre datas (cadastrados, distribuidos, citados)
def processar_datas(dataframe, coluna, pergunta):
    hoje = pd.Timestamp.now()

    # Verificar se a pergunta é sobre um mês específico
    if "mês" in pergunta.lower() or "mes" in pergunta.lower():
        mes = extrair_mes_da_pergunta(pergunta)
        if mes:
            processos_mes = dataframe[dataframe[coluna].dt.month == mes]
            quantidade = processos_mes.shape[0]
            return f"No mês {mes}, foram {quantidade} processos.", {
                f"{coluna}_por_data": {str(k): v for k, v in processos_mes.groupby(processos_mes[coluna].dt.date).size().to_dict().items()}
            }
    
    # Verificar se a pergunta é sobre hoje
    elif "hoje" in pergunta.lower():
        processos_hoje = dataframe[dataframe[coluna] == hoje.normalize()]
        quantidade = processos_hoje.shape[0]
        return f"Hoje, foram {quantidade} processos.", {
            f"{coluna}_por_data": {str(hoje.date()): quantidade}
        }
    
    # Verificar se a pergunta é sobre ontem
    elif "ontem" in pergunta.lower():
        ontem = (hoje - pd.Timedelta(days=1)).normalize()
        processos_ontem = dataframe[dataframe[coluna] == ontem]
        quantidade = processos_ontem.shape[0]
        return f"Ontem, foram {quantidade} processos.", {
            f"{coluna}_por_data": {str(ontem.date()): quantidade}
        }

    # Verificar se a pergunta é sobre um intervalo de tempo (semana atual ou anterior)
    elif "semana" in pergunta.lower():
        return processar_semana(dataframe, coluna, pergunta)
    
    # Caso não encontre o período, retornar uma mensagem padrão
    return f"Não foi possível identificar o período na pergunta. Por favor, especifique uma data ou intervalo.", {}



# Função auxiliar para extrair o mês da pergunta
def extrair_mes_da_pergunta(pergunta):
    meses = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6,
        "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
    }
    for mes, numero in meses.items():
        if mes in pergunta.lower():
            return numero
    return None


# Função auxiliar para processar perguntas sobre semanas (semana atual ou anterior)
def processar_semana(dataframe, coluna, pergunta):
    hoje = pd.Timestamp.now()

    # Verificar se é a semana atual
    if "semana atual" in pergunta.lower():
        inicio_semana = hoje - pd.Timedelta(days=hoje.weekday())  # Pega o início da semana (segunda-feira)
        processos_semana = dataframe[(dataframe[coluna] >= inicio_semana) & (dataframe[coluna] <= hoje)]
        quantidade = processos_semana.shape[0]
        return f"Na semana atual, foram {quantidade} processos.", {
            f"{coluna}_por_data": {str(k): v for k, v in processos_semana.groupby(dataframe[coluna].dt.date).size().to_dict().items()}
        }

    # Verificar se é a semana anterior
    elif "semana anterior" in pergunta.lower() or "semana passada" in pergunta.lower():
        inicio_semana_anterior = (hoje - pd.Timedelta(days=hoje.weekday())) - pd.Timedelta(weeks=1)
        fim_semana_anterior = inicio_semana_anterior + pd.Timedelta(days=6)  # Fim da semana anterior (domingo)
        processos_semana_anterior = dataframe[(dataframe[coluna] >= inicio_semana_anterior) & (dataframe[coluna] <= fim_semana_anterior)]
        quantidade = processos_semana_anterior.shape[0]
        return f"Na semana anterior, foram {quantidade} processos.", {
            f"{coluna}_por_data": {str(k): v for k, v in processos_semana_anterior.groupby(dataframe[coluna].dt.date).size().to_dict().items()}
        }

    return "Não foi possível identificar a semana especificada.", {}

# Função para contar o número de tokens
def contar_tokens(texto):
    # Uma maneira simplificada de contar tokens é dividir o texto em palavras
    # Você pode ajustar isso para ser mais preciso com base no comportamento do modelo
    return len(texto.split())

# Função para consultar o Gemini com o contexto dos dados do Excel
def consultar_gemini(pergunta, dataframe):
    # Configurar a API do Gemini
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])  # Certifique-se de ter a chave de API do Gemini no seu .env
    model = genai.GenerativeModel("gemini-1.5-pro")

    # Converter todos os dados do DataFrame em uma string para fornecer contexto ao Gemini
    contexto = dataframe.to_string(index=False)
    prompt = f"Os dados a seguir são extraídos de um arquivo Excel:\n{contexto}\n\nPergunta: {pergunta}\n\nResponda de forma direta e concisa, fornecendo apenas o resultado principal, por exemplo: Atualmente, há X processos ativos. sem detalhes extras."

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
