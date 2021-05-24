import sympy,random,copy
from Utils.Additional import binary_exp,linear_congruence

class Curve:

	__D = lambda parameter: (4*binary_exp(parameter.get('a',0),3,parameter['p']) + 27*binary_exp(parameter.get('b',0),2,parameter['p']))%parameter['p']

	__validate = lambda data,**template: outcome if len(outcome:=dict(filter(lambda item:  (values:=template.get(item[0],None)) is not None and (item[1] in values if values else True ),data.items())))==len(template) else None
	
	
	def __init__(self,**parameters):
		self.__parameters,self.__order=self.__accept(**parameters),None
		base=self.__set_up_base(**{**self.__parameters,'order':parameters.get('order',None)})
		self.__parameters.update({'g':base[0],'order':base[1]})
		

	def __accept(self,**parameters):
		'''
		if all parameters have been assinged -> validate the prime, D for a,b
		Else generate a prime 'p', then generate respected a,b so that condition for D fulfills
		'''
		Zp = lambda parameter: parameter['a'] in range(parameter['p']) and parameter['b'] in range(parameter['p'])

		if (parameters:=Curve.__validate(parameters,p=(),a=(),b=(),g=())) and sympy.isprime(parameters['p']):
			if Curve.__D(parameters)!=0:
				return parameters
		return self.__generate()


	def __generate(self):
		parameters={'p':sympy.randprime(20,200)}
		while Curve.__D(parameters)==0:
			parameters['a'],parameters['b']=random.randint(0,parameters['p']-1),random.randint(0,parameters['p']-1)
		return parameters


	def __compute_primitive_element(self):
		'''
		Find a Running Point - present on the Curve
		'''
		R,x=Point(self),(i for i in range(self.p))
		while not R.x:
			try:
				R.x=next(x)
			except StopIteration:
				break
		return self.__compute_order(R)

	def __compute_order(self,R):
		'''
		return: (R,# computed using R)
		'''
		for order in self.order_range(prime=True):
			if not (order*R).coordinates:
				return R,order
		return R,None

	def __set_up_base(self,**parameters):
		if (coordinates:=parameters.get('g')):	
			
			point=Point(self)
			point.coordinates=coordinates
			
			if point.coordinates:
				base = (point,order) if (order:=parameters.get('order')) else self.__compute_order(point)
			else:
				raise Exception('Generator is not on the curve')
		else:
			
			while not (base:=self.__compute_primitive_element())[1]:
				self.__parameters=self.__generate()
		return base



	def order_range(self,prime=False):
		if (parameter:=Curve.__validate({'prime':prime},prime=(True,False))):
			
			side=lambda p,operation:getattr((p+1),f'__{operation}__')(2*round(p**0.5))
			
			hasse=range(side(self.p,'sub'),side(self.p,'add')+1)
			
			return (value for value in hasse if sympy.isprime(value) ) if parameter['prime'] else hasse


	def __getattr__(self,attr):
		return self.__parameters.get(attr,None)

	@property
	def parameters(self):
		return {k:(v if k!='g' else v.coordinates)  for k,v in self.__parameters.items()}


class Point:
	
	def __init__(self,curve):
		
		if isinstance(curve,Curve):
			self.__curve=curve
			self.__coordinates=None
		else:
			raise TypeError



	def __compute_y(self,x,multiple=False):
		return sympy.sqrt_mod((binary_exp(x,3,self.curve.p) + self.curve.a*x + self.curve.b)%self.curve.p,self.curve.p,multiple)

	def __add__(self,other):
		'''
		С - current point, O - other point
		If O is on the curve, but doesnt have any coordinates - then return C , works viceversa
		If O is on the curve, has coordinates : if C==-O then return None - "Infinity" , otherwise procede to add according to the conditions [slope=tagnent if C==O, otherwise slope=line]
		S+O=R
		'''
		if isinstance(other,Point) and self.__curve==other.curve:
			
			if not other.coordinates or not self.coordinates:
				R=Point(self.__curve)
				if (coordinates:=(self.coordinates if self.coordinates else (other.coordinates if other.coordinates else None))):
					R.coordinates=coordinates
				return R

			if self!=-other:
			
				slope = ( (3*(self.x**2) + self.curve.a)* linear_congruence( 2*self.y, 1, self.curve.p ) )%self.curve.p  if self==other else \
				( (other.y-self.y)*linear_congruence( (other.x-self.x)%self.curve.p, 1, self.curve.p ) )%self.curve.p

				x = (slope**2 - self.x - other.x) % self.curve.p
				y = (slope * (self.x-x) - self.y) % self.curve.p

				R=Point(self.__curve)
				R.coordinates=(x,y)
				return R

			return Point(self.__curve)

		raise TypeError

	def __radd__(self,other):
		'''
		C - self point, O - other point
		O+C
		'''
		return self.__add__(self,other)


	def __mul__(self,n):
		'''
		C - current point , n - multiplicative value
		Initial state C=R ~> running point = Infinity ~> a Point that's on a curve with no coordinates
		Double and add algorithm : on each iteration - double (if R has coodrinates) , then if the bit is a '1' - add
		In case, if at some iteration R becomes infinity -> initial state
		'''
		'''Double and Add'''
		R=Point(self.__curve)
		if isinstance(n,int) and n>0:
			n = bin(n%self.curve.order if self.curve.order else n)[2:]
			for bit in n:
				R = (R+R) if R.coordinates else R
				R = (self+R) if bit=='1' else R
		return R

	def __rmul__(self,n):
		return self.__mul__(n)

	
	def __eq__(self,other):
		'''
		C - current point, O - other point
		C==O
		'''
		if (siblings:=isinstance(other,type(self))) and self.coordinates and other.coordinates:
			return self.coordinates == other.coordinates
		if not other and not siblings:
			return False
		raise TypeError

	def __ne__(self,other):
		'''
		C - current point, O - other point
		C!=O
		'''
		if (siblings:=isinstance(other,type(self))) and self.coordinates and other.coordinates:
			return self.coordinates != other.coordinates
		if not other and not siblings:
			return False
		raise TypeError

	def __neg__(self):
		'''
		C (x,y) - current point
		-C = (x,-y%p)
		'''
		if self.__coordinates:
			inverse=Point(self.__curve)
			inverse.coordinates=(self.x, -self.y%self.curve.p)
			return inverse

		return None
	
	@property
	def x(self):
		return self.__coordinates[0] if self.__coordinates else None

	@x.setter
	def x(self,coordinate):
		if not self.__coordinates and (y:=self.__compute_y(coordinate)):
			self.__coordinates=(coordinate,y)
		return None

	@property
	def y(self):
		return self.__coordinates[1] if self.__coordinates else None

	@property
	def coordinates(self):
		return self.__coordinates

	@coordinates.setter
	def coordinates(self,coordinates):
		if not self.__coordinates and isinstance(coordinates,tuple) and len(coordinates)==2 and coordinates[1] in self.__compute_y(coordinates[0],True):
			self.__coordinates=coordinates
		return None

	@property
	def curve(self):
		return self.__curve
	
