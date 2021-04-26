#-----------------------------------------------------------------------------------------------------------------------------#
# Classe de tratamento de dados do Notifica Covid-19 Paraná
# Todos os direitos reservados ao autor
#-----------------------------------------------------------------------------------------------------------------------------#

from os.path import dirname, join, isfile, isdir
from datetime import datetime, date, timedelta
from unidecode import unidecode
from hashlib import sha256, md5
from os import error, makedirs, system
from time import sleep
import pandas as pd

from bulletin import __file__ as __root__
from bulletin.commom import static
from bulletin.commom.utils import isvaliddate
from bulletin.commom.normalize import normalize_text, normalize_number, normalize_hash
from bulletin.metabase.request import download_metabase

#----------------------------------------------------------------------------------------------------------------------
class Notifica:

    #----------------------------------------------------------------------------------------------------------------------
    def __init__(self, pathfile=''):
        self.__source = None
        self.pathfile = pathfile
        self.database = join(dirname(__root__),'resources','database','notifica.pkl')
        self.output = join('output')
        self.errorspath = join('output','errors',datetime.today().strftime('%Y'),datetime.today().strftime('%B').lower(),datetime.today().strftime('%d'))

        self.was_download = []

        if not isdir(self.errorspath):
            makedirs(self.errorspath)

        if not isdir(dirname(self.database)):
            makedirs(dirname(self.database))

    #----------------------------------------------------------------------------------------------------------------------
    def __len__(self):
        return len(self.__source)

    #----------------------------------------------------------------------------------------------------------------------
    def shape(self):
        return (len(self.__source),len(self.__source.loc[self.__source['evolucao'] == 1]),len(self.__source.loc[self.__source['evolucao'] == 2]),len(self.__source.loc[self.__source['evolucao'] == 3]),len(self.__source.loc[self.__source['evolucao'] == 4]))

    def download_todas_notificacoes(self):
        classificacao_final = ['0','1','2','3','5']

        download_metabase(filename='null.csv',where=f"classificacao_final IS NULL AND nt.metodo <> '' AND nt.metodo <> '3' AND nt.metodo IS NOT NULL AND nt.excluir_ficha = '2' AND nt.uf_residencia = '41' AND nt.uf_unidade_notifica = '41' AND (nt.status_notificacao = '1' OR nt.status_notificacao = '2')")
        for cf in classificacao_final:
            download_metabase(filename=f"{cf}.csv",where=f"classificacao_final = {cf} AND nt.metodo <> '' AND nt.metodo <> '3' AND nt.metodo IS NOT NULL AND nt.excluir_ficha = '2' AND nt.uf_residencia = '41' AND nt.uf_unidade_notifica = '41' AND (nt.status_notificacao = '1' OR nt.status_notificacao = '2')")



    #----------------------------------------------------------------------------------------------------------------------
    def read_todas_notificacoes(self):
        classificacao_final = ['0','1','2','3','5']

        self.read(join('input','queries_exames','null.csv'))
        for cf in classificacao_final:
            self.read(join('input','queries_exames',f"{cf}.csv"), append=True)

        self.save()

    #----------------------------------------------------------------------------------------------------------------------
    def read(self,pathfile,save=True,append=False):
        notifica = pd.read_csv(pathfile,
                           parse_dates = ['data_notificacao'],
                           date_parser = lambda x: pd.to_datetime(x, errors='coerce', format='%d/%m/%Y')
                        )

        #notifica = self.__normalize(notifica)

        if save:
            if isinstance(self.__source, pd.DataFrame) and append:
                self.__source = self.__source.append(notifica, ignore_index=True)
            else:
                self.__source = notifica

        return notifica

    #----------------------------------------------------------------------------------------------------------------------
    def load(self):
        try:
            self.__source = pd.read_pickle(self.database)
        except:
            raise Exception(f"Arquivo {self.database} não encontrado")

    #----------------------------------------------------------------------------------------------------------------------
    def save(self, df=None):
        if isinstance(df, pd.DataFrame) and len(df) > 0:
            new_df = df
            self.__source = new_df
        elif isinstance(self.__source, pd.DataFrame) and len(self.__source) > 0:
            new_df = self.__source
        else:
            raise Exception('Não é possível salvar um DataFrame inexistente, realize a leitura antes ou passe como para esse método')

        new_df.to_pickle(self.database)

    #----------------------------------------------------------------------------------------------------------------------
    # Normaliza strings, datas e códigos. Anula valores incorretos.
    def __normalize(self, notifica):
        if not (isinstance(notifica, pd.DataFrame) and len(notifica) > 0):
            raise Exception(f"Dataframe: {notifica} vazio")

        print('normalize notifica')

        #Anula datas invalidas
        mask = notifica['data_nascimento'].apply(lambda x: isvaliddate(x, begin=date(1800,1,1)))
        notifica.loc[~mask, 'data_nascimento'] = pd.NaT
        mask = notifica['data_1o_sintomas'].apply(isvaliddate)
        notifica.loc[~mask, 'data_1o_sintomas'] = pd.NaT
        mask = notifica['data_cura_obito'].apply(isvaliddate)
        notifica.loc[~mask, 'data_cura_obito'] = pd.NaT
        mask = notifica['data_coleta'].apply(isvaliddate)
        notifica.loc[~mask, 'data_coleta'] = pd.NaT
        mask = notifica['data_recebimento'].apply(isvaliddate)
        notifica.loc[~mask, 'data_recebimento'] = pd.NaT
        mask = notifica['data_liberacao'].apply(isvaliddate)
        notifica.loc[~mask, 'data_liberacao'] = pd.NaT
        mask = notifica['data_notificacao'].apply(isvaliddate)
        notifica.loc[~mask, 'data_notificacao'] = pd.NaT
        mask = notifica['updated_at'].apply(isvaliddate)
        notifica.loc[~mask, 'updated_at'] = pd.NaT

        #Seleciona melhor data de diagnóstico dentre as datas validas na ordem de prioridade: data_coleta -> data_recebimento -> data_liberacao -> data_notificacao
        notifica['data_diagnostico'] = notifica['data_notificacao']
        notifica.loc[notifica['data_liberacao'].notnull(), 'data_diagnostico'] = notifica.loc[notifica['data_liberacao'].notnull(), 'data_liberacao']
        # notifica.loc[notifica['data_recebimento'].notnull(), 'data_diagnostico'] = notifica.loc[notifica['data_recebimento'].notnull(), 'data_recebimento']
        # notifica.loc[notifica['data_coleta'].notnull(), 'data_diagnostico'] = notifica.loc[notifica['data_coleta'].notnull(), 'data_coleta']

        #Calcula a idade com base na data de notificação
        notifica.loc[(notifica['data_nascimento'].notnull()) & (notifica['data_notificacao'].notnull()),'idade'] = notifica.loc[(notifica['data_nascimento'].notnull()) & (notifica['data_notificacao'].notnull())].apply(lambda row: row['data_notificacao'].year - row['data_nascimento'].year - ((row['data_notificacao'].month, row['data_notificacao'].day) < (row['data_nascimento'].month, row['data_nascimento'].day)), axis=1)
        notifica.loc[notifica['data_nascimento'].isnull(),'idade'] = -99
        notifica['idade'] = notifica['idade'].apply(lambda x: normalize_number(x, fill=-99))

        #Atribui código 99/999999 ou valores correspondentes à coluna nos campos não especificados ou nulos
        notifica.loc[notifica['uf_residencia'] == 0,'uf_residencia'] = 99
        notifica.loc[notifica['ibge_residencia'] == 0,'ibge_residencia'] = 999999
        notifica.loc[notifica['uf_unidade_notifica'] == 0,'uf_unidade_notifica'] = 99
        notifica.loc[notifica['ibge_unidade_notifica'] == 0,'ibge_unidade_notifica'] = 999999


        #Copia lista de municipios, deixa o nome do municipio normalizado e altera nome das colunas
        municipios = static.municipios[['ibge','municipio','uf']].copy()
        municipios['municipio'] = municipios['municipio'].apply(normalize_text)
        municipios = municipios.rename(columns={'ibge':'ibge_residencia','municipio':'mun_resid','uf':'uf_resid'})

        #Copia lista de regionais e altera nome das colunas
        regionais = static.regionais[['ibge','nu_reg']].copy()
        regionais = regionais.rename(columns={'ibge':'ibge_residencia','nu_reg':'rs'})

        #Relaciona ibge de residencia das notificacoes com a lista de municipios e regionais
        notifica = pd.merge(left=notifica, right=municipios, how='left', on='ibge_residencia')
        notifica = pd.merge(left=notifica, right=regionais, how='left', on='ibge_residencia')

        #Altera nome das colunas da lista de municipios
        municipios = municipios.rename(columns={'ibge_residencia':'ibge_unidade_notifica','mun_resid':'mun_atend','uf_resid':'uf_atend'})

        #Relaciona ibge de atendimento das notificacoes com a lista de municipios e regionais
        notifica = pd.merge(left=notifica, right=municipios, how='left', on='ibge_unidade_notifica')

        #Atribui código 99 na coluna de regionais nos casos de fora
        notifica['rs'] = notifica['rs'].apply(lambda x: normalize_number(x,fill='99'))
        notifica['rs'] = notifica['rs'].apply(lambda x: str(x).zfill(2))

        #Conjunto de negações encontradas na coluna nome_mae
        nao = set(['NAO','CONSTA','INFO','INFORMADO','CONTEM',''])
        #Anula campo com alguma negação na coluna nome_mae
        notifica.loc[ [True if set(nome_mae.split(" ")).intersection(nao) else False for nome_mae in notifica['nome_mae'] ], 'nome_mae'] = None

        #Exporta notificações erradas
        notificacoes_sem_sexo = notifica.loc[(notifica['classificacao_final']==2) & (notifica['sexo'].isnull())]
        notificacoes_sem_sexo.to_excel(join(self.errorspath,'notificacoes_sem_sexo.xlsx')) if len(notificacoes_sem_sexo) > 0 else True

        notificacoes_sem_mun_resid = notifica.loc[(notifica['classificacao_final']==2) & (notifica['mun_resid'].isnull())]
        notificacoes_sem_mun_resid.to_excel(join(self.errorspath,'notificacoes_sem_mun_resid.xlsx')) if len(notificacoes_sem_mun_resid) > 0 else True

        notificacoes_sem_mun_atend = notifica.loc[(notifica['classificacao_final']==2) & (notifica['mun_atend'].isnull())]
        notificacoes_sem_mun_atend.to_excel(join(self.errorspath,'notificacoes_sem_mun_atend.xlsx'))

        notificacoes_sem_nome_mae = notifica.loc[(notifica['classificacao_final']==2) & (notifica['nome_mae'].isnull())]
        notificacoes_sem_nome_mae.to_excel(join(self.errorspath,'notificacoes_sem_nome_mae.xlsx')) if len(notificacoes_sem_nome_mae) > 0 else True

        notificacoes_sem_data_nascimento = notifica.loc[(notifica['classificacao_final']==2) & (notifica['data_nascimento']==pd.NaT)]
        notificacoes_sem_data_nascimento.to_excel(join(self.errorspath,'notificacoes_sem_data_nascimento.xlsx')) if len(notificacoes_sem_data_nascimento) > 0 else True

        notificacoes_sem_data_diagnostico = notifica.loc[(notifica['classificacao_final']==2) & (notifica['data_diagnostico']==pd.NaT)]
        notificacoes_sem_data_diagnostico.to_excel(join(self.errorspath,'notificacoes_sem_data_diagnostico.xlsx')) if len(notificacoes_sem_data_diagnostico) > 0 else True

        notificacoes_sem_data_cura_obito = notifica.loc[(notifica['classificacao_final']==2) & (notifica['evolucao']!=3) & (notifica['data_cura_obito']==pd.NaT)]
        notificacoes_sem_data_cura_obito.to_excel(join(self.errorspath,'notificacoes_sem_data_cura_obito.xlsx')) if len(notificacoes_sem_data_cura_obito) > 0 else True

        #Remove notificações erradas
        notifica = notifica.drop(index=set(notificacoes_sem_sexo.index.tolist() + notificacoes_sem_mun_resid.index.tolist() + notificacoes_sem_data_nascimento.index.tolist() + notificacoes_sem_data_diagnostico.index.tolist() + notificacoes_sem_data_cura_obito.index.tolist()))

        parser = lambda x: x #md5(str.encode(x)).hexdigest() if (x != None) else None

        #Gera hashes para identificar as notificacoes caso o campo da coluna necessaria nao for nulo
        notifica.loc[notifica['mun_resid'].notnull() & (notifica['idade']!=-99), 'hash_resid'] = notifica.loc[notifica['mun_resid'].notnull()].apply(lambda row: parser(normalize_hash(row['paciente'])+str(row['idade'])+normalize_hash(row['mun_resid'])), axis=1)
        notifica.loc[notifica['mun_atend'].notnull() & (notifica['idade']!=-99), 'hash_atend'] = notifica.loc[notifica['mun_atend'].notnull()].apply(lambda row: parser(normalize_hash(row['paciente'])+str(row['idade'])+normalize_hash(row['mun_atend'])), axis=1)
        notifica.loc[ notifica['nome_mae'].notnull(), 'hash_mae'] = notifica.loc[ notifica['nome_mae'].notnull() ].apply(lambda row: parser(normalize_hash(row['paciente'])+normalize_hash(row['nome_mae'])), axis=1)
#         notifica.loc[ notifica['cpf'].notnull(), 'hash_cpf'] = notifica.loc[ notifica['cpf'].notnull() ].apply(lambda row: parser((row['cpf'])), axis=1)
#         notifica.loc[notifica['data_nascimento']!=pd.NaT, 'hash_nasc'] = notifica.loc[notifica['data_nascimento']!=pd.NaT].apply(lambda row: parser(normalize_hash(row['paciente'])+date_hash(row['data_nascimento'])), axis=1)
#         notifica['hash_diag'] = notifica.apply(lambda row: normalize_hash(row['paciente'])+date_hash(row['data_diagnostico']), axis=1)

        #Gera hash para identificar alterações nos id das fichas
        # notifica['checksum'] = notifica.apply(
        #     lambda row:
        #         sha256(
        #             str.encode(
        #                 normalize_hash(row['paciente']) + normalize_hash(row['mun_resid']) + 
        #                 normalize_hash(row['evolucao'])
        #             )
        #         ).hexdigest()
        #     ,axis = 1
        # )

        return notifica

    #----------------------------------------------------------------------------------------------------------------------
    def verify_changes(self, comunicados):
        query = ", ".join(str(id) for id in comunicados['id'])
        print(f"Download {len(comunicados['id'])} notificações para buscar alterações")
        downloaded = self.read(download_metabase(filename='alteracoes.csv',where=f"classificacao_final == 2 AND id NOT IN ({query})"),save=False)
        old_and_new = pd.merge(comunicados[['id','checksum']], downloaded[['id','checksum']], on='id', how='left', sulffixes=['_old','_new'])
        changed = old_and_new.loc[old_and_new['checksum_old']!=old_and_new['checksum_new']]
        changes = pd.merge(comunicados.loc[comunicados['id'].isin(changed['id']),['id','paciente','mun_resid','evolucao']],downloaded.loc[downloaded['id'].isin(changed['id']),['id','paciente','mun_resid','evolucao']])
        print(f"Foram encontrados {len(changes)} diferenças")
        changes.to_excel(join(output,f"mudancas_{datetime.today().strftime('%d_%m')}"))
        return changes

    #----------------------------------------------------------------------------------------------------------------------
    def download_news(self, comunicados):
        query = ", ".join(str(id) for id in comunicados['id'])
        novos = self.read(download_metabase(filename='novos.csv',where=f"classificacao_final == 2 AND id NOT IN ({query})"),save=False)
        return novos

    #----------------------------------------------------------------------------------------------------------------------
    def get_casos(self):
        return self.__source.copy()

    #----------------------------------------------------------------------------------------------------------------------
    def get_obitos(self):
        return self.__source.loc[self.__source['evolucao'] == 2].copy()

    #----------------------------------------------------------------------------------------------------------------------
    def get_recuperados(self):
        return self.__source.loc[self.__source['evolucao'] == 1].copy()

    #----------------------------------------------------------------------------------------------------------------------
    def get_casos_ativos(self):
        return self.__source.loc[self.__source['evolucao'] == 3].copy()

    #----------------------------------------------------------------------------------------------------------------------
    def get_obitos_nao_covid(self):
        return self.__source.loc[self.__source['evolucao'] == 4].copy()
