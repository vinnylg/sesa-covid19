#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from os.path import join
from datetime import datetime, timedelta
from bulletin.data.casos_confirmados import CasosConfirmados


from bulletin.data.notifica import Notifica
from bulletin.data.casos_confirmados import CasosConfirmados

novos_casos = pd.read_excel(join('output','novos_casos.xlsx'),dtype={'idade':int, 'rs':str})

novos_obitos = pd.read_excel(join('output','novos_obitos.xlsx'),dtype={'idade':int, 'rs':str})
force=True
hard=True
CasosConfirmados().relatorio(novos_casos, novos_obitos)