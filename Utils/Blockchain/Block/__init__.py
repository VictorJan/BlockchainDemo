from Utils.Additional import validate
from Utils.Signature import ECDSA
from Utils.Blockchain.Transaction import Transaction
from hashlib import sha256
import json

class Block:
	__zeros=5
	def __init__(self,ecdsa,**block):
		'''
		ecdsa user;
		block: :
		raw = json of a block -> for validation
		payload = {previous=[previous hash],transactions=[t1,t2,...]} 
		'''
		self.__value,self.__ecdsa=None,None
		if isinstance(ecdsa,ECDSA) and (block:=self.decode(r) if (r:=block.get('raw')) else ( (block:=validate(p,previous={'type':str},transactions={'type':tuple})) if (p:=block.get('payload',{})) else None)):
			self.__ecdsa=ecdsa
			self.__value=json.dumps(block if r else self.__mine(**block),indent=2)

	def __getattr__(self,attr):
		return json.loads(self.value).get(attr,None)

	def __contains__(self,transaction):
		if isinstance(transaction,Transaction):
			for each in self.transactions:
				if each.value==transaction.value:
					return True
		return False

	def __mine(self,**payload):
		'''
		payload: previous:[value]; transactions:[...]
		'''
		if (scope:=self.__create(**payload)):
			while bin(int( (proof:=sha256(json.dumps(scope['data']).encode() )).hexdigest() ,16))[2:].zfill(256)[:self.__zeros]!='0'*self.__zeros:
				scope['data']['nonce']+=1
			scope['proof']=proof.hexdigest()
			return scope
		return None

	def __create(self,**payload):
		'''
		payload: previous:[value]; transactions:[...]
		'''
		scope={
			'previous':payload['previous'],
			'data':{
				'transactions':{},
				'nonce':0
				}
			}

		for index,transaction in enumerate(payload['transactions']):
			if isinstance(transaction,Transaction):
				scope['data']['transactions'][index+1]=json.loads(transaction.value)
			else:
				return {}
		return scope if payload['transactions'] else {}


	@property
	def value(self):
		return self.__value

	@property
	def transactions(self):
		return tuple(Transaction(self.__ecdsa,False,raw=json.dumps(self.data['transactions'][transaction])) for transaction in self.data['transactions'] )

	@property
	def valid(self):
		if self.__value and self.__ecdsa:
			mapped=json.loads(self.__value)
			if sha256(json.dumps(mapped['data']).encode()).hexdigest()==mapped['proof']:
				for transaction_id in mapped['data']['transactions']:
					if not (running:=Transaction(self.__ecdsa,False,raw=json.dumps(mapped['data']['transactions'][transaction_id]))).valid:
						return False
				return True

		return False

	@staticmethod
	def decode(raw):
		try:
			mapped=json.loads(raw)
			return mapped if validate(mapped,previous={'type':str},data={'type':dict,'contains':['transactions','nonce']},proof={'type':str}) else None
		except:
			return {}