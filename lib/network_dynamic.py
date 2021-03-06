from client_dynamic import Client
from server_dynamic import Server
from config import *

import simpy as sp
import numpy as np
import datetime

np.random.seed(SEED)

class Network:
	""" Implementation of a Content Delivery Network. Server racks are located in five
	countries: India, China, USA, Japan, Brazil. A rack with x servers is initially 
	placed in each contry and the total CDN mantaining cost is calculated every 'x' minutes.
	The value of 'x' is stored in the lib.config file.
	
	Parameters
	----------
		stat : instance
			instance of Stats class. It is used to analyze performances and results
		exp : int
			wake up strategy identification number
			
	Attributes
	----------
		total_cost : float
			total mantaining cost of the CDN
		stat : instance
			instance of the Stats class used to analyze the simulator performances
		s : dict
			the keys are the countries, the values are the servers rack
		cl : instance
			instance of the Client class
	
	Methods
	-------
		startServers()
			initialize a servers rack in each country.
		arrival(env, avg_dly_cl, key)
			simulate a request arrival
		updateCost()
			every 'x' minsutes the total mantaining cost of the CDN is updated
		getTime(now)
			manage the simulation time by turning the seconds into hh:mm:ss format.
	
	"""
	def __init__(self, stat, exp):
		self.s = {}
		self.total_cost = 0
		self.stat = stat
		self.exp = exp
				
		self.startServers()
		

	def startServers(self):
		"""Initialize a servers rack in each country. The starting number of servers in a
		 rack is stored in the lib.config file.
		
		Attributes
		----------
			rack : dict
				each entry contains the country and the number of servers in that country
		"""
		cnt = 0
		# Deploy servers rack
		for u in COUNTRY:
			self.rack = []
			for i in range(SERVERS_DYN[u]):
				cnt+=1
				self.rack.append(Server(u, cnt, self.exp))
				self.s[u] = self.rack
		
		# Provide the server list to each server
		for u in COUNTRY:
			for server in self.s[u]:
				server.server_list = self.s
			for i in range(START_ACTIVE[u]):
				self.s[u][i].inIdle = False				
		
		
	def arrival(self, env, avg_dly_cl, key):
		"""Cyclically initialize new clients after an exponentially distributed time 
		interval. Every 'x' minutes the total mantaining cost of the CDN is evaluated.
		The value of 'x' is stored in the lib.config file.
		
		Parameters
		----------
			env : simpy.core.Environment
				instance of the SymPi Environment class
			avg_dly_cl : float
				country-specific number of daily internet users
			key :  string
				country name
				
		Yields
		------
			simpy.events.Timeout
				after the inter_arrival delay
			
		"""
		cnt = 0
		hour = START
		acquisition = 0

		while True:
			# time manager
			if int(env.now/(INTERACQ*60))!=acquisition:
				acquisition = int(env.now/(INTERACQ*60))
				# update the cost every 'x' minutes
				if key == "Japan":
					# update the average session time
					self.stat.avgSessionTime()
					cost = self.updateCost()
					timing = self.getTime(env.now)
					active = self.stat.nActive(self.s)
					act_ch = self.stat.singActive(self.s['China'])
					act_ja = self.stat.singActive(self.s['Japan'])
					act_br = self.stat.singActive(self.s['Brazil'])
					act_us = self.stat.singActive(self.s['USA'])
					act_in = self.stat.singActive(self.s['India'])
					print """------------------------------
					{} - avg.sess.time: {}
						   local requests: {}%
						   tot.cost: {} USD
						   active: {}""".format(
						timing, 
						self.stat.avg_sess_time,
						self.stat.local_req_perc,
						cost,
						active
					)

					self.stat.createDF(
						timing, 
						self.stat.avg_sess_time,
						self.stat.local_req_perc,
						cost,
						act_ch,
						act_ja,
						act_br,
						act_us,
						act_in,
						active,
						self.exp
					)
			# update the simulated hours
			if int(env.now/3600)+START!=hour:
				hour = int(env.now/3600)+START
				if hour >=24:
					hour = hour-24
			# timezone managing
			if hour+TIMEZONE[key]<0:
				local_time = 24+(hour+TIMEZONE[key])
			else:
				local_time = hour+TIMEZONE[key]
			# new day
			if local_time >= 24:
				local_time-=24
			
			# define the arrival rate and the arrival interval
			avg_hly_cl = avg_dly_cl * TRAFFIC[local_time]
			arrival_rate = avg_hly_cl/3600
			inter_arrival = np.random.poisson(1/arrival_rate)

			yield env.timeout(inter_arrival)
			
			# initialize a new client
			cnt+=1 #client id
			self.cl = Client(env, key, cnt, self.s, self.stat)
			self.s = self.cl.rack_list
			self.stat.n_clients[key]+=1
			
	
	def updateCost(self):
		"""Update the total mantaining cost of the CDN. The total cost is determined as the
		summation of the local cost of the rack. The hourily local cost of a server is stored
		in the lib.config file.
		
		Attributes
		----------
			total_cost : float
				total mantaining cost of the CDN
		
		Returns
		-------
			total_cost : float
				total mantaining cost of the CDN
		
		"""
		self.total_cost = 0
		for country in self.s:
			for server in self.s[country]:
				if not server.inIdle:
					self.total_cost += COSTS[country]
		
		return self.total_cost
	
	
	def getTime(self, now):
		"""Manage the simulation time by turning the seconds into hh:mm:ss format. The 
		starting hour is specified in the lib.config file
	
		Parameters
		----------
			now : int
				seconds lasted from the beginning of the simulation
		
		Attributes
		----------
			H : int
				simulation hours
			M : int
				simulation minutes
			S : int
				simulation seconds
				
		Returns
		-------
			str
				datetime. hh:mm:ss format
				
		"""
		self.H = int(now/3600)
		self.M = int((now - self.H*3600)/60)
		self.S = int((now - self.H*3600 - self.M*60))
		self.H+=START
		if self.H >= 24:
			self.H-=24
				
		if self.H < 10:
			self.H = "0{}".format(self.H)
		if self.M < 10:
			self.M = "0{}".format(self.M)
		if self.S < 10:
			self.S = "0{}".format(self.S)
	
		return "{}:{}:{}".format(self.H,self.M,self.S)


	


