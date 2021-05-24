def binary_exp(a,p,m):
	z=1
	for i in bin(p)[2:]:
		z=(z**2 * a**int(i,2))%m
	return z

def linear_congruence(a,b,m):
	from math import gcd
	if gcd(a,m)==1:
		from sympy import totient
		return (binary_exp(a,totient(m)-1,m)*b)%m
	return None

def validate(input_data,**template):
	'''
	input_data - input dictionary
	template : key : {
		type:[int,str,...] -> isintance
		contains: getattr(__contains__)()
	}
	'''
	for key in template:
		if key in input_data:
			for requirement in template[key]:
				try:
					if requirement=="type" and not isinstance(input_data[key],template[key][requirement]):
						return None
					if requirement=="contains" and not \
					( (len(tuple(filter(lambda r: contains(r),template[key][requirement])))==len(template[key][requirement]) if getattr(template[key][requirement],'__iter__',None) else contains(template[key][requirement])) \
						if (contains:=getattr(input_data[key],f'__{requirement}__',None)) else True ):
						return None
				except:
					return None
		else:
			return None
	return input_data
	