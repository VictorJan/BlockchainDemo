from Utils.Additional import validate
from Utils.Signature import ECDSA
from Utils.Blockchain.Transaction import Transaction
from Utils.Blockchain.Block import Block
import json

class Chain:
	def __init__(self,block=None):
		if isinstance(block,Block) and block.previous=='' and block.valid:
			self.__blocks=[block]
		else:
			self.__blocks=[]

	def __contains__(self,block):
		'''
		Block, it's transactions in each block and the proof with the previous.
		'''
		if isinstance(block,Block):
			for transaction in self.transactions:
				if transaction in block:
					return True
			for each in self.__blocks:
				if each.proof==block.proof or each.previous==block.previous:
					return True
		return False
	
	def accept(self,block):
		if isinstance(block,Block) and (block.previous==self.__blocks[-1].proof if self.__blocks else block.previous=='') and block.valid and block not in self:
			self.__blocks.append(block)
			return True
		return False

	def pop(self,index=-1):
		try:
			self.__blocks.pop(index)
		except:
			pass

	@property
	def valid(self):
		previous=''
		for block in self.__blocks:
			if block.valid and block.previous==previous:
				previous=block.proof
			else:
				return False
		return True

	@property
	def value(self):
		chain={}
		for index,block in enumerate(self.__blocks):
			chain[index+1]=json.loads(block.value)
		return json.dumps(chain,indent=3)

	@property
	def tail(self):
		return self.__blocks[-1] if self.__blocks else None

	@property
	def length(self):
		return len(self.__blocks)

	@property
	def transactions(self):
		return [transaction for block in self.__blocks for transaction in block.transactions]
	

	@staticmethod
	def decode(ecdsa,raw):
		'''
		Converts raw json chainblock into a Chain object. Retrieve blocks from the json, then set up a "running_chain" and accept each block , if for some reason a block couldn't have been accpeted -> return empty Chain
		'''
		try:
			mapped=json.loads(raw)
		except:
			mapped={}
		finally:
			running_chain=Chain()
			if validate(mapped,**{'1':dict(type=dict,contains=['previous','data','proof'])}) and isinstance(ecdsa,ECDSA):
				for block in mapped:
					if not running_chain.accept(Block(ecdsa,raw=json.dumps(mapped[block]))):
						return Chain()
			return running_chain
