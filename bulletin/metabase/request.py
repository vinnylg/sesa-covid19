from bulletin.commom.normalize import trim_overspace
import requests
import pandas as pd
import json
import io
import urllib3
import cgi
from clint.textui import progress
from os import makedirs
from os.path import join, dirname, isdir
from bulletin import __file__ as __root__
from retry import retry

urllib3.disable_warnings()

# class Metabase:
#     def __init__(self):
#     def login(self):
#         email = input('enter with email')
#         email = input('enter with email')

#     def logout(self):

@retry(Exception, delay=10, tries=-1)
def download_metabase(filename=None, where='nt.metodo <> "" AND nt.metodo <> "3" AND nt.metodo IS NOT NULL AND nt.excluir_ficha = "2" AND nt.uf_residencia = "41" AND nt.uf_unidade_notifica = "41" AND (nt.status_notificacao = "1" OR nt.status_notificacao = "2")', limit='ALL', offset='0'):
    if not isdir(join('input','queries_exames')):
        makedirs(join('input','queries_exames'))

    header = {
        'Host':'metabase.saude.pr.gov.br',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language':'pt-BR',
        'Accept-Encoding':'gzip, deflate, br',
        'Content-Type':'application/x-www-form-urlencoded',
        'Origin':'https://metabase.saude.pr.gov.br',
        'Connection':'keep-alive',
        'Referer':'https://metabase.saude.pr.gov.br/question',
        'Cookie':'metabase.SESSION=bbc6832e-7d85-43fb-b9d6-79f001af0cea',
        'Upgrade-Insecure-Requests':'1'
    }

    # sql = f"SELECT nt.id, nt.paciente, to_char(nt.data_nascimento,'DD/MM/YYYY') AS data_nascimento, nt.nome_mae, nt.cpf, nt.tipo_paciente AS cod_tipo_paciente, tpp.valor AS tipo_paciente, nt.idade, CASE WHEN nt.sexo = '1' THEN 'M' WHEN nt.sexo = '2' THEN 'F' ELSE '' END AS sexo, nt.raca_cor AS cod_raca_cor, rc.valor AS raca_cor, nt.etnia AS cod_etnia, etn.etnia, nt.uf_residencia, nt.ibge_residencia, nt.classificacao_final AS cod_classificacao_final, clf.valor AS classificacao_final, nt.criterio_classificacao AS cod_criterio_classificacao, ccl.valor AS criterio_classificacao, nt.evolucao AS evolucao, evo.valor AS evolucao, to_char(nt.data_1o_sintomas,'DD/MM/YYYY') AS data_1o_sintomas, to_char(nt.data_cura_obito,'DD/MM/YYYY') AS data_cura_obito, nt.co_seq_exame, nt.metodo AS cod_metodo, met.valor AS metodo, nt.exame AS cod_exame, exa.valor AS exame, nt.resultado AS cod_resultado, res.valor AS resultado, to_char(nt.data_coleta,'DD/MM/YYYY') AS data_coleta, to_char(nt.data_recebimento,'DD/MM/YYYY') AS data_recebimento, to_char(nt.data_liberacao,'DD/MM/YYYY') AS data_liberacao, nt.status_notificacao AS cod_status_notificacao, snt.valor as status_notificacao, nt.excluir_ficha, nt.origem AS cod_origem, ori.valor AS origem, nt.uf_unidade_notifica, nt.ibge_unidade_notifica, to_char(nt.data_notificacao,'DD/MM/YYYY') AS data_notificacao, to_char(nt.updated_at,'DD/MM/YYYY') AS updated_at FROM public.notificacao nt LEFT JOIN public.termo exa ON (exa.codigo::character varying = nt.exame::character varying AND exa.tipo = 'exame') LEFT JOIN public.termo ori ON (ori.codigo::character varying = nt.origem::character varying AND ori.tipo = 'origem') LEFT JOIN public.termo tpp ON (tpp.codigo::character varying = nt.tipo_paciente::character varying AND tpp.tipo = 'tipo_paciente') LEFT JOIN public.termo rc ON (rc.codigo::character varying = nt.raca_cor::character varying AND rc.tipo = 'raca_cor') LEFT JOIN public.termo res ON (res.codigo::character varying = nt.resultado::character varying AND res.tipo = 'resultado') LEFT JOIN public.termo met ON (met.codigo::character varying = nt.metodo::character varying AND met.tipo = 'metodo') LEFT JOIN public.termo ccl ON (ccl.codigo::character varying = nt.criterio_classificacao::character varying AND ccl.tipo = 'criterio_classificacao') LEFT JOIN public.termo clf ON (clf.codigo::character varying = nt.classificacao_final::character varying AND clf.tipo = 'classificacao_final') LEFT JOIN public.termo evo ON (evo.codigo::character varying = nt.evolucao::character varying AND evo.tipo = 'evolucao') LEFT JOIN public.termo snt ON (snt.codigo::character varying = nt.status_notificacao::character varying AND snt.tipo = 'status') LEFT JOIN public.etnia etn ON (etn.co_etnia::character varying = nt.etnia::character varying) WHERE {where} ORDER BY id ASC LIMIT {limit} OFFSET {offset}"

    with open(join(dirname(__root__),'metabase','exames.sql')) as file:
        sql = " ".join([ row.replace('\n',' ') for row in file.readlines() if not '--' in row ])
        sql = trim_overspace(f"{sql} WHERE {where} ORDER BY 1")

    print(f"Requesting {where}")

    query = {
        "database": 2,
        "type": "native",
        "native": {
            "query": sql
        }
    }

    query = json.dumps(query)

    res = requests.post("https://metabase.saude.pr.gov.br/api/dataset/csv",
                            headers = header,
                            data = {'query': query},
                            verify=False,
                            stream=True
                        )

    if res.status_code in [ 200, 202 ] :
        print(f"Success code {res.status_code }")
    else:
        print(f"Error code {res.status_code }")
        raise Exception()

    if not filename:
        _, params = cgi.parse_header(res.headers['Content-Disposition'])
        pathfile = join('input','queries_exames',params['filename'])
    else:
        pathfile = join('input','queries_exames',filename)

    with open(join(pathfile),'wb') as out:
        print(f'Saving in {pathfile}')
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                out.write(chunk)
                out.flush()


    try:
        print(f"Download finish, time elapsed: {res.elapsed}")
        print(f"downloaded shape {pd.read_csv(pathfile).shape}\n")
    except:
        print(f"download error")
        raise Exception()


    return pathfile
