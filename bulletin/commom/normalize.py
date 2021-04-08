import datetime
import numpy as np
import pandas as pd
from unidecode import unidecode as unidecode

from sys import exit
from bulletin.commom import static

def trim_overspace(text):
	parts = filter(lambda x: len(x) > 0,text.split(" "))
	return " ".join(parts)

def normalize_cpf(cpf):
	cpf = ''.join(filter(lambda x: x >= '0' and x <= '9', str(cpf)))
	cpf = str(cpf).zfill(11)
	digitos = list(map(int,cpf))

	if max(digitos) == min(digitos):
		return None

	validacao = sum(np.array(digitos[:9]) * np.array([10,9,8,7,6,5,4,3,2])) * 10 % 11

	if validacao != digitos[-2]:
		return None

	return cpf[:3] + '.' + cpf[3:6] + '.' + cpf[6:9] + '-' + cpf[9:]

def normalize_hash(text):
	return "".join(filter(lambda x: x not in [' ','\n','\t','0','\\','/'], str(text).upper()))

def data_hash(text):
	return "".join(filter(lambda x: x >= '0' and x <= '9', str(text).upper()))

def normalize_text(text):
	if text == None:
		return None

	x = str(text).replace(".","").replace("\n","").replace(",","").replace("\t","").replace("''","'").replace("\"","'").upper()
	x = trim_overspace(x)
	x = unidecode(x)

	return x

def normalize_labels(text):
	x = str(text).replace("'"," ").replace(".","").replace("\n","").replace(",","").lower()
	x = trim_overspace(x).replace(" ","_")
	x = unidecode(x)

	return x

def normalize_number(num,cast=int,error='fill',fill='-1'):
	try:
		return cast(num)
	except ValueError:
		if error == 'raise':
			raise Exception(ValueError)
		elif error == 'fill':
			return normalize_number(fill,cast,'raise')

def normalize_municipios(mun):
	mun = normalize_text(mun)
	est = 'PR'

	if '-' in mun or '/' in mun:
		mun = mun.split('-')[-1]

		if '/' in mun:
			mun, est = mun.split('/')
			est = trim_overspace(est)
		else:
			municipios = static.municipios_sesa_ibge.loc[static.municipios_sesa_ibge['uf']!='PR']
			municipios['municipio_sesa'] = municipios['municipio_sesa'].apply(lambda x: normalize_hash(normalize_text(x)))
			municipios['municipio_ibge'] = municipios['municipio_ibge'].apply(lambda x: normalize_hash(normalize_text(x)))

			municipio = municipios.loc[municipios['municipio_sesa']==normalize_hash(mun)]
			if len(municipio) == 0:
				municipio = municipios.loc[municipios['municipio_ibge']==normalize_hash(mun)]

			if len(municipio) != 0:
				est = municipio.iloc[0]['uf']

	mun = trim_overspace(mun)

	return (mun,est)

def normalize_ibge(ibge):
	ibge = str(ibge)
	if ibge:
		ibge = ibge[:len(ibge)-1]

	return int(ibge)

# def normalize_date(date):
# 	try:
# 		date = normalize_text(date)
# 		date = date.split(' ')[0]

# 		if '-' in date:
# 			date = date.split('-')
# 		elif '/' in date:
# 			date = date.split('/')
# 		else:
# 			return pd.NaT

# 		if len(date) != 3:
# 			return pd.NaT

# 		if len(date[0]) == 4:
# 			year, month, day = tuple(map(int,date))
# 		elif len(date[2]) == 4:
# 			day, month, year = tuple(map(int,date))
# 		else:
# 			return pd.NaT

# 		begin = datetime.date('2020','03','1')
# 		date = datetime.date(year, month, day)
# 		today = datetime.date.today()

# 		if date > today or date < begin:
# 			date = pd.NaT

# 		return date
# 	except:
# 		return pd.NaT