#-----------------------------------------------------------------------------------------------------------------------------#
# Classe de tratamento de dados do SIM Paraná
# Todos os direitos reservados ao autor
#-----------------------------------------------------------------------------------------------------------------------------#

from os.path import dirname, join, isdir
from datetime import datetime
from os import makedirs
import pandas as pd
import numpy as np
from simpledbf import Dbf5
from bulletin import __file__ as __root__
from bulletin.commom import static

class sim:
    
    def __init__(self, pathfile=''):
        self.__source = None
        self.pathfile = pathfile
        self.database = join(dirname(__root__),'resources','database','sim.pkl')
        self.errorspath = join('output','errors','sim',datetime.today().strftime('%B_%Y'))

        if not isdir(self.errorspath):
            makedirs(self.errorspath)

        if not isdir(dirname(self.database)):
            makedirs(dirname(self.database))

    def __len__(self):
        return len(self.__source)

    def read(self,pathfile, append=False):
        obitos = Dbf5(pathfile, codec = 'cp860').to_dataframe()

        if isinstance(self.__source, pd.DataFrame) and append:
            self.__source = self.__source.append(obitos, ignore_index=True)
        else:
            self.__source = obitos
    
    def read_all_database_files(self):
        last_digit = ['0', '1']

        for x in last_digit:
            self.read(join('input','dbf',f"DOPR202{x}.dbf"), append=True)

    def load(self):
        try:
            self.__source = pd.read_pickle(self.database)
        except:
            raise Exception(f"Arquivo {self.database} não encontrado")

    def save(self, df=None):
        if isinstance(df, pd.DataFrame) and len(df) > 0:
            new_df = df
            self.__source = new_df
        elif isinstance(self.__source, pd.DataFrame) and len(self.__source) > 0:
            new_df = self.__source
        else:
            raise Exception('Não é possível salvar um DataFrame inexistente, realize a leitura antes ou passe como para esse método')

        new_df.to_pickle(self.database)

    def to_notifica(self):
        self.__source = self.__source[['NUMERODO', 'NUMERODV', 'DTOBITO', 'NUMSUS', 'NOME', 'NOMEMAE', 'DTNASC',
                    'IDADE', 'SEXO', 'RACACOR', 'OCUP', 'CODESTRES', 'CODMUNRES', 'BAIRES',
                    'ENDRES', 'NUMRES', 'CEPRES', 'CODESTOCOR', 'CODMUNOCOR', 'LINHAA', 'LINHAB',
                    'LINHAC', 'LINHAD', 'LINHAII', 'CAUSABAS']]

        self.__source = self.__source.rename(
            columns={
                'DTOBITO': 'data_cura_obito',
                'NUMSUS': 'cns',
                'NOME': 'paciente',
                'NOMEMAE': 'nome_mae',
                'DTNASC': 'data_nascimento',
                'IDADE': 'idade',
                'SEXO': 'sexo',
                'RACACOR': 'raca_cor',
                'OCUP': 'cod_cbo',
                'CODESTRES': 'uf_residencia',
                'CODMUNRES': 'ibge_residencia',
                'BAIRES': 'bairro_residencia',
                'ENDRES': 'logradouro_residencia',
                'NUMRES': 'numero_residencia',
                'CEPRES': 'cep_residencia',
                'CODESTOCOR': 'uf_unidade_notifica',
                'CODMUNOCOR': 'ibge_unidade_notifica'
            })

        self.__source.loc[self.__source['raca_cor'] == '3', 'raca_cor'] = '-1'
        self.__source.loc[self.__source['raca_cor'] == '4', 'raca_cor'] = '3'
        self.__source.loc[self.__source['raca_cor'] == '-1', 'raca_cor'] = '4'
        self.__source.loc[self.__source['raca_cor'].isnull(), 'raca_cor'] = '99'

        self.__source["data_cura_obito"] = self.__source["data_cura_obito"].apply(lambda x: pd.to_datetime(x, format='%d%m%Y'))
        self.__source["data_nascimento"] = self.__source["data_nascimento"].apply(lambda x: pd.to_datetime(x, format='%d%m%Y'))

        self.__source['idade'] = pd.to_numeric(self.__source['idade'], downcast = 'integer')
        self.__source['idade'] = self.__source['idade'].apply(lambda x: np.subtract(x, 400))
        self.__source.loc[self.__source['idade'] < 1, 'idade'] = 0
        self.__source.loc[self.__source['idade'] == 599, 'idade'] = None

        self.__source.loc[self.__source['nome_mae'].isnull(), 'nome_mae'] = ''
        nao = set(['NAO','CONSTA','INFO','INFORMADO','CONTEM',''])
        self.__source.loc[ [True if set(nome_mae.split(" ")).intersection(nao) else False for nome_mae in self.__source['nome_mae'] ], 'nome_mae'] = None

        #self.__source.loc[self.__source['cns'].isnull(), 'cns'] = '0'
        #self.__source.loc[self.__source['cod_cbo'].isnull(), 'cod_cbo'] = '0'
        #self.__source.loc[self.__source['numero_residencia'].isnull(), 'numero_residencia'] = '0'
        #self.__source.loc[self.__source['cep_residencia'].isnull(), 'cep_residencia'] = '0'

        self.__source['id'] = self.__source['NUMERODO'].str.cat(self.__source['NUMERODV'])

        self.__source.loc[self.__source['LINHAA'].isnull(), 'LINHAA'] = ''
        self.__source.loc[self.__source['LINHAB'].isnull(), 'LINHAB'] = ''
        self.__source.loc[self.__source['LINHAC'].isnull(), 'LINHAC'] = ''
        self.__source.loc[self.__source['LINHAD'].isnull(), 'LINHAD'] = ''
        self.__source.loc[self.__source['LINHAII'].isnull(), 'LINHAII'] = ''
        self.__source.loc[self.__source['CAUSABAS'].isnull(), 'CAUSABAS'] = ''
        self.__source.loc[((self.__source['LINHAB'].apply(lambda x: 'B342' in x)) | (self.__source['LINHAC'].apply(lambda x: 'B342' in x)) |
                (self.__source['LINHAD'].apply(lambda x: 'B342' in x)) | (self.__source['LINHAII'].apply(lambda x: 'B342' in x)) |
                (self.__source['CAUSABAS'].apply(lambda x: 'B342' in x))), 'evolucao'] = '2'
        self.__source.loc[self.__source['evolucao'] != '2', 'evolucao'] = '4'

        self.__source = self.__source[['id', 'data_cura_obito', 'cns', 'paciente', 'nome_mae', 'data_nascimento', 'idade', 'sexo',
                    'raca_cor', 'cod_cbo', 'uf_residencia', 'ibge_residencia', 'bairro_residencia', 'logradouro_residencia',
                    'cep_residencia', 'uf_unidade_notifica', 'ibge_unidade_notifica', 'evolucao']]

        self.__source['numero_do'] = self.__source['id']   
        #self.__source.loc[self.__source['numero_do'].isnull(), 'numero_do'] = '0'
        #self.__source['numero_do'] = self.__source['numero_do'].astype('str')
        self.__source['sistema'] = 'SIM'

    #Métodos usados após to_notifica()
    
    def shape(self):
        return (len(self.__source.loc[self.__source['evolucao'] == '2']),
                len(self.__source.loc[self.__source['evolucao'] == '4']))

    def get_obitos(self):
        return self.__source.loc[self.__source['evolucao'] == '2'].copy()

    def get_obitos_nao_covid(self):
        return self.__source.loc[self.__source['evolucao'] == '4'].copy()

