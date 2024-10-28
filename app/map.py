from collections import defaultdict
import re

# Dicionário para mapear tipos de perguntas e suas variações
categoria_perguntas = defaultdict(list)

# Mapeamento de categorias para funções
categoria_perguntas['valor_total_acordos'] = [
    r"valor total de acordos", 
    r"qual o valor total dos acordos", 
    r"quanto foi o total de acordos", 
    r"acordos total"
]

categoria_perguntas['valor_condenacao_estado'] = [
    r"valor de condenacao por estado", 
    r"quanto foi condenado por estado", 
    r"qual o valor da condenacao em cada estado"
]

categoria_perguntas['estado_maior_valor_causa'] = [
    r"estado com maior valor da causa", 
    r"qual estado tem o maior valor da causa",
    r"qual estado tem a maior causa"
]

categoria_perguntas['estado_maior_media_valor_causa'] = [
    r"estado com maior media de valor da causa", 
    r"qual estado tem a maior media da causa", 
    r"qual a media maior de valor da causa por estado"
]

categoria_perguntas['divisao_resultados_processos'] = [
    r"divididos os resultados dos processos", 
    r"como estão divididos os resultados", 
    r"divisao dos resultados dos processos"
]

categoria_perguntas['transitaram_julgado'] = [
    r"transitaram em julgado", 
    r"processos que transitaram em julgado"
]

categoria_perguntas['quantidade_processos_estado'] = [
    r"quantidade de processos por estado", 
    r"quantos processos existem em cada estado", 
    r"numero de processos por estado",
    r"quantos processos por estado",
]

categoria_perguntas['quantidade_total_processos'] = [
    r"quantidade total de processos", 
    r"quantos processos existem no total", 
    r"quantos processos ao todo"
]

categoria_perguntas['valor_total_causa'] = [
    r"valor total da causa", 
    r"qual o valor total das causas", 
    r"total de valor de causa"
]

categoria_perguntas['processos_ativos'] = [
    r"quantos processos ativos", 
    r"processos ativos", 
    r"quantos processos tenho ativos", 
    r"numero de processos ativos"
]

categoria_perguntas['processos_arquivados'] = [
    r"quantos processos arquivados", 
    r"processos arquivados", 
    r"numero de processos arquivados"
]

categoria_perguntas['quantidade_recursos'] = [
    r"quantos recursos foram interpostos", 
    r"numero de recursos interpostos", 
    r"recursos interpostos"
]

categoria_perguntas['sentencas'] = [
    r"divisao dos resultados das sentencas", 
    r"divisao das sentencas", 
    r"como estao divididos os resultados das sentencas"
]

categoria_perguntas['assuntos_recorrentes'] = [
    r"assuntos mais recorrentes", 
    r"quais os assuntos mais recorrentes", 
    r"assuntos mais frequentes"
]

categoria_perguntas['tribunal_acoes_convencoes'] = [
    r"tribunal tem mais acoes sobre convencoes coletivas", 
    r"qual tribunal tem mais casos sobre convencoes coletivas"
]

categoria_perguntas['rito_sumarisimo'] = [
    r"rito sumarisimo", 
    r"processos no rito sumaríssimo"
]

categoria_perguntas['divisao_fase'] = [
    r"divisao por fase", 
    r"como está a divisao dos processos por fase"
]

categoria_perguntas['reclamantes_multiplos'] = [
    r"algum reclamante tem mais de um processo", 
    r"reclamantes com mais de um processo"
]

categoria_perguntas['estado_mais_ofensor'] = [
    r"estado devo ter mais preocupacao", 
    r"estado mais ofensor", 
    r"qual estado é o mais preocupante"
]

categoria_perguntas['comarca_mais_ofensora'] = [
    r"comarca devo ter mais preocupacao", 
    r"comarca mais ofensora", 
    r"qual comarca é a mais preocupante"
]

categoria_perguntas['melhor_estrategia'] = [
    r"melhor estrategia para aplicar nesse estado", 
    r"qual estrategia é melhor para aplicar no estado"
]

categoria_perguntas['beneficio_economico_carteira'] = [
    r"beneficio economico da carteira", 
    r"qual o beneficio economico da carteira", 
    r"carteira economico beneficio"
]

categoria_perguntas['beneficio_economico_estado'] = [
    r"beneficio economico por estado", 
    r"qual o beneficio economico em cada estado"
]

categoria_perguntas['idade_carteira'] = [
    r"idade da carteira", 
    r"qual a idade da carteira"
]

categoria_perguntas['maior_media_duracao_estado'] = [
    r"estado com maior media de duracao", 
    r"qual estado tem a maior media de duracao"
]

categoria_perguntas['maior_media_duracao_comarca'] = [
    r"comarca com maior media de duracao", 
    r"qual comarca tem a maior media de duracao"
]

categoria_perguntas['processos_improcedentes'] = [
    r"quantos processos improcedentes", 
    r"quantos processos improcedente", 
    r"processos julgados improcedentes",
    r"quais os processos foram improcedentes",
    r"quais os processos foram improcedente",
    r"processos improcedentes"
]
categoria_perguntas['processos_procedentes'] = [
    r"quantos processos procedentes", 
    r"processos julgados procedentes",
    r"quais os processos foram procedentes",
    r"quais os processos foram procedente",
    r"processos procedentes"
]

categoria_perguntas['processos_extintos_sem_custos'] = [
    r"quantos processos extinto sem custos", 
    r"processos extintos sem custos"
]

categoria_perguntas['processo_maior_tempo_sem_movimentacao'] = [
    r"processo com maior tempo sem movimentacao", 
    r"qual processo está mais tempo sem movimentação"
]

categoria_perguntas['divisao_por_rito'] = [
    r"como esta a divisao por rito", 
    r"qual a divisao dos processos por rito"
]

categoria_perguntas['processos_nao_julgados'] = [
    r"quantos processos ainda nao foram julgados", 
    r"processos não julgados"
]

categoria_perguntas['processos_nao_citados'] = [
    r"quantos processos ainda nao foram citados", 
    r"processos não citados"
]

categoria_perguntas['processo_mais_antigo'] = [
    r"processo mais antigo da base", 
    r"qual o processo mais antigo"
]
