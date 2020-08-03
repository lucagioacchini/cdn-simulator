import random
import simpy

from lib.config import *

random.seed(SEED)

class Server:
	""" Create a server located in the provided country and labelled with the provided ID.
	The maximum capacity of the server is stored in the lib.config file. 
	When a request is sent to the server, it determines the sevice time and reduces its 
	available capacity until the client (request) does not leave the system.
	If the available capacity is near to the max_th threshold, a new server is woken up by 
	following three different criteria:
	exp : 1 - Distance-based one.
	exp : 2 - Cost-based one
	exp : 3 - People-based one.
	When the available capacity exceeds the idle_th threshold, from now on, if it goes under
	the min_th threshold enters the 'completing' status. No more requests are accepted, the
	server serves the pending ones and then is set to idle.
	
	Parameters
	----------
		country : str
			contry where the server is located
		serv_id : int
			server identification number
		exp : int
			wake up strategy identification number
	
	Attributes
	----------
		country : str
			contry where the server is located
		serv_id : int
			server identification number
		exp : int
			wake up strategy identification number
		available_capacity : float
			available capacity of servers
		server_list : list
			list of all the servers deployed in the CDN
		best_list : list
			list of the deployed servers sorted with three different criteria. The criterium
			is indicated by the exp attribute
		canIdle : bool
			True if the server can be in idle, False otherwise
		completing : bool
			True if the server cannot accept more request and it is emptying the queues
		inIdle : bool
			True if the server is in idle, False otherwise
		size_queue : list
			server's packet queue storing the requests size
		finish_queue : list
			server's packet queue storing the instant at which the request is served
			
	Methods
	-------
		process(size, env, cl_host)
			serves the request and update the server available capacity
		estimateRTT(row, col)
			estimate the packet Round Trip Time (RTT)
		wakeUp(host)
			wake up a server with three different criteria. The criterion is indicated by
			the exp attribute
		minActiveServ()
			check if the minimum number of active servers per region is ensured
		endService(env)
			the server stops receiving new requests, serves the ones in the queues and
			is goes in idle
		orderCost()
			sort the deployed servers in the whole CDN with respect to the minimum cost
		orderPeople()
			sort the deployed servers in the whole CDN with respect to the maximum number
			of people in the hosting countries
	
	"""
	def __init__(self, country, serv_id, exp):
		self.country = country
		self.serv_id = serv_id
		self.exp = exp
		self.available_capacity = CAPACITY
		# Servers list
		self.server_list = []
		self.best_list = []
		# Dynamic allocation flags
		self.can_idle = False
		self.completing = False
		self.in_idle = True
		# Server packets queue
		self.size_queue = []
		self.finish_queue = []
		
		if self.exp == 2:
			self.orderCost()
		elif self.exp == 3:
			self.orderPeople()
		
		
	def process(self, reqsize, env, cl_host):	
		"""The server processes the request by determining the service time and updating 
		the	available capacity.
		The RTT is composed by three terms:
		1 - A small server latency, coming from a discrete random variable uniformly 
		   distributed between 1 ms and 10 ms.
		2 - Estimated RTT based on the client-server distance
		3 - Transfer delay, which is determined by the size of the response divided by 
		the capacity allocated to the request in the server.
		
		When a request arrives at the server, its size is stored in a queue and the istant 
		at which the request should be served is stored in a second queue. The server 
		available capacity is updated before and after the request processing.
		
		Parameters
		----------
			reqsize: float
				request size in bits
			env : simpy.core.Environment
				instance of the SymPi Environment class
			cl_host : str
				country the client belongs to
		
		Attributes
		----------
			idle_th : float
				capacity threshold. The server can be in idle if this threshold is excedeed
			min_th : float
				capacity threshold. The server completes its pending requests and goes in 
				idle if this threshold is exceeded
			max_th : float
				capacity threshold. The server wake up a new server if this threshold is
				excedeed
			self.req : float
				request size in bits
				
		Yields
		------
			simpy.events.Timeout 
				after the service time in seconds
		
		"""
		hour = int(env.now/3600)
		hour += START
		if hour >= 24:
			hour -= 24
		if hour >= 4 and hour < 13:
			self.idle_th = CANIDLE_H
			self.min_th =  MIN_H
			self.max_th = MAX_H
		else:
			self.idle_th = CANIDLE_L
			self.min_th = MIN_L
			self.max_th = MAX_L
		
		RTT_row = COUNTRY.index(cl_host)
		RTT_col = COUNTRY.index(self.country)
		
		# Determine the service time
		t1 = random.uniform(1e-3, 1e-2)
		t2 = self.estimateRTT(RTT_row, RTT_col)
		t3 = reqsize/self.available_capacity
		time = t1 + t2 + t3
		
		# Add the new request to the queues
		self.size_queue.append(reqsize)
		self.finish_queue.append(env.now + time)
		# Update the server available capacity
		self.available_capacity -= reqsize
		
		# The minimum capacity is exceeded. From now on the server can be in idle
		if self.available_capacity <= self.idle_th:
			self.can_idle = True
			
		# The maximum capacity is exceeded. A server in idle can be woken up
		if self.available_capacity <= self.max_th:
			#print '{}:{} - Waking up a server'.format(self.country, self.serv_id)
			self.wakeUp(cl_host)
			self.can_wake = False
			
		# The available capacity is over the minimum capacity.
		if self.available_capacity >= self.min_th and self.can_idle:
			# if the minimum number of local active server is ensured, the server stops 
			# receiving new requests
			if self.minActiveServ():
				#print '{}:{} server can be idle'.format(self.country, self.serv_id)
				self.completing = True
				env.process(self.endService(env))

		yield env.timeout(time)
		
		# Update the server available capacity
		to_remove = self.finish_queue.index(env.now)
		# After the request processing update the available capacity
		self.available_capacity += self.size_queue[to_remove]
		# Remove the served requests from the queue
		self.size_queue.pop(to_remove)
		self.finish_queue.pop(to_remove)
		
		
	def estimateRTT(self, row, col):
		"""Estimate the packet Round Trip Time (RTT) by using the Distances matrix stored in
		the lib.config file. The RTT is estimated by dividing the distance in km between 
		the server location and the request sender one times 3*1e5.
		
		Parameters
		----------
			row : int
				row index of the Distances matrix
			col : int
				column index of the Distances matrix
				
		Returns
		-------
			dist_delay : float
				estimated RTT in seconds
		
		"""
		dist = DISTANCES[row][col]
		dist_delay = dist/(3*1e5)
		
		return dist_delay
	
	
	def wakeUp(self, cl_host):
		""" Wake up a server by using three different criteria:
		exp : 1 - Firstly the local servers are checked. If all the local servers are
			active, the nearest country is checked and so on until a server in idle is not 
			found
		exp : 2 - The best server to wake up is chosen in the country with the minimum
			mantaining cost.
		exp : 3 - The best server to wake up is chosen in the country with the greatest 
			number of people.
		
		Parameters
		----------
			cl_host : string
				country of the client which is being served
		Attributes
		----------
			triggered : bool
				True if a server is woken up, False otherwise
		"""
		active_cnt = 0
		self.triggered = False
		
		# exp 1
		if self.exp == 1:
			# Wake up a local server first
			for serv in self.server_list[cl_host]:
				if serv.inIdle:
					serv.inIdle = False
					self.triggered = True
					"""
					print '{}:{} locally wake up'.format(
						serv.country, 
						serv.serv_id
					)
					"""
					break
		
			# If local servers cannot be woken up, wake up a foreign server
			if self.triggered == False:
				# sort the countries in an ascending way with respect to their distance 
				# from the client region
				cl_row = COUNTRY.index(cl_host)
				temp_row = np.sort(DISTANCES[cl_row,:])
				# look for available foreign servers
				for item in temp_row:
					if item != 0:
						foreign = COUNTRY[np.where(temp_row == item)[0][0]]
						for serv in self.server_list[foreign]:
							if serv.inIdle:
								serv.inIdle = False
								self.triggered = True
								"""
								print '{}:{} foreign wake up'.format(
									serv.country, 
									serv.serv_id
								)
								"""
								break
						if self.triggered == True:
							break
		
		# exp 2 or 3
		else:
			for i in range(5):
				best_country = self.best_list[i][1]
				for serv in self.server_list[best_country]:
					if serv.inIdle:
						serv.inIdle = False
						self.triggered = True
						"""
						print '{}:{} wake up'.format(
							self.country, 
							best_country
						)
						"""
						break
				if self.triggered:
					break	
			
										
	def minActiveServ(self):
		"""Exploit the deployed server list to check if the minimum number of servers in the
		same country of the actual server is ensured.
		
		Attributes
		----------
			active_cnt : int
				counter of the local active servers
			
		Returns
		-------
			bool
				True if the minimum number of local servers is ensured, False otherwise
		"""
		self.active_cnt = 0
		
		for serv in self.server_list[self.country]:	
			if not serv.inIdle and not serv.completing:
				self.active_cnt+=1
		
		if self.active_cnt > MIN_ACTIVE[self.country]:
			return True
		else:
			return False
	
	
	def endService(self, env):
		"""The server stops receiving new requests, completes the pending ones, empties
		the queues and goes to sleep.
		
		Parameters
		----------
			env : simpy.core.Environment
		
		Yields
		------
			simpy.events.Timeout
				after the service time nedded to empty the queue 
		"""
		temp = sorted(
			self.finish_queue,
			reverse = True
		)
		wait = temp[0]-env.now
		
		yield env.timeout(wait)
		
		self.available_capacity += sum(self.size_queue)
		#print '{}:{} server in idle'.format(self.country, self.serv_id)
		
		# The queues are emptied
		self.size_queue = []
		self.finish_queue = []
		
		# When all the requests are served, the server is put in idle
		self.completing = False
		self.in_idle = True
		self.can_idle = False
		
		
	def orderCost(self):	
		"""Sort the deployed servers in the whole CDN with respect to the minimum mantaining
		cost.
		"""	
		for u in COUNTRY:
			self.best_list.append([COSTS[u], u])
		
		self.best_list = sorted(
			self.best_list,
			key = lambda x:x[0]
		)		
	
	
	def orderPeople(self):		
		"""Sort the deployed servers in the whole CDN with respect to the maximum number of 
		people in the countries hosting the servers.
		"""	
		for u in COUNTRY:
			self.best_list.append([DAILY_USERS[u], u])
		
		self.best_list = sorted(
			self.best_list,
			key = lambda x:x[0]
		)
