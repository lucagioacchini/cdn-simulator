from lib.server_static import Server
from lib.config import *

import simpy as sp
import random

random.seed(SEED)

class Client:
	"""Create a new client and start its session. A session is made of a number of requests
	belonging to [10, 100]. When all the client's requests are served, the client leaves the 
	system. 
	If all the countries have busy servers, a new server is deployed by using 3
	criteria:
	exp : 1 - Distance-based one.
	exp : 2 - Cost-based one.
	exp : 3 - People-based one.
	
	Parameters
	----------
		env : simpy.core.Environment
			instance of the SimPy Environment class
		key : str
			country of the client
		cl_id : int
			client identification number
		rack : dict
			list of servers located in each country
		stat : instance
			instance of the Stats class used to analyze performances and results
		exp : int
			deploy strategy identification number
			
	Attributes
	----------
		env : simpy.core.Environment
			instance of the SimPy Environment class
		key : str
			country of the client
		cl_id : int
			client identification number
		rack_list : dict
			list of servers located in each country
		req_size : float
			client request size
		k : int
			number of client requests
		exp : int
			deploy strategy identification number
		session_time : float
			total time spent by a client in the system
		stat : instance
			instance of the Stats class used to analyze performances and results
	
	Methods
	-------
		startSession()
			start the session of each client and assigns the requests to the servers
		costCheck()
			find the best country where the new server will be deployed with respect to
			the minimum maintaining cost
		peopleCheck()
			find the best country where the new server will be deployed with respect to
			the number of inhabitants
			
	"""
	def __init__(self, env, key, cl_id, rack, stat, exp):
		self.key = key
		self.k = random.randint(10,100)
		self.env = env
		self.req_size = 0
		self.cl_id = cl_id
		self.rack_list = rack
		self.session_time = .0
		self.exp = exp
		self.stat = stat

		self.env.process(self.startSession())
	
	
	def startSession(self):
		"""Start the session of each client. A client is associated with a number of 
		requests belonging to [10, 100]. The size request is a number belonging to 
		[4MB, 40MB].
		When the client send a request to a server, it checks if local servers are 
		available. Otherwise, an available server in other countries is searched. The
		searching policy is based on the client-server distance: the client check in the 
		nearest country first.
		If all the countries have busy servers, a new local server is added. The request is
		served by this last one and the server rack is updated.
		
		Deploying strategy: Firstly the number of servers per country is checked. 
		exp : 1 - The new server is deployed locally
		exp : 2 - Firstly the number of served per country is checked. The new server is
			deployed in the country identified with the minimum mantaining cost. The 
			countries are roundly chosen until all the countries don't have the same number 
			of servers.
		exp : 3 - Firstly the number of served per country is checked. The new server is
			deployed in the country identified with the maximum number of inhabitants. The 
			countries are roundly chosen until all the countries don't have the same number 
			of servers.
			
		When a client finishes its requests, it leaves the system.
		
		Attributes
		----------
			busy : bool
				True if all the servers are busy, False otherwise
			retry : bool
				True if the client is retrying to send the request, False otherwise

		Yields
		------
			simpy.events.Process 
				The process is the 'processing' method of the Server class
			
		"""
		time_ref = self.env.now
		
		while self.k > 0:
			self.stat.nOfReq()
			# define the request size
			self.req_size = random.uniform(MIN_REQ, MAX_REQ)
			
			self.busy = True
			
			# sort the local server list according to their available capacity
			self.rack_list[self.key] = sorted(
				self.rack_list[self.key], 
				reverse = True, 
				key = lambda x:x.available_capacity
			)
			
			# send the request to the server with the maximum available capacity
			for server in self.rack_list[self.key]:
				if self.req_size <= server.available_capacity:
					self.busy = False
					# update the number of request served locally
					self.stat.localReq()
					
					# the local server serves the client
					yield self.env.process(server.process(
						self.req_size, 
						self.env, 
						self.key
					))
					break
			
			# if the local servers are busy check the other countries
			if self.busy == True:
				cl_row = COUNTRY.index(self.key)
				# sort the countries in an ascending way with respect to their distance 
				# from the client region
				temp_row = np.sort(DISTANCES[cl_row,:])
				# look for available foreign servers
				for item in temp_row:
					if item != 0:
						# sort the foreign server list according to their available capacity
						country = COUNTRY[np.where(temp_row == item)[0][0]]
						self.rack_list[country] = sorted(
							self.rack_list[country], 
							reverse = True, 
							key = lambda x:x.available_capacity 
						)
						# send the request to the foreign server with the maximum 
						# available capacity
						for server in self.rack_list[country]:
							if self.req_size <= server.available_capacity:
								self.busy = False
								
								# the foreign server serves the client
								yield self.env.process(server.process(
									self.req_size, 
									self.env, 
									country
								))
								break
				
				# all the servers are busy, create a new local server
				if self.busy == True:
					# deploy new server with respect to distance
					if self.exp == 1:
						serv_id = self.rack_list[self.key][-1].serv_id + 1
						# update the local servers rack list
						self.rack_list[self.key].append(Server(self.key, serv_id))
						server = self.rack_list[self.key][-1]
						print "\t   new server added in {}".format(self.key)
						# update the number of request served locally
						self.stat.localReq()
						
						# the new local server serves the client
						yield self.env.process(server.process(
							self.req_size, 
							self.env, 
							self.key
						))
					
					# deploy new server with respect to cost	
					elif self.exp == 2:
						serv_id = self.rack_list[self.key][-1].serv_id + 1
						next_serv = self.costCheck()
						# update the local servers rack list
						self.rack_list[next_serv].append(Server(next_serv, serv_id))
						server = self.rack_list[next_serv][-1]
						print "\t   new server added in {}".format(next_serv)
						# update the number of request served locally
						self.stat.localReq()
						
						# the new local server serves the client
						yield self.env.process(server.process(
							self.req_size, 
							self.env, 
							self.key
						))
					
					# deploy new server with respect to people
					elif self.exp == 3:
						serv_id = self.rack_list[self.key][-1].serv_id + 1
						next_serv = self.peopleCheck()
						# update the local servers rack list
						self.rack_list[next_serv].append(Server(next_serv, serv_id))
						server = self.rack_list[next_serv][-1]
						print "\t   new server added in {}".format(next_serv)
						# update the number of request served locally
						self.stat.localReq()
						
						# the new local server serves the client
						yield self.env.process(server.process(
							self.req_size, 
							self.env, 
							self.key
						))
			
			# update the remaining request number			
			self.k -= 1
			
			# estimate the session time for each client
			if self.k == 0:
				self.stat.estimateSessionTime(self.env.now - time_ref)
				
	def costCheck(self):
		"""Sort the countries with respect to the minimum mantaining cost of a server.
		people in the countries hosting the servers.
		The new server is deployed in the country identified with the minimum mantaining 
		cost. The countries are roundly chosen until all the countries don't have the same 
		number of servers.
		
		Returns
		-------
			min_country : str
				country where the new server will be deployed
				
		"""	
		min_flag = False
		max_n_serv = 0
		min_cost_list = []
		for u in COUNTRY:
			if len(self.rack_list[u]) > max_n_serv:
				max_n_serv = len(self.rack_list[u])
		
		for u in COUNTRY:
			min_cost_list.append([COSTS[u], u])
		
		min_cost_list = sorted(
			min_cost_list,
			key = lambda x:x[0]
		)
		
		for i in range(5):
			min_country = min_cost_list[i][1]
			if len(self.rack_list[min_country]) < max_n_serv:
				min_flag = True
				return min_country
		
		if min_flag == False:
			for i in range(5):
				min_country = min_cost_list[i][1]
				if len(self.rack_list[min_country]) == max_n_serv:
					break
			return min_country
			
	def peopleCheck(self):
		"""Sort the countries with respect to the minimum mantaining cost of a server.
		people in the countries hosting the servers.
		The new server is deployed in the country identified with the maximum number of
		inhabitants. The countries are roundly chosen until all the countries don't have the 
		same number of servers.
		
		Returns
		-------
			max_country : str
				country where the new server will be deployed
				
		"""	
		max_flag = False
		max_n_serv = 0
		max_people_list = []
		for u in COUNTRY:
			if len(self.rack_list[u]) > max_n_serv:
				max_n_serv = len(self.rack_list[u])
		
		for u in COUNTRY:
			max_people_list.append([DAILY_USERS[u], u])
		
		max_people_list = sorted(
			max_people_list,
			reverse = True,
			key = lambda x:x[0]
		)

		for i in range(5):
			max_country = max_people_list[i][1]
			if len(self.rack_list[max_country]) < max_n_serv:
				max_flag = True
				return max_country
		
		if max_flag == False:
			for i in range(5):
				max_country = max_people_list[i][1]
				if len(self.rack_list[max_country]) == max_n_serv:
					break
			return max_country
