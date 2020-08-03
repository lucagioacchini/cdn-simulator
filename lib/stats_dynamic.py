import pandas as pd
from config import *

class Stats():
	"""Create a .csv dataframe to analyze the simulation performances and results.
	
	Attributes
	----------
		n_clients : dict
			number of clients entering the system
		n_req : int
			number of generated requests
		local_req : int
			number of locally served requests 
		local_req_perc : flaot
			percentage of locally serverd requests
		sess_time : list
			when a client finishes its requests its session time is appended to the list
		avg_sess_time : float
			average session time of the clients. The value is updated every 30 minutes
		data : dict
			dataframe
		index : list
			dataframe row names
			
	Methods
	-------
		estimateSessionTime(time)
			estimate the client session time
		avgSessionTime()
			determine the average session time
		nOfReq()
			count the number of generated requests
		localReq()
			count the number of locally served requests and its percentage
		singActive(serv):
			count the number of active servers in each country.
		nActive(s):
			count the total number of active servers in the CDN.
		avgAvailCapacity(s):
			determine the average available capacity of all the active servers in the CDN.
		createDF(self, now, avg, req, cost, 
			act_ch, act_ja,	act_br, act_us, act_in, tot_act, exp
		)
			save the dataframe to a .csv file
			
	"""
	def __init__(self):
		self.n_clients = {
			'China':0,
			'India':0,
			'USA':0,
			'Brazil':0,
			'Japan':0
		}
		self.n_req = 0
		self.local_req = 0
		self.local_req_perc = 0
		self.sess_time = []
		self.avg_sess_time = 0
		self.data = {
			'avg.sess.time':[], 
			'local.req':[], 
			'tot.cost':[], 
			'tot.act.s.':[],
			'China.act.s.':[],
			'USA.act.s.':[],
			'Brazil.act.s.':[],
			'Japan.act.s.':[],
			'India.act.s.':[],
			'China.cl':[],
			'India.cl':[],
			'USA.cl':[],
			'Brazil.cl':[],
			'Japan.cl':[],
			'tot.cl':[]
		}
		self.index = []

	
	def estimateSessionTime(self, time):
		"""Estimate the client session time.
		
		Parameters
		----------
			time : float
				session time of the clients
				
		"""
		self.sess_time.append(time)
	
	
	def avgSessionTime(self):
		"""Determine the average session time.
		
		"""
		self.avg_sess_time = (sum(self.sess_time))/len(self.sess_time)
		self.sess_time = []
	
	
	def nOfReq(self):
		"""Count the number of generated requests.
		
		"""
		self.n_req+=1
	
	
	def localReq(self):
		"""Count the number of locally served requests and its percentage.
		
		"""
		self.local_req+=1
		self.local_req_perc = 100*self.local_req/self.n_req
		
	def singActive(self,serv):
		"""Count the number of active servers in each country.
		
		Parameters
		----------
			serv : list
				list of all the deployed servers in a specific country
		
		"""
		self.n_active = 0
		for server in serv:
			if not server.inIdle and not server.completing:
				self.n_active+=1
		return self.n_active
	
	def nActive(self, s):
		"""Count the total number of active servers in the CDN.
		
		Parameters
		----------
			s : dict
				informations of the servers with respect to the country
			
		"""
		self.n_active = 0
		for country in s:
			for server in s[country]:
				if not server.inIdle and not server.completing:
					self.n_active+=1
		return self.n_active
	
	def avgAvailCapacity(self, s):
		"""Determine the average available capacity of all the active servers in the CDN.
		
		Parameters
		----------
			s : dict
				list of servers deployed in each country
				
		"""
		self.avg_cap = 0.0
		for country in s:
			for server in s[country]:
				if not server.inIdle and not server.completing:
					self.avg_cap += server.available_capacity
					self.n_active+=1
		return self.avg_cap/self.n_active
		
	def createDF(self, now, avg, req, cost, 
			act_ch, act_ja,	act_br, act_us, act_in, tot_act, exp
		):
		"""Save the dataframe to a .csv file.
		
		Parameters
		----------
			now : str
				simulated time
			avg : float
				average session time
			req : float
				percentage of locally served requests
			cost : float
				total mantaining cost of the CDN
			act_ch : int
				total number active servers in China
			act_ja : int
				total number active servers in Japan
			act_br : int
				total number active servers in Brazil
			act_us : int
				total number active servers in USA
			act_in : int
				total number active servers in India
			tot_act : int
				total number active servers
			exp : int
				wake up strategy identification number
		
		"""
		tot_cl = 0
		self.index.append(now)
		self.data["avg.sess.time"].append(avg)
		self.data["local.req"].append(req)
		self.data["tot.cost"].append(cost)
		self.data["China.act.s."].append(act_ch)
		self.data["USA.act.s."].append(act_us)
		self.data["India.act.s."].append(act_in)
		self.data["Brazil.act.s."].append(act_br)
		self.data["Japan.act.s."].append(act_ja)
		self.data["tot.act.s."].append(tot_act)
		for country in COUNTRY:
			self.data['{}.cl'.format(country)].append(self.n_clients[country])
			tot_cl+=self.n_clients[country]
			self.n_clients[country]=0
		self.data['tot.cl'].append(tot_cl)
		
		# creates pandas DataFrame. 
		df = pd.DataFrame(self.data, self.index) 
		# export data
		df.to_csv("output/2_dynamic0{}.csv".format(exp))
