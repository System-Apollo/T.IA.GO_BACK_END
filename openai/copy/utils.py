#utils.py

# Contém funções auxiliares, como processamento de dados do Excel e integração com ChatGPT.
import pandas as pd
import openai
import os

# Função para carregar e preparar os dados do Excel
def carregar_dados(file):
    df = pd.read_excel(file)

    # Converter colunas que são datas para o formato datetime
    colunas_data = ['Data de distribuição', 'Data de cadastro', 'Data de citação']
    
    for coluna in colunas_data:
        if coluna in df.columns:
            df[coluna] = pd.to_datetime(df[coluna], format='%d/%m/%Y', errors='coerce')
    
    return df


# Função para consultar o GPT-4 com o contexto dos dados do Excel
def consultar_chatgpt(pergunta, dataframe):
     # Converter todos os dados do DataFrame em uma string para fornecer contexto ao ChatGPT
    contexto = dataframe.head(20).to_string(index=False)
    prompt = f"Os dados a seguir são extraídos de um arquivo Excel:\n{contexto}\n\nPergunta: {pergunta}\n\nResponda de forma direta e concisa, fornecendo apenas o resultado principal, sem detalhes extras."

    # Enviar a pergunta com o contexto para o ChatGPT
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Você é um assistente que responde de forma direta e concisa, fornecendo apenas o resultado principal. Por exemplo, a quantidades em numeros."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.7,
    )
    return response['choices'][0]['message']['content'].strip()
