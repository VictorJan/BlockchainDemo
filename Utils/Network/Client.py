from Utils.EllipticCurve import Curve
from Utils.Signature import ECDSA
from Utils.Blockchain.Transaction import Transaction
from Utils.Blockchain.Block import Block
from Utils.Blockchain.Chain import Chain
from threading import Thread,Lock
import json,socket,re

class Client:
	def __init__(self,server_socket):
		print('Client:')
		self.__socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.__socket.connect(server_socket)
		
		if self.__set_up_connection():
			self.__blockchain=Chain()
			for thread in (Thread(target=self.__send),Thread(target=self.__receive)):
				thread.start()
		else:
			print('Couldn\'t establish a connection.')

	def __set_up_connection(self):
		'''
		1.S:->{p,g,#}:C
		2.S:<-{user,public_key}
		3.S -!- {user,public_key}
		'''
		domain=json.loads((message:=self.__socket.recv(1024).decode()))
		domain['g']=tuple(domain['g'])
		self.__ecdsa=ECDSA((name:=input('Your unique name:')),Curve(**domain))
		self.__socket.send(json.dumps({'user':name,'public_key':self.__ecdsa.keyring['public_key'].coordinates}).encode())
		if self.__socket.recv(1024).decode()=='Connection is set up.':
			return True
		return False

	def __send(self):
		command_re,transaction_re='\[(.+)\]','(\d+)>(\w+)'
		while True:
			try:
				if (command_match:=re.match(command_re,(input_stream:=input("#")))) and (command:=command_match.groups(0)):
					if (transaction_match:=re.match(transaction_re,command[0])) and (payload:=transaction_match.groups()) :
						if (transaction:=Transaction(self.__ecdsa,payload=dict(recipient=payload[1],amount=int(payload[0])))).valid:
							self.__socket.send(f"[Transaction]{transaction.value}".encode())
					elif command[0] == 'Mine':
						if (transactions:=Transaction.get_transactions()) and (block:=Block(self.__ecdsa,payload=dict(previous = (last.proof if (last:=self.__blockchain.tail) else ''),transactions=tuple(transactions) ) )).valid:
							self.__socket.send(f"[Block]{json.dumps(json.loads(block.value))}".encode())		
					elif command[0] == 'keychain':
						print(','.join(self.__ecdsa.keychain.keys()))
					elif command[0] == 'blockchain':
						print(self.__blockchain.value)

					elif command[0] == "Request Blockchain":
						self.__socket.send('[Request Blockchain]'.encode())

			except:
				break

	def __receive(self):
		'''
		if: incoming content is json -> treat it as a function, i.e new Transaction , new Public Key, new Block 
		[Transaction],[Block],[Key],[Request Blockchain]
		'''
		proper='\[(Block|Transaction|Key|Request Blockchain)\](.*)'
		resolution_re='\[(Accepted|Denied)\](.+)'
		while True:
			try:
				data=self.__socket.recv(4096).decode()
				if (incoming:=re.match(proper,data)) and (incoming:=incoming.groups()):
					if incoming[0]=='Key' and incoming[1]:
						if self.__ecdsa.add(**(payload:=json.loads(incoming[1]))):
							print(f"{payload['user']} has joined.\n#",end="")
					
					elif incoming[0]=='Transaction' and incoming[1]:
						if (t:=Transaction(self.__ecdsa,raw=incoming[1])).valid:
							
							self.__ecdsa.add(user=t.data['recipient']['name'],public_key=t.data['recipient']['public_key'])
							
							print(f"New valid transaction : {t.data['sender']['name']} {t.data['content']} > {t.data['recipient']['name']}\n#",end="")
					
					elif incoming[0]=='Block' and incoming[1]:
						if (resolution:=re.match(resolution_re,incoming[1])) and (resolution:=resolution.groups()):
							if resolution[0]=='Accepted' and (b:=Block(self.__ecdsa,raw=resolution[1])).valid:
								if self.__blockchain.accept(b):
									Transaction.update_transactions(*b.transactions)
									print('By the majority of votes, the block has been accepted and the transactions have been updated.\n#',end="")
								else:
									print('By the majority of votes, the block has been accepted. However it\'s not suitable for your chain , update the chain using the "[Request Blockchain]" command.\n#',end="")
							else:
								print('By the majority of votes, the block wasn\'t accepted.\n#',end="")
						else:
							if (b:=Block(self.__ecdsa,raw=incoming[1])).valid and self.__blockchain.accept(b):
								self.__blockchain.pop()
								Transaction.update_transactions(*b.transactions)
								self.__socket.send(f"[Block][Accept]".encode())
							else:
								self.__socket.send(f"[Block][Deny]".encode())
					
					elif incoming[0]=='Request Blockchain':
						if not incoming[1]:
							self.__socket.send(f"[Request Blockchain]{json.dumps(json.loads(self.__blockchain.value))}".encode())
						else:
							self.__blockchain=Chain.decode(self.__ecdsa,raw=incoming[1])
							Transaction.update_transactions(*self.__blockchain.transactions)
							print('The blockchain has been updated.\n#',end="")


			except:
				break







	