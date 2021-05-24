from Utils.EllipticCurve import Curve
from Utils.Signature import ECDSA
from Utils.Blockchain.Transaction import Transaction
from Utils.Blockchain.Block import Block
from Utils.Blockchain.Chain import Chain
from threading import Thread,Lock
import json,socket,re

class Server:
	def __init__(self,server_socket):
		self.__ecdsa,self.__connections=ECDSA('server',Curve()),{}
		self.__socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.__socket.bind(server_socket)
		self.__socket.listen(5)
		self.__resolving={}
		self.__handle_connections()

	def __handle_connections(self):
		while True:
			client=self.__socket.accept()
			if self.__set_up_connection(client):
				Thread(target=self.__receive,args=(client,)).start()


	def __set_up_connection(self,client):
		'''
		1.S:->{p,g,#}:C
		2.S:<-{user,public_key}
		3.S -!- {user,public_key}
		'''

		client[0].send(json.dumps(self.__ecdsa.curve.parameters).encode())

		if self.__ecdsa.add( **(payload:=json.loads(client[0].recv(1024).decode())) ) and payload['user'] not in self.__connections:
			self.__connections[client]={'name':payload['user']}
			client[0].send('Connection is set up.'.encode())
			self.__multicast(f"[Key]{json.dumps({'user':payload['user'],'public_key':self.__ecdsa.keychain[payload['user']].coordinates})}",self.__connections[client])
			return True

		return False


	def __receive(self,client):
		'''
		If message is new block request -> send the block to the resolving ,with amount of votes [1] , the miner's vote, and the according block -> send to other users. Then wait for responses and add the votes, at the end of each count verify the amount of votes, if amount == amount of clients -> send a resolution. 
		Resolve Block : block:[value],votes:[value]
		Resolve Chain : chains:[chain objects]
		'''
		block_re='\[Block\]({.+})'
		vote_re='\[Block\]\[(Accept|Deny)\]'
		blockchain_re = '\[Request Blockchain\]'
		while True:
			incoming=client[0].recv(4096).decode()
			if (resolve_match:=re.match(block_re,incoming)) and not self.__resolving:
				self.__resolving={'block':resolve_match.groups()[0],'votes':[1]}
				self.__multicast(incoming,self.__connections[client])
			
			elif (resolve_match:=re.match(vote_re,incoming)) and 'block' in self.__resolving and 'votes' in self.__resolving:
				
				self.__resolving['votes']+=([1] if resolve_match.groups()[0]=='Accept' else [-1])
				
				if self.__resolving and len(self.__resolving['votes'])==len(self.__connections):
					self.__multicast(f"[Block][{'Accepted' if sum(self.__resolving['votes']) > 0 else 'Denied'}]{self.__resolving['block']}")
					self.__resolving={}

			elif (blockchain_match:=re.match(blockchain_re,incoming)) and not self.__resolving:
				self.__resolving['chains']=[]
				self.__resolving['requestee']=self.__connections[client]
				self.__multicast(incoming,self.__connections[client])

			elif (blockchain_match:=re.match(f"{blockchain_re}({{.*}})",incoming)):
				self.__resolving['chains']+=[Chain.decode(self.__ecdsa,(raw_chain:=blockchain_match.groups()[0]))]
				if self.__resolving and len(self.__resolving['chains'])==len(self.__connections)-1:
					payload=f"[Request Blockchain]{json.dumps(json.loads( (max(self.__resolving['chains'],key=lambda c:c.length).value) ))}"
					self.__multicast(payload,sender=None,recipient=self.__resolving['requestee'])
					self.__resolving={}

			else:
				self.__multicast(incoming,self.__connections[client])



	def __multicast(self,message,sender=None,recipient=None):
		for client in self.__connections:
			if recipient and self.__connections[client]['name'] == recipient['name']:
				client[0].send(message.encode())
				return None

			elif (self.__connections[client]['name']!=sender['name'] if sender else True) and not recipient:
				client[0].send(message.encode())

		return None
