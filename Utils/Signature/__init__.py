import random,json,datetime
from hashlib import sha256
from Crypto.Util.number import bytes_to_long
from Utils.EllipticCurve import Curve,Point
from Utils.Additional import linear_congruence,validate


class ECDSA:

	
	def __init__(self,unique_name,curve):
		self.__curve=self.__accept(curve)
		self.__keyring={'owner':unique_name,**self.__set_up_initial()}
		self.__keychain={unique_name:self.__keyring['public_key']}

		
	def __accept(self,curve):
		if isinstance(curve,Curve):
			return curve
		raise TypeError

	def __set_up_initial(self):
		private=random.randint(2,self.curve.order-1)
		public=private*self.curve.g
		return {'private_key':private,'public_key':public}

	def sign(self,data):
		'''
		Signing accpets data ,type of str.
		Return a dictionary of singed data - data and a signature - a (r,s) tuple:
		'''
		k=random.randint(2,self.curve.order-1)
		try:
			z=bytes_to_long(sha256(str(data).encode()).digest())
		except:
			raise Exception('Datatype of data must be convertable to a string.')

		compute_r=lambda k,g,order: ((k*g).x)%order
		compute_s=lambda k,z,r,private,order: (linear_congruence(k,1,order)*( (z%order) + r*private))%order

		while (r:=compute_r(k,self.curve.g,self.curve.order))==0 or (s:=compute_s(k,z,r,self.__keyring['private_key'],self.curve.order))==0:
			k=random.randint(2,self.curve.order-1)
		
		return {'data':str(data),'signature':(r,s)}

	def verify(self,**data):
		'''
		You may only verify the data, if the sender uses the same domain parameters, in the Blockchain.

		data:{
		raw:json data+signature
		payload: {user:[{unique_name,public_key}],data:[data , that's singed],signature:[a signature tuple]}
		}
		'''
		if (payload:=self.decode(r) if (r:=data.get('raw')) else (payload:=validate(p,user={'type':dict,'contains':['name','public_key']},data={'type':str},signature={'type':tuple}) if (p:=data.get('payload')) else None)):
			
			payload = {'user':payload['data']['sender'],'data':json.dumps(payload['data']),'signature':tuple(payload['signature'])} if 'raw' in data else payload 
			
			self.add(user=payload['user']['name'],public_key=payload['user']['public_key'])
			
			if (public_key:=self.__keychain.get(payload['user']['name'],None)):

				z=bytes_to_long(sha256(str(payload['data']).encode()).digest())

				compute_multiplier=lambda s,value,order: (inverse_s*value)%order if (inverse_s:=linear_congruence(s,1,order)) else None

				u=compute_multiplier(payload['signature'][1],z,self.__curve.order)
				v=compute_multiplier(payload['signature'][1],payload['signature'][0],self.__curve.order)
				return (payload['signature'][0]==(((u*self.__curve.g)+(v*public_key)).x)%self.__curve.order) if u is not None and v is not None else False
		
		return False
	
	def __export(self,data,signature):
		'''
		data:
		signature:
		'''
		return json.dumps({
			'data':data,
			'signature':signature
			})
	

	def add(self,**payload):
		'''
		payload : user=str,public_key
		'''
		if (payload:=validate(payload,user={'type':str},public_key={})) and payload['user'] not in self.__keychain:
			point=Point(self.curve)
			point.coordinates=tuple(payload['public_key'])
			if point.coordinates:
				self.__keychain[payload['user']]=point
				return True
		return None

	@staticmethod
	def decode(raw):
		'''
		At the signature state decoding should validate existance of data:sender:{name,public_kye}; signature:[r,s].
		'''
		try:
			mapped=json.loads(str(raw))
			return mapped if validate(mapped,data={'type':dict,'contains':['sender']},signature={'type':list}) and validate(mapped['data'],sender={'type':dict,'contains':['name','public_key']}) else None
		except:
			return {}
	
	@property
	def curve(self):
		return self.__curve

	@property
	def keychain(self):
		return self.__keychain
	@property
	def keyring(self):
		return self.__keyring
	
	
	