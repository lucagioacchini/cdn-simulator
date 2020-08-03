from lib.server_dynamic import Server
from lib.config import *

import simpy as sp
import random

random.seed(SEED)

class Client:
	"""Create a new client and start its session. A session is made of a number of requests
	belonging to [10, 100]. When all the client's requests are served, the client leaves the 
	system.
	
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
		session_time : float
			total time spent by a client in the system
		stat : instance
			instance of the Stats class used to analyze performances and results
	
	Methods
	-------
		startSession()
			start the session of each client and assigns the requests to the servers
			
	"""
	def __init__(self, env, key, cl_id, rack, stat):
		self.key = key
		self.k = random.randint(10,100)
		self.env = env
		self.req_size = 0
		self.cl_id = cl_id
		self.rack_list = rack
		self.session_time = .0
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
		If all the countries have busy servers, it starts to resend the same request until 
		it is not served.
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
		self.time_ref = self.env.now
		
		while self.k > 0:
			retry_cnt = 0
			self.stat.nOfReq()
			self.req_size = random.uniform(MIN_REQ, MAX_REQ)
			self.busy = True
			self.retry = False
			
			while self.busy:
				# sort the local server list according to their available capacity
				self.rack_list[self.key] = sorted(
					self.rack_list[self.key], 
					reverse = True, 
					key = lambda x:x.available_capacity
				)
			
				# send the request to the server with the maximum available capacity
				for server in self.rack_list[self.key]:
					if self.req_size <= server.available_capacity and \
					  not server.in_idle and \
					  not server.completing:
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
							# sort the foreign server list according to their 
							# available capacity
							country = COUNTRY[np.where(temp_row == item)[0][0]]
							self.rack_list[country] = sorted(
								self.rack_list[country], 
								reverse = True, 
								key = lambda x:x.available_capacity 
							)
						
							# send the request to the foreign server with the maximum 
							# available capacity
							for server in self.rack_list[country]:
								if self.req_size <= server.available_capacity and \
								  not server.in_idle and \
								  not server.completing:
									self.busy = False
									
									# the foreign server serves the client
									yield self.env.process(server.process(
										self.req_size, 
										self.env, 
										country
									))
									break
				
				if self.busy == True:
					# the client waits 1 second before retrying to reach an available server
					yield self.env.timeout(.05)
					retry_cnt+=1
					self.retry = True
					if retry_cnt == 1 and self.key=='China':
						"""
						print 'Server busy. req id: {}-{}'.format(
							self.cl_id, 
							self.k
						)
						"""
				else:
					self.retry = False
					if retry_cnt!=0 and self.key=='China':
						"""
						print 'Request {} -{} served after {} attempts'.format(
							self.cl_id, 
							self.k, 
							retry_cnt
						)
						"""

			# update the remaining request number			
			self.k -= 1
			
			# estimate the session time for each client
			if self.k == 0:
				self.stat.estimateSessionTime(self.env.now - time_ref)
