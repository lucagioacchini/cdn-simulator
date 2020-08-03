import numpy as np

# Random seed used in all the codes
SEED = 126

# Starting hour of the simulation. 
# e.g. if the simulation starts at 00:00, START = 0
# The hours are in the '24' hours format.
START = 0

# Interval of acquisition expressed in minutes
INTERACQ = 20

# Seconds of simulation
SIMTIME = 129600

# Server's capacity in bits
CAPACITY = 1e10

# The server's capacity is limited to avoid its saturation
# SERVER_LIMIT/100 [%], so the 80% is SERVER_LIMIT = .8
# This variable is used only in the fixed number of server simulator
SERVER_LIMIT = .8

# Threshold values for low traffic (L) and high traffic (H). See the 
# dynamic codes in the 'lib' folder.
# These variables are used only in the dynamic server allocation simulator
MAX_L = .3*CAPACITY
MIN_L = .95*CAPACITY
CANIDLE_L = .93*CAPACITY

MAX_H = .50*CAPACITY
MIN_H = .95*CAPACITY
CANIDLE_H = .50*CAPACITY

# List of countries in which the servers are deployed
COUNTRY = ['China','India','USA','Brazil','Japan']

# Distances matrix used to estimate the request service time and
# for the routing strategy. The distance is expressed in km
# The rows and colums order is:
# China, India, USA, Brazil, Japan
DISTANCES = np.array([
	[0, 2983.65, 11646.7, 16632.05, 3046.61],
	[2983.65, 0, 13576.02, 14774.6, 5959.02],
	[11646.7, 13576.02, 0, 7316.57, 10149.95],
	[16632.05, 14774.6, 7316.57, 0, 17369.59],
	[3046.61, 5959.02, 10149.95, 17369.59, 0]
])

# Only a small percentage the daily internet users per country uses the CDN.
# CONV/100 [%], so the 0.1% of the people is CONV = 1e-3 
CONV = 1e-3 
DAILY_USERS = {
	'China':int(829367947*CONV),
	'India':int(560347554*CONV),
	'USA':int(292090854*CONV),
	'Brazil':int(149206801*CONV),
	'Japan':int(118845120*CONV)
}

# Requests size: [4MB, 40MB]
MIN_REQ = 3.2e7
MAX_REQ = 3.2e8

# Servers's local mantaining cost per hour [USD]
COSTS={
	'China':0.2336,
	'India':0.1792,
	'USA':0.1984,
	'Brazil':0.2688,
	'Japan':0.2176
}

# Starting servers rack for the fixed number of servers simulator
SERVERS_STA = 1

# Number of deployed servers per country
SERVERS_DYN = {
	'China':15,
	'India':15,
	'USA':15,
	'Brazil':15,
	'Japan':15
}

# Starting active servers for the dynamic server allocation
START_ACTIVE = {
	'China':6,
	'India':4,
	'USA':2,
	'Brazil':2,
	'Japan':2
}

# Minimum number of active servers for the dynamic server allocation
MIN_ACTIVE = {
	'Brazil':2,
	'India':4,
	'USA':2,
	'Japan':2,
	'China':5
}

# Hourly traffic
TRAFFIC = [
	0.37/100,
	0.37/100,
	0.37/100,
	0.37/100,
	0.23/100,
	0.23/100,
	0.23/100,
	4.84/100,
	4.64/100,
	5.56/100,
	7.9/100,
	8.34/100,
	7.9/100,
	7.41/100,
	9.28/100,
	11.12/100,
	9.74/100,
	8.8/100,
	7.41/100,
	2.32/100,
	1.39/100,
	0.46/100,
	0.46/100,
	0.46/100
]

# Countries timezone
TIMEZONE = {
	'Brazil':-5,
	'India':3,
	'USA':-6,
	'Japan':7,
	'China':6
}
