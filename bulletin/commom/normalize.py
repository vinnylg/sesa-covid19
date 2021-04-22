import datetime
from unidecode import unidecode as unidecode

def normalize_hash(text):
	return "".join(filter(lambda x: x >= 'A' and x <= 'Z', str(text).upper()))

def trim_overspace(text):
	parts = filter(lambda x: len(x) > 0,text.split(" "))
	return " ".join(parts)

def normalize_text(text):
    #.replace("'"," ") alguns municipios tem ' e as macros maravilhosas do excel vão falhar
	x = str(text).replace(".","").replace("\n","").replace(",","").replace("\t","").replace("''","'").replace("\"","'").upper()
	x = trim_overspace(x)
	x = unidecode(x)

	if x == 'nan' or len(x) == 0 or x == '0' or x == 'nao_informado':
		return ''
	else:
		return x

def normalize_labels(text):
	x = str(text).replace("'"," ").replace(".","").replace("\n","").replace(",","").lower()
	x = trim_overspace(x).replace(" ","_")
	x = unidecode(x)

	if x == 'nan' or len(x) == 0 or x == '0' or x == 'nao_informado':
		return ''
	else:
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
	if '-' in mun:
		mun = mun.split('-')[-1]
	if '/' in mun:
		mun = mun.split('/')[0]

	mun = trim_overspace(mun)
	return mun

def normalize_igbe(ibge):
	ibge = normalize_number(ibge)
	if ibge != -1:
		try:
			ibge = str(ibge)
			ibge = ibge[:len(ibge)-1]
			ibge = int(ibge)
		except ValueError:
			return -1

	return ibge
