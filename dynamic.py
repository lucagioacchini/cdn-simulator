import matplotlib.pyplot as plt
import numpy as np
import simpy
import math
import sys
import os

from lib.network_dynamic import Network
from lib.stats_dynamic import Stats
from lib.config import*

env = simpy.Environment()
stat = Stats()

if len(sys.argv)!=2:
	print "usage: python dynamic.py <exp>"
	print """
Dynamic server allocation. Three simulation scenarios (exp):
1 - Servers are woken up with respect to the distance
2 - Servers are woken up with respect to the minimum cost
3 - Servers are woken up with respect to the maximum people	
	"""
	exit()
else:
	# CDN initialization
	net = Network(stat, int(sys.argv[1]))

	# Define a process for each country
	for u in COUNTRY:
		env.process(net.arrival(
			env, 
			DAILY_USERS[u], 
			u
		))

	# Sart simulation
	print ("0{}:00:00 - Simulation Started".format(START))
	env.run(until=SIMTIME)
	# Simulation ended
	print "Simulation Ended"
