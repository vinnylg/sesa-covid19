import datetime
from unidecode import unidecode as unidecode

from sys import exit
from bulletin.commom.static import municipios

def trim_overspace(text):
	parts = filter(lambda x: len(x) > 0,text.split(" "))
	return " ".join(parts)

def normalize_hash(text):
	return "".join(filter(lambda x: x >= 'A' and x <= 'Z', str(text).upper()))

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
			municipios = municipios.loc[municipios['uf']!='PR']
			municipios['municipio_sesa'] = municipios['municipio_sesa'].apply(lambda x: normalize_hash(normalize_text(x)))
			municipios['municipio_ibge'] = municipios['municipio_ibge'].apply(lambda x: normalize_hash(normalize_text(x)))

			municipio = municipios.loc[municipios['municipio_sesa']==normalize_hash(mun)]
			if len(municipio) == 0:
				municipio = municipios.loc[municipios['municipio_ibge']==normalize_hash(mun)]

			if len(municipio) != 0:
				est = municipio.iloc[0]['uf']

	mun = trim_overspace(mun)

	return (mun,est)

def normalize_igbe(ibge):
	if ibge:
		ibge = ibge[:len(ibge)-1]

	return ibge
