from lib.config import *

import simpy
import random

random.seed(SEED)

class Server:
	""" Create a server located in the provided country and labelled with the provided ID.
	The maximum capacity of the server is stored in the lib.config file. 
	When a request is sent to the server, it determines the sevice time and reduces its 
	available capacity until the client (request) does not leave the system.
	
	Parameters
	----------
		country : str
			contry where the server is located
		serv_id : int
			server identification number
	
	Attributes
	----------
		country : str
			contry where the server is located
		serv_id : int
			server identification number
		available_capacity : float
			available capacity of servers
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
	
	"""
	def __init__(self, country, serv_id):
		self.country = country
		self.serv_id = serv_id
		self.available_capacity = SERVER_LIMIT*CAPACITY
		# Server packets queue
		self.size_queue = []
		self.finish_queue = []
		
	def process(self, reqsize, env, cl_host):	
		"""The server processes the request by determining the service time and updating the 
		available capacity.
		The RTT is composed by three terms:
		1. A small server latency, coming from a discrete random variable uniformly 
		   distributed between 1 ms and 10 ms.
		2. Estimated RTT based on the client-server distance
		3. Transfer delay, which is determined by the size of the response divided by the
		   capacity allocated to the request in the server.
		
		When a request arrives at the server, its size is stored in a queue and the istant 
		at which the request should be served is stored in a second queue. The server 
		available capacity is updated before and after the request processing.
		
		Parameters
		----------
			size: float
				request size
			env : Environment
				instance of the SymPi Environment class
			cl_host : str
				country the client belongs to
			
		Yields
		------
			simpy.events.Timeout 
				after the service time in seconds
		
		"""
		RTT_row = COUNTRY.index(cl_host)
		RTT_col = COUNTRY.index(self.country)
		
		# Determine the service time
		t1 = random.uniform(1e-3, 1e-2)
		t2 = self.estimateRTT(RTT_row, RTT_col)
		t3 = reqsize/self.available_capacity
		time = t1 + t2 + t3
		
		# Add the new request to the queues
		self.size_queue.append(reqsize)
		self.finish_queue.append(env.now+time)
		# Update the server available capacity
		self.available_capacity -= self.size_queue[-1]
		
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
