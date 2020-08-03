import pandas as pd
from config import *

class Stats():
	"""Create a .csv dataframe to analyze the simulation performances and results.
	
	Attributes
	----------
		n_clients : dict
			number of clients entering the system per country
		n_req : int
			number of generated requests
		local_req : int
			number of locally served requests 
		local_req_perc : float
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
		nServers(s)
			count the total number of servers in the CDN
		createDF(now, avg, req, cost, serv, exp)
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
			'range':[],
			'China.cl':[],
			'India.cl':[],
			'USA.cl':[],
			'Brazil.cl':[],
			'Japan.cl':[], 
			'avg.sess.time':[], 
			'local.req':[], 
			'tot.cost':[], 
			'tot.servers':[],
			'China.servers':[],
			'USA.servers':[],
			'Brazil.servers':[],
			'Japan.servers':[],
			'India.servers':[],
			'tot.cl':[]
		}
		self.index = []
		self.idx_cnt = 0
	
				
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
	
	
	def nServers(self, s):
		"""Count the total number of servers in the CDN.
		
		Parameters
		----------
			s : dict
				informations of the servers with respect to the country
			
		"""
		self.n_server = 0
		for country in s:
			self.n_server += len(s[country])
			self.data[country+'.servers'].append(len(s[country]))
		return self.n_server
	
	
	def createDF(self, now, avg, req, cost, serv, exp):
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
			serv : int
				total number of servers
			exp : int
				new servers deployment strategy identification number
		
		"""
		self.index.append(now)
		self.data["range"].append(self.idx_cnt)
		self.data["avg.sess.time"].append(avg)
		self.data["local.req"].append(req)
		self.data["tot.cost"].append(cost)
		self.data["tot.servers"].append(serv)
		tot_cl = 0
		for country in COUNTRY:
			self.data['{}.cl'.format(country)].append(self.n_clients[country])
			tot_cl+=self.n_clients[country]
			self.n_clients[country]=0
		self.data['tot.cl'].append(tot_cl)
		self.idx_cnt+=1
		# creates pandas DataFrame. 
		df = pd.DataFrame(self.data, self.index) 
		# export data
		df.to_csv("output/2_static0{}.csv".format(exp))
