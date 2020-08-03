import matplotlib.pyplot as plt
import numpy as np
import simpy
import math
import sys
import os

from lib.network_static import Network
from lib.stats_static import Stats
from lib.config import*

env = simpy.Environment()
stat = Stats()

if len(sys.argv)!=2:
	print "usage: python static.py <exp>"
	print """
Fixed number of servers. Three simulation scenarios (exp):
1 - New servers are added with respect to the distance
2 - New servers are added with respect to the minimum cost
3 - New servers are added with respect to the maximum people	
	"""
	exit()
else:
	# CDN initialization
	net = Network(stat)

	# Define a process for each country
	for u in COUNTRY:
		env.process(net.arrival(
			env, 
			DAILY_USERS[u], 
			u, 
			int(sys.argv[1])
		))

	# Sart simulation
	print "0{}:00:00 - Simulation Started".format(START)
	env.run(until=SIMTIME)
	# Simulation ended
	print "Simulation Ended"
