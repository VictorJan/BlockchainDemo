from Utils.Additional import validate
from Utils.Signature import ECDSA
import json,datetime

class Transaction:
	
	__transactions=[]

	def __init__(self,ecdsa,store=True,**transaction):
		'''
		ecdsa user;
		transaction: :
		~validation~ raw = json of a transaction -> for validation
		~creation~ payload = {recipient=[name],amount=[value]} -> recipient's name must be on the keychain of passed ecdsa
		'''
		self.__value,self.__ecdsa=None,None
		if isinstance(ecdsa,ECDSA) and (transaction:=self.decode(r) if (r:=transaction.get('raw')) else ( (transaction:=validate(p,recipient={'type':str},amount={'type':int})) if (p:=transaction.get('payload',{})) else None)):
			self.__ecdsa=ecdsa
			self.__value=json.dumps(transaction) if r else (self.__export(**self.__ecdsa.sign(formated)) if (formated:=self.__format(**transaction)) else None)
			if not self in self and self.valid and store:
				self.__transactions.append(self)
	
	def __getattr__(self,attr):
		return json.loads(self.value).get(attr,None)

	def __eq__(self,other):
		return other.value==self.value if isinstance(other,Transaction) else False
	
	def __contains__(self,other):
		if isinstance(other,Transaction):
			for transaction in self.__transactions:
				if transaction==other:
					return True
		return False

	def __format(self,**data):
		'''
		Format the data for the transation -> validates the existance of the recipient.
		data:
			{
				datentime:
				sender:{
					name:
					public_key:
				}
				recipient:{
					name:
					public_key:
				}
				content:
			}
		'''
		if self.__ecdsa and data['recipient'] in self.__ecdsa.keychain:
			credentials_block=lambda user: {'name':user,'public_key':self.__ecdsa.keychain[user].coordinates}
			return json.dumps({
					'datentime':str(datetime.datetime.utcnow()),
					'sender':credentials_block(self.__ecdsa.keyring['owner']),
					'recipient':credentials_block(data['recipient']),
					'content':data['amount']
				})
		
		return None


	
	def __export(self,**incoming):
		'''
		Incoming : incoming: {data:[str_value],signature:[signature_value]}. Reconvert data value into a dictionary - because we have passed the jsonified dict  previously.
		Return:
		data:json.loads({...})
		signature:(...)
		'''
		return json.dumps({
			'data':json.loads(incoming['data']),
			'signature':incoming['signature']
			})
	
	@property
	def value(self):
		return self.__value


	@property
	def valid(self):
		#using raw : raw=self.__value
		#using payload : payload=dict(user=self.data['sender'],data=json.dumps(self.data),signature=tuple(self.signature))
		return self.__ecdsa.verify(raw=self.__value) if self.__ecdsa and self.__value else False

		
	@classmethod
	def index(cls,transaction):
		if isinstance(transaction,Transaction):
			for i,t in enumerate(cls.__transactions):
				if t.value==transaction.value:
					return i
		return None

	@classmethod
	def update_transactions(cls,*transaction):
		for t in iter(transaction):
			if isinstance(t,Transaction) and (index:=cls.index(t)) is not None:
				cls.__transactions.pop(index)
	

	@classmethod
	def get_transactions(cls,valid=False):
		return cls.__transactions if not valid else [t.valid for t in cls.__transactions]
		
	@staticmethod
	def decode(raw):
		try:
			mapped=json.loads(str(raw))
			return mapped if validate(mapped,data={'type':dict,'contains':['datentime','sender','recipient','content']},signature={'type':list}) \
			and validate(mapped['data'],sender={'type':dict,'contains':['name','public_key']},recipient={'type':dict,'contains':['name','public_key']}) else None
		except:
			return {}
	
	

