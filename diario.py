#!/usr/bin/env python
# coding: utf-8

from sys import argv
import pandas as pd
from datetime import datetime, timedelta

from bulletin.data.notifica import Notifica
from bulletin.data.casos_confirmados import CasosConfirmados

hoje = datetime.today()
ontem = hoje - timedelta(1)
anteontem = ontem - timedelta(1)

force = False
hard = False
if len(argv) == 2:
    if argv[1] == '--force':
        force = True
    elif argv[1] == '--hard':
        hard = True
elif len(argv) == 3:
    if (argv[1] == '--force' or argv[1] == '--hard') and (argv[2] == '--hard' or argv[2] == '--force'):
        force = True
        hard = True

notifica = Notifica(force=force, hard=hard)
notifica.shape()

casos_confirmados = CasosConfirmados(force=force, hard=hard)
casos_confirmados.shape()

notifica.filter_date(anteontem)

notifica_novos_casos = notifica.get_casos()

notifica_novos_obitos = notifica.get_obitos()

novos_casos = casos_confirmados.novos_casos(notifica_novos_casos)

novos_obitos = casos_confirmados.novos_obitos(novos_casos, notifica_novos_obitos)

casos_confirmados.relatorio(novos_casos, novos_obitos)
