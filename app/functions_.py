# functions_.py
import pandas as pd
import os
import re
import locale

# Definir a localidade para o formato brasileiro
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')  # Ajuste para o sistema onde está rodando, pode ser necessário instalar o locale 'pt_BR'


# Função para processar o status do caso ou processo de um autor específico
def processar_status_autor(pergunta, dataframe):
    pergunta_lower = pergunta.lower().strip()
    # Extração do nome do autor da pergunta (assumindo nome completo)
    palavras_pergunta = pergunta_lower.split()
    nome_autor = None
    
    # Procurar o nome e sobrenome dentro da pergunta
    for i in range(len(palavras_pergunta) - 1):
        possivel_nome = f"{palavras_pergunta[i]} {palavras_pergunta[i + 1]}"
        if dataframe['Envolvidos - Polo Ativo'].str.contains(possivel_nome, case=False).any():
            nome_autor = possivel_nome
            break

    if nome_autor:
        # Filtrar o dataframe para o nome do autor e buscar o status correspondente
        status_autor = dataframe[dataframe['Envolvidos - Polo Ativo'].str.contains(nome_autor, case=False)]
        
        if not status_autor.empty:
            return f"O status do processo do {nome_autor} é: {status_autor['Status'].values[0]}", {}
        else:
            return f"Não foi encontrado nenhum processo ou caso relacionado ao autor {nome_autor}.", {}
    else:
        return "Por favor, forneça o nome completo (nome e sobrenome) do autor para que possamos identificar o caso corretamente.", {}


def processar_nao_citados(dataframe):
    # Contar processos que ainda não têm data de citação (processos não citados)
    processos_nao_citados = dataframe[dataframe['Data de citação'].isna()].shape[0]
    
    # Contar processos que já foram citados
    processos_citados = dataframe[dataframe['Data de citação'].notna()].shape[0]
    
    # Retornar o texto da resposta e os dados para o gráfico
    return f"Atualmente, há {processos_nao_citados} processos que ainda não foram citados.", {
        "processos_citados": processos_citados,
        "processos_nao_citados": processos_nao_citados
    }

def processar_nao_julgados(dataframe):
    # Considerar como processos não julgados aqueles sem resultado de sentença
    processos_nao_julgados = dataframe[dataframe['Resultado da Sentença'].isnull() | dataframe['Resultado da Sentença'].str.contains('não', case=False, na=True)]

    # Quantidade de processos não julgados
    quantidade_nao_julgados = processos_nao_julgados.shape[0]

    # Preparar o texto de resposta
    return f"Atualmente, há {quantidade_nao_julgados} processos que ainda não foram julgados.", {
        "nao_julgados": quantidade_nao_julgados
    }

def processar_divisao_por_rito(dataframe):
    # Contar a quantidade de processos por tipo de Rito
    ritos = dataframe['Rito'].str.lower().value_counts().to_dict()

    # Preparar o texto de resposta com os valores de cada rito
    ritos_texto = ", ".join([f"{rito.capitalize()}: {quantidade}" for rito, quantidade in ritos.items()])
    
    # Preparar os dados para o gráfico
    dados_grafico = {rito.capitalize(): quantidade for rito, quantidade in ritos.items()}

    # Retornar a resposta e os dados para o gráfico
    return f"A divisão dos processos por rito é: {ritos_texto}.", {
        "ritos": dados_grafico
    }

def processar_maior_tempo_sem_movimentacao(dataframe):
    # Converter as colunas 'Data de distribuição' e 'Última mov.' para o formato datetime
    dataframe['Data de distribuição'] = pd.to_datetime(dataframe['Data de distribuição'], format='%d/%m/%Y', errors='coerce')
    dataframe['Última mov.'] = pd.to_datetime(dataframe['Última mov.'], format='%d/%m/%Y', errors='coerce')

    # Calcular a diferença de dias entre 'Última mov.' e 'Data de distribuição'
    dataframe['Dias sem movimentação'] = (dataframe['Última mov.'] - dataframe['Data de distribuição']).dt.days

    # Identificar o processo com maior tempo sem movimentação
    processo_maior_tempo = dataframe.loc[dataframe['Dias sem movimentação'].idxmax()]

    # Extrair os dados do processo
    numero_processo = processo_maior_tempo['Número CNJ']
    dias_sem_movimentacao = processo_maior_tempo['Dias sem movimentação']

    # Selecionar os 4 processos com maior tempo sem movimentação
    top_4_processos = dataframe[['Número CNJ', 'Dias sem movimentação']].sort_values(by='Dias sem movimentação', ascending=False).head(4)

    # Preparar os dados para o gráfico
    dados_grafico = top_4_processos.set_index('Número CNJ').to_dict()['Dias sem movimentação']

    # Retornar a resposta e os dados para o gráfico
    return f"O processo com maior tempo sem movimentação é o número {numero_processo}, com {dias_sem_movimentacao} dias sem movimentação.", {
        "processos": dados_grafico
    }



def processar_sentencas_extinto_sem_custos(dataframe):
    # Converter a coluna 'Resultado da Sentença' para minúsculas para garantir consistência
    dataframe['Resultado da Sentença'] = dataframe['Resultado da Sentença'].str.lower()

    # Contar a quantidade de processos extintos sem custos
    extincao_sem_resolucao = dataframe[dataframe['Resultado da Sentença'] == 'sentenca de extincao sem resolucao do merito'].shape[0]
    improcedentes = dataframe[dataframe['Resultado da Sentença'] == 'sentenca improcedente'].shape[0]

    # Soma dos processos sem custos
    total_extinto_sem_custos = extincao_sem_resolucao + improcedentes

    # Contar todos os tipos de sentenças para o gráfico
    sentencas_contagem = dataframe['Resultado da Sentença'].value_counts().to_dict()

    # Abreviações das sentenças para o gráfico
    abreviacoes_sentencas = {
        "sentenca improcedente": "Improcedente",
        "sentenca de extincao sem resolucao do merito": "Sem resolução do mérito",
        "sentenca parcialmente procedente": "Procedente",
        "sentenca de homologacao de acordo": "Acordo"
    }

    # Substituir as legendas pelas abreviações no dicionário de sentenças
    sentencas_abreviadas = {abreviacoes_sentencas.get(key, key): value for key, value in sentencas_contagem.items()}

    # Retornar a resposta e os dados para o gráfico
    return f"Há {total_extinto_sem_custos} processos extintos sem custos (incluindo extinção sem resolução e improcedentes).", {
        "sentencas": sentencas_abreviadas
    }


def processar_sentencas_improcedentes(dataframe):
    # Converter a coluna 'Resultado da Sentença' para minúsculas para garantir consistência
    dataframe['Resultado da Sentença'] = dataframe['Resultado da Sentença'].str.lower()

    # Contar a quantidade de sentenças improcedentes
    quantidade_improcedentes = dataframe[dataframe['Resultado da Sentença'] == 'sentenca improcedente'].shape[0]

    # Contar todos os tipos de sentenças para o gráfico
    sentencas_contagem = dataframe['Resultado da Sentença'].value_counts().to_dict()

    # Abreviações das sentenças para o gráfico
    abreviacoes_sentencas = {
        "sentenca improcedente": "Improcedente",
        "sentenca de extincao sem resolucao do merito": "Sem resolução do mérito",
        "sentenca parcialmente procedente": "Procedente",
        "sentenca de homologacao de acordo": "Acordo"
    }

    # Substituir as legendas pelas abreviações no dicionário de sentenças
    sentencas_abreviadas = {abreviacoes_sentencas.get(key, key): value for key, value in sentencas_contagem.items()}

    # Retornar a resposta e os dados para o gráfico
    return f"Há {quantidade_improcedentes} processos com sentença improcedente.", {
        "sentencas": sentencas_abreviadas
    }


def processar_media_duracao_por_estado(dataframe):
    # Converter as colunas 'Última mov.' e 'Data de distribuição' para datetime, corrigindo o formato
    dataframe['Última mov.'] = pd.to_datetime(dataframe['Última mov.'], format='%d/%m/%Y', errors='coerce')
    dataframe['Data de distribuição'] = pd.to_datetime(dataframe['Data de distribuição'], format='%d/%m/%Y', errors='coerce')

    # Calcular a duração do processo (diferença entre 'Última mov.' e 'Data de distribuição')
    dataframe['Duração'] = (dataframe['Última mov.'] - dataframe['Data de distribuição']).dt.days

    # Remover valores de duração inválidos (NaN)
    dataframe = dataframe.dropna(subset=['Duração'])

    # Verificar se há dados suficientes para continuar
    if dataframe.empty:
        return "Não há dados suficientes para calcular a média de duração por estado.", {}

    # Extrair o estado da coluna 'Foro'
    dataframe['Estado'] = dataframe['Foro'].str.split('-').str[-1].str.strip()

    # Calcular a média de duração por estado
    media_duracao_por_estado = dataframe.groupby('Estado')['Duração'].mean().to_dict()

    if not media_duracao_por_estado:
        return "Não foi possível calcular a média de duração por estado.", {}

    # Identificar o estado com a maior média de duração
    estado_maior_media = max(media_duracao_por_estado, key=media_duracao_por_estado.get)
    maior_media = media_duracao_por_estado[estado_maior_media]
    
    

    return f"O estado com a maior média de duração dos processos é {estado_maior_media}, com uma média de {maior_media:.0f} dias.", {
        "media_duracao_por_estado": media_duracao_por_estado
    }

def processar_media_duracao_por_comarca(dataframe):
    # Converter as colunas 'Última mov.' e 'Data de distribuição' para datetime, corrigindo o formato
    dataframe['Última mov.'] = pd.to_datetime(dataframe['Última mov.'], format='%d/%m/%Y', errors='coerce')
    dataframe['Data de distribuição'] = pd.to_datetime(dataframe['Data de distribuição'], format='%d/%m/%Y', errors='coerce')

    # Calcular a duração do processo (diferença entre 'Última mov.' e 'Data de distribuição')
    dataframe['Duração'] = (dataframe['Última mov.'] - dataframe['Data de distribuição']).dt.days

    # Remover valores de duração inválidos (NaN)
    dataframe = dataframe.dropna(subset=['Duração'])

    # Verificar se há dados suficientes para continuar
    if dataframe.empty:
        return "Não há dados suficientes para calcular a média de duração por comarca.", {}

    # Extrair o município (comarca) da coluna 'Foro'
    dataframe['Comarca'] = dataframe['Foro'].str.split('-').str[0].str.strip()

    # Calcular a média de duração por comarca
    media_duracao_por_comarca = dataframe.groupby('Comarca')['Duração'].mean().to_dict()

    if not media_duracao_por_comarca:
        return "Não foi possível calcular a média de duração por comarca.", {}

    # Identificar a comarca com a maior média de duração
    comarca_maior_media = max(media_duracao_por_comarca, key=media_duracao_por_comarca.get)
    maior_media = media_duracao_por_comarca[comarca_maior_media]

    return f"A comarca com a maior média de duração dos processos é {comarca_maior_media}, com uma média de {maior_media:.0f} dias.", {
        "media_duracao_por_comarca": media_duracao_por_comarca
    }


def processar_media_duracao_processos_arquivados(dataframe):
    # Filtrar os processos arquivados
    processos_arquivados = dataframe[dataframe['Status'].str.lower() == 'arquivado']

    # Garantir que as colunas de data estejam no formato correto e tratar valores inválidos
    processos_arquivados['Última mov.'] = pd.to_datetime(processos_arquivados['Última mov.'], format='%d/%m/%Y', errors='coerce')
    processos_arquivados['Data de distribuição'] = pd.to_datetime(processos_arquivados['Data de distribuição'], format='%d/%m/%Y', errors='coerce')

    # Remover linhas onde uma das datas é inválida (NaT)
    processos_arquivados = processos_arquivados.dropna(subset=['Última mov.', 'Data de distribuição'])

    # Verificar se há processos suficientes para calcular a duração
    if processos_arquivados.empty:
        return "Não foi possível calcular a média de duração dos processos arquivados.", {}

    # Calcular a duração (diferença em dias entre Última mov. e Data de distribuição)
    processos_arquivados['Duração'] = (processos_arquivados['Última mov.'] - processos_arquivados['Data de distribuição']).dt.days

    # Calcular a média da duração
    media_duracao = processos_arquivados['Duração'].mean()

    # Retornar a média
    return f"A média de duração dos processos arquivados é de {media_duracao:.0f} dias.", {
        "duração_por_processo": processos_arquivados['Duração'].to_dict()
    }



def extrair_comarca(foro):
    """Função para extrair o município (comarca) da coluna 'Foro'."""
    match = re.match(r"^(.+?)\s*-\s*[A-Z]{2}", foro)
    if match:
        return match.group(1).strip()  # Retorna o nome do município (comarca)
    return foro  # Caso não encontre o formato esperado, retorna o valor original

def processar_comarca_mais_preocupante(dataframe):
    # Extrair a comarca (município) da coluna 'Foro'
    dataframe['Comarca'] = dataframe['Foro'].apply(extrair_comarca)

    # Limpar e converter a coluna 'Total deferido' para float, tratando apenas strings
    dataframe['Total deferido'] = dataframe['Total deferido'].apply(lambda x: str(x) if isinstance(x, str) else x)
    dataframe['Total deferido'] = pd.to_numeric(
        dataframe['Total deferido']
        .str.replace('R$', '', regex=False)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False),
        errors='coerce'
    )

    # Agrupar por comarca e somar os valores de condenação
    valor_condenacao_por_comarca = dataframe.groupby('Comarca')['Total deferido'].sum()

    # Verificar qual comarca tem o maior valor de condenação
    comarca_mais_preocupante = valor_condenacao_por_comarca.idxmax()
    maior_valor = valor_condenacao_por_comarca.max()

    # Converter os dados para um formato gráfico
    dados_grafico = valor_condenacao_por_comarca.to_dict()

    return f"A comarca com o maior valor de condenação é {comarca_mais_preocupante}, com um total de R$ {maior_valor:,.2f}.", {
        "valor_condenacao_por_comarca": dados_grafico  # Dados para o gráfico
    }

def processar_estado_mais_ofensor(dataframe):
    # Garantir que todos os valores na coluna 'Total deferido' sejam strings antes de aplicar as substituições
    dataframe['Total deferido'] = dataframe['Total deferido'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)

    # Converter para float
    dataframe['Total deferido'] = pd.to_numeric(dataframe['Total deferido'], errors='coerce')

    # Agrupar por estado (Foro) e somar os valores de condenação
    valor_condenacao_por_estado = dataframe.groupby('Foro')['Total deferido'].sum()

    # Verificar qual estado tem o maior valor de condenação
    estado_mais_preocupante = valor_condenacao_por_estado.idxmax()
    maior_valor = valor_condenacao_por_estado.max()

    # Converter os dados para um formato gráfico
    dados_grafico = valor_condenacao_por_estado.to_dict()

    return f"O estado com o maior valor de condenação é {estado_mais_preocupante}, com um total de R$ {maior_valor:,.2f}.", {
        "valor_condenacao_por_estado": dados_grafico  # Dados para o gráfico
    }


def processar_reclamantes_multiplos(dataframe):
    # Remover qualquer tipo de espaço antes e depois dos nomes
    dataframe['Envolvidos - Polo Ativo'] = dataframe['Envolvidos - Polo Ativo'].str.strip()

    # Contar quantos processos cada reclamante tem
    reclamantes = dataframe['Envolvidos - Polo Ativo'].value_counts()

    # Filtrar os reclamantes que têm mais de um processo
    reclamantes_multiplos = reclamantes[reclamantes > 1].to_dict()

    if len(reclamantes_multiplos) > 0:
        reclamantes_texto = ", ".join([f"{reclamante}: {quantidade} processos" for reclamante, quantidade in reclamantes_multiplos.items()])
        return f"Os reclamantes com mais de um processo são: {reclamantes_texto}.", {
            "reclamantes_multiplos": reclamantes_multiplos  # Dados para gráfico
        }
    else:
        return "Nenhum reclamante tem mais de um processo.", {}
    
def processar_rito(dataframe):
    # Contar a quantidade de processos por tipo de rito
    ritos = dataframe['Rito'].str.lower().value_counts().to_dict()

    # Verificar quantos processos estão no rito sumaríssimo
    quantidade_sumarissimo = ritos.get('sumaríssimo', 0)  # A contagem de "Sumaríssimo" no dataframe

    return f"Há {quantidade_sumarissimo} processos no rito sumaríssimo.", {
        "ritos": ritos  # Retorna todos os ritos para exibição no gráfico
    }
def processar_tribunal_acoes_convenções(dataframe):
    # Filtrar as linhas onde o assunto é "Acordo e Convenção Coletivos de Trabalho"
    convenções = dataframe[dataframe['Assuntos'].str.contains('Acordo e Convenção Coletivos de Trabalho', case=False, na=False)]
    
    # Contar os tribunais (coluna Órgão) associados a essas ações
    tribunais = convenções['Órgão'].value_counts().to_dict()

    # Verificar qual tribunal tem mais ações
    if tribunais:
        tribunal_mais_acoes = max(tribunais, key=tribunais.get)
        quantidade = tribunais[tribunal_mais_acoes]
        return f"O tribunal com mais ações sobre convenções coletivas é {tribunal_mais_acoes} com {quantidade} ações.", {
            "tribunais": tribunais  # Retorna todos os tribunais para o gráfico
        }
    else:
        return "Não foram encontradas ações sobre convenções coletivas nos tribunais.", {}


# Função para processar os assuntos mais recorrentes
def processar_assuntos_recorrentes(dataframe):
    # Contar a frequência dos assuntos na coluna "Assuntos"
    assuntos = dataframe['Assuntos'].str.lower().value_counts().to_dict()

    # Abreviar os nomes dos assuntos
    assuntos_abreviados = {abreviar_assuntos(assunto): quantidade for assunto, quantidade in assuntos.items()}

    # Ordenar os assuntos pela quantidade e pegar os 2 primeiros
    dois_mais_recorrentes = dict(list(assuntos_abreviados.items())[:2])

    # Preparar a resposta para os 2 mais recorrentes
    assuntos_texto = ", ".join([f"{assunto}: {quantidade}" for assunto, quantidade in dois_mais_recorrentes.items()])
    return f"Os dois assuntos mais recorrentes são: {assuntos_texto}.", {
        "assuntos": assuntos_abreviados  # Enviar todos para o gráfico com abreviações
    }
# Função auxiliar para abreviar os nomes longos dos assuntos
def abreviar_assuntos(assunto):
    abreviacoes = {
        "acordo e convenção coletivos de trabalho": "Acordo/Convenção",
        "verbas rescisórias": "Verbas Rescisórias",
        "estabilidade acidentária": "Estabilidade Acident.",
        "indenização por dano moral": "Dano Moral",
        "indenização por dano material": "Dano Material",
        "rescisão indireta": "Rescisão Indireta",
        "diferença de comissão": "Dif. Comissão",
        "gestante": "Gestante",
        "doença ocupacional": "Doença Ocup."
        # Adicione mais abreviações conforme necessário
    }

    return abreviacoes.get(assunto.lower(), assunto)  # Retorna a abreviação se houver, caso contrário retorna o original
# Função para processar a quantidade de recursos interpostos
def processar_quantidade_recursos(dataframe):
    # Remover espaços extras e converter para minúsculas para evitar problemas de formatação
    dataframe['Tipo de Recurso'] = dataframe['Tipo de Recurso'].str.strip().str.lower()

    # Contar os processos com recursos (diferentes de '-')
    recursos_interpostos = dataframe[dataframe['Tipo de Recurso'] != '-'].shape[0]

    # Contar os processos sem recursos
    sem_recursos = dataframe[dataframe['Tipo de Recurso'] == '-'].shape[0]

    # Retornar a resposta com a quantidade de recursos interpostos e os dados para o gráfico
    return f"Foram interpostos {recursos_interpostos} recursos, e {sem_recursos} processos não têm recurso.", {
        "com_recursos": recursos_interpostos,
        "sem_recursos": sem_recursos
    }

def processar_quantidade_processos_por_estado(dataframe):
    # Agrupar os processos por estado (coluna 'Foro') e contar a quantidade de processos por estado
    processos_por_estado = dataframe['Foro'].value_counts().to_dict()

    # Preparar a resposta textual
    estados_texto = ", ".join([f"{estado}: {quantidade}" for estado, quantidade in processos_por_estado.items()])
    resposta = f"A quantidade de processos por estado está distribuída da seguinte forma: {estados_texto}."

    # Preparar os dados para o gráfico
    grafico_data = {
        "estados": processos_por_estado
    }

    return resposta, grafico_data
# Função para contagem de numero de processo ,e separa por ativos e arquivados
def processar_quantidade_processos(dataframe):
    # Contar a quantidade total de processos
    total_processos = int(dataframe['Número CNJ'].count())

    # Contar os processos ativos e arquivados
    processos_ativos = int(dataframe[dataframe['Status'].str.lower() == 'ativo']['Número CNJ'].count())
    processos_arquivados = int(dataframe[dataframe['Status'].str.lower() == 'arquivado']['Número CNJ'].count())

    # Retornar a resposta e os dados do gráfico
    return f"Há um total de {total_processos} processos. Destes, {processos_ativos} são ativos e {processos_arquivados} estão arquivados.", {
        "ativos": processos_ativos,
        "arquivados": processos_arquivados
    }

# Função auxiliar para processar perguntas sobre "Data de Trânsito em Julgado"
def processar_transito_julgado(dataframe):
    # Verificar quais células da coluna 'Data de Trânsito em Julgado' têm data e quais estão vazias
    transitado = dataframe['Data de Trânsito em Julgado'].notna() & dataframe['Data de Trânsito em Julgado'].apply(lambda x: str(x).strip() != '-')
    processos_transitados = int(transitado.sum())  # Converte para tipo int nativo
    processos_nao_transitados = int((~transitado).sum())  # Converte para tipo int nativo

    # Retornar a resposta e os dados para o gráfico
    return f"Atualmente, {processos_transitados} processos já transitaram em julgado e {processos_nao_transitados} ainda não.", {
        "transitados": processos_transitados,
        "nao_transitados": processos_nao_transitados
    }

# Função auxiliar para processar perguntas sobre "Resultado da Sentença"
def processar_sentenca(dataframe, pergunta):
    sentencas = dataframe['Resultado da Sentença'].str.lower().value_counts().to_dict()

    # Dicionário de abreviações para as sentenças
    abreviacoes_sentencas = {
        "sentenca improcedente": "Improcedente",
        "sentenca de extincao sem resolucao do merito": "Sem resolução do mérito",
        "sentenca parcialmente procedente": "Procedente",
        "sentenca de homologacao de acordo": "Acordo"
    }

    # Substituir as legendas pelas abreviações no dicionário de sentenças
    sentencas_abreviadas = {abreviacoes_sentencas.get(key, key): value for key, value in sentencas.items()}

    # Se a pergunta mencionar "divididos" ou "resultados dos processos", retornamos as divisões das sentenças
    if "divididos" in pergunta.lower() or "resultados dos processos" in pergunta.lower():
        sentencas_texto = ", ".join([f"{sentenca}: {quantidade}" for sentenca, quantidade in sentencas_abreviadas.items()])
        return f"Os resultados das sentenças estão divididos da seguinte forma: {sentencas_texto}.", {
            "sentencas": sentencas_abreviadas
        }

    # Termos comuns relacionados às sentenças
    termos_sentenca = {
        "extinção sem resolução do mérito": "Sem resolução do mérito",
        "parcialmente procedente": "Procedente",
        "improcedente": "Improcedente",
        "homologação de acordo": "Acordo"
    }

    # Verificar se alguma sentença específica foi mencionada na pergunta
    for termo, abreviado in termos_sentenca.items():
        if termo in pergunta.lower():
            quantidade = sentencas_abreviadas.get(abreviado, 0)  # Se não existir, retorna 0
            return f"Atualmente, existem {quantidade} processos com o resultado de {abreviado}.", {
                "sentencas": sentencas_abreviadas  # Sempre retornar todas as sentenças para gráficos
            }
    
    # Se a sentença específica não for reconhecida
    return "O resultado de sentença especificado não foi encontrado. Os resultados disponíveis são: " + ", ".join(sentencas_abreviadas.keys()), {
        "sentencas": sentencas_abreviadas
    }

# Função para processar o valor total da causa
def processar_valor_total_causa(dataframe):
    # Converter a coluna 'Total da causa' para valores numéricos (removendo símbolos de moeda e ajustando formatação)
    dataframe['Total da causa'] = pd.to_numeric(
        dataframe['Total da causa']
        .str.replace('R$', '', regex=False)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False), errors='coerce'
    )

    # Somar o valor total da causa para todos os processos
    valor_total_causa = dataframe['Total da causa'].sum()

    # Dividir o total por status (ativo e arquivado)
    total_ativos = dataframe[dataframe['Status'].str.lower() == 'ativo']['Total da causa'].sum()
    total_arquivados = dataframe[dataframe['Status'].str.lower() == 'arquivado']['Total da causa'].sum()

    # Formatar os valores no padrão brasileiro
    valor_total_causa_formatado = f"{valor_total_causa:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    total_ativos_formatado = f"{total_ativos:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    total_arquivados_formatado = f"{total_arquivados:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Retornar a resposta com o valor total e os dados para o gráfico
    resposta_texto = f"O valor total da causa é de R$ {valor_total_causa_formatado}.\n" \
                     f"Total de ativos: R$ {total_ativos_formatado}.\n" \
                     f"Total de arquivados: R$ {total_arquivados_formatado}."

    return resposta_texto, {
        "ativos": total_ativos,
        "arquivados": total_arquivados
    }


def processar_media_valor_causa_por_estado(dataframe):
    # Limpar e converter os valores na coluna "Total da causa"
    dataframe['Total da causa'] = pd.to_numeric(
        dataframe['Total da causa']
        .str.replace('R$', '', regex=False)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False),
        errors='coerce'
    )
    
    # Agrupar por estado (coluna Foro) e calcular a média
    media_valor_por_estado = dataframe.groupby('Foro')['Total da causa'].mean().dropna()
    
    # Encontrar o estado com a maior média
    estado_maior_media = media_valor_por_estado.idxmax()
    maior_media = media_valor_por_estado.max()

    # Formatar a média no estilo brasileiro (R$ X.XXX.XXX,XX)
    resposta_texto = f"O estado com a maior média de valor de causa é {estado_maior_media} com uma média de R$ {maior_media:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Retornar a resposta e os dados do gráfico
    return resposta_texto, {
        "media_valor_causa_por_estado": media_valor_por_estado.to_dict()
    }


def processar_maior_valor_causa_por_estado(dataframe):
    # Converter a coluna 'Total da causa' para string, limpar e converter para float
    dataframe['Total da causa'] = dataframe['Total da causa'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    
    # Converter para numérico, tratando erros como NaN
    dataframe['Total da causa'] = pd.to_numeric(dataframe['Total da causa'], errors='coerce')

    # Agrupar por estado (coluna 'Foro') e somar os valores de 'Total da causa'
    soma_por_estado = dataframe.groupby('Foro')['Total da causa'].sum()

    # Encontrar o estado com o maior valor de causa
    estado_com_maior_valor = soma_por_estado.idxmax()
    maior_valor = soma_por_estado.max()

   # Criar a resposta textual, formatando o valor no estilo brasileiro (R$ X.XXX.XXX,XX)
    resposta_texto = f"O estado com o maior valor de causa é {estado_com_maior_valor}, com um total de R$ {maior_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # Retornar os dados em um formato serializável para o gráfico
    return resposta_texto, {
        "valor_causa_por_estado": soma_por_estado.to_dict()
    }

def processar_valor_condenacao_por_estado(dataframe):
    # Converter os valores da coluna 'Total deferido (condenação)' para string e remover 'R$', '.', e ',' para transformar em float
    dataframe['Total deferido'] = dataframe['Total deferido'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)

    # Converter a coluna para valores numéricos, tratando os erros como NaN
    dataframe['Total deferido'] = pd.to_numeric(dataframe['Total deferido'], errors='coerce')

    # Agrupar por estado (coluna 'Foro') e somar os valores
    soma_por_estado = dataframe.groupby('Foro')['Total deferido'].sum()
    

     # Criar a resposta textual, formatando os valores no estilo brasileiro (R$ X.XXX,XX)
    resposta_texto = "O valor total de condenações por estado é:\n"
    resposta_texto += "\n".join([f"{estado}: R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') for estado, valor in soma_por_estado.items()])
    # Retornar os dados em um formato serializável para o gráfico
    return resposta_texto, {
        "condenacao_por_estado": soma_por_estado.to_dict()  # Retorna um dicionário com os valores para o gráfico
    }


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
        return f"Atualmente, há {quantidade} processos arquivados/encerrados.", {
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

def processar_fase(dataframe, pergunta=None):
    # Converter a coluna 'Fase' para minúsculas para facilitar a comparação
    fases = dataframe['Fase'].str.lower().value_counts().to_dict()
    
    # Se a pergunta não especifica uma fase particular, retorna todas as fases
    if not pergunta or "fase" in pergunta.lower():
        fases_texto = ", ".join([f"{fase}: {quantidade}" for fase, quantidade in fases.items()])
        return f"As fases estão distribuídas da seguinte forma: {fases_texto}.", {
            "fases": fases
        }
    
    # Agora, vamos verificar se a pergunta menciona uma fase específica
    termos_fase = {
        "recursal": "recursal",
        "arquivado": "arquivado",
        "finalizado": "finalizado",
        "conciliatória": "conciliatória",
        "julgamento": "julgamento",
        "executória": "executória"
    }

    # Verificar se alguma fase específica foi mencionada na pergunta
    for termo, fase in termos_fase.items():
        if termo in pergunta.lower():
            quantidade = fases.get(fase.lower(), 0)  # Se não existir, retorna 0
            return f"Atualmente, existem {quantidade} processos na fase {fase}.", {
                "fases": fases  # Sempre retornar todas as fases para gráficos
            }
    
    # Se a fase específica não for reconhecida
    return "A fase especificada não foi encontrada. As fases disponíveis são: " + ", ".join(fases.keys()), {
        "fases": fases
    }
# Função auxiliar para processar perguntas sobre "Resultado da Sentença"
def processar_sentenca(dataframe, pergunta):
    sentencas = dataframe['Resultado da Sentença'].str.lower().value_counts().to_dict()

    # Dicionário de abreviações para as sentenças
    abreviacoes_sentencas = {
        "sentenca improcedente": "Improcedente",
        "sentenca de extincao sem resolucao do merito": "Sem resolução do mérito",
        "sentenca parcialmente procedente": "Procedente",
        "sentenca de homologacao de acordo": "Acordo"
    }

    # Substituir as legendas pelas abreviações no dicionário de sentenças
    sentencas_abreviadas = {abreviacoes_sentencas.get(key, key): value for key, value in sentencas.items()}

    # Se a pergunta não especificar uma sentença particular, retorna todas as sentenças
    if "sentença" in pergunta.lower():
        sentencas_texto = ", ".join([f"{sentenca}: {quantidade}" for sentenca, quantidade in sentencas_abreviadas.items()])
        return f"Os resultados das sentenças estão distribuídos da seguinte forma: {sentencas_texto}.", {
            "sentencas": sentencas_abreviadas
        }

    # Termos comuns relacionados às sentenças
    termos_sentenca = {
        "extinção sem resolução do mérito": "Sem resolução do mérito",
        "parcialmente procedente": "Procedente",
        "improcedente": "Improcedente",
        "homologação de acordo": "Acordo"
    }

    # Verificar se alguma sentença específica foi mencionada na pergunta
    for termo, abreviado in termos_sentenca.items():
        if termo in pergunta.lower():
            quantidade = sentencas_abreviadas.get(abreviado, 0)  # Se não existir, retorna 0
            return f"Atualmente, existem {quantidade} processos com o resultado de {abreviado}.", {
                "sentencas": sentencas_abreviadas  # Sempre retornar todas as sentenças para gráficos
            }
    
    # Se a sentença específica não for reconhecida
    return "O resultado de sentença especificado não foi encontrado. Os resultados disponíveis são: " + ", ".join(sentencas_abreviadas.keys()), {
        "sentencas": sentencas_abreviadas
    }

def processar_valor_acordo(dataframe):
    if 'Valor do acordo' in dataframe.columns:
        # Garantir que todos os valores estão no formato de string
        dataframe['Valor do acordo'] = dataframe['Valor do acordo'].astype(str)
        
        # Remover símbolos de moeda e converter valores para numéricos
        dataframe['Valor do acordo'] = (
            dataframe['Valor do acordo']
            .str.replace('R$', '', regex=False)  # Remover o símbolo 'R$'
            .str.replace('.', '', regex=False)   # Remover os pontos dos milhares
            .str.replace(',', '.', regex=False)  # Substituir vírgula por ponto para decimal
        )
        
        # Converter os valores da coluna para numéricos
        dataframe['Valor do acordo'] = pd.to_numeric(dataframe['Valor do acordo'], errors='coerce')
        
        # Somar os valores, ignorando os NaN
        valor_total_acordo = dataframe['Valor do acordo'].sum()

        # Contar quantos valores de acordo existem (sem contar valores 0)
        quantidade_acordos = dataframe[dataframe['Valor do acordo'] > 0]['Valor do acordo'].count()
        
        # Preparar dados para gráfico (quantidade e valor total), convertendo para tipos JSON-serializáveis
        grafico_data = {
            "Quantidade de Acordos": int(quantidade_acordos),  # Converter para int
            "Valor Total": float(valor_total_acordo)  # Converter para float
        }
        
        # Formatar o valor total no formato de moeda brasileiro
        valor_total_acordo_formatado = locale.currency(valor_total_acordo, grouping=True, symbol=True)
        
        # Retornar a resposta e os dados para o gráfico
        return f"O valor total dos acordos é de R$ {valor_total_acordo_formatado} com {quantidade_acordos} acordos.", grafico_data
    else:
        return "Não foi possível calcular o valor total dos acordos, coluna 'Valor do acordo' não encontrada.", {}


    
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
        ontem = (pd.Timestamp.now() - pd.Timedelta(days=1)).normalize()
        processos_ontem = dataframe[dataframe[coluna] == ontem]
        quantidade = processos_ontem.shape[0]
        return f"Ontem, foram {quantidade} processos.", {
            f"{coluna}_por_data": {str(ontem.date()): quantidade}
        }

    # Verificar se a pergunta é sobre um intervalo de tempo (semana atual ou anterior)
    elif "semana" in pergunta.lower():
        return processar_semana(dataframe, coluna, pergunta)

    # Caso não encontre o período, retornar uma mensagem padrão com dois valores
    return f"Não foi possível identificar o período na pergunta.", {}




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

    # Caso não identifique a semana corretamente, retornar mensagem padrão
    return f"Não foi possível identificar a semana especificada.", {}