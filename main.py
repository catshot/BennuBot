import threading, time, socket, re
from datetime import date
#TODO Garbage collection for unused "outMSG" data.
#TODO Permissions instead of just admins
#TODO Remote plugin loading (via plugin)
#TODO Alternative hash authentication
#TODO Ability to shutdown bot (via plugin)
#TODO Store things into a database accessable by plugins
#TODO Add things to send queue via function (Ex: sendMSG(outMSG))
#TODO Pass sendqueue messages to gen plugins before queuing them (via thread ofc)

#These will be loaded from protoFolder and plugFolder respectively.
protoList = ['irc.py'] #Protocols to be loaded
plugList  = ['say.py', 'pyexec.py', 'irc_commands.py', 'time.py'] #Plugins to be loaded

protoFolder = 'protocols/'
plugFolder   = 'plugins/'

nick = 'BennuBot'

quiet = True
funcPrefix = '.'
protoPrefix = ';'

admins = {}
funcs = {}
genFuncs = []
protocols = {}

plugName = None
load = None
plugAdmins = None

#MSG, Protocol, Server, Channel, Nick, UID (May be "None")
inMSG = []
#MSG, Protocol, Server, Channel (May be "None")
outMSG = []

change = False

#TODO Optional print?
def log(text):
	msg = time.strftime('%Y-%m-%d %H:%M:%S') + '\t' + text
	try: print msg
	except: None
	open('log', 'a').write(msg + '\r\n')

def loadProtocol(location, name):
	global protocols, plugName, load, plugAdmins, admins
	plugName = None
	load = None
	plugAdmins = None
	try:
		eval(compile(open(location, 'U').read(), name, 'exec'), globals())
		if plugName: name = plugName
		if not load:
			log('Protocol \"' + name + '\" must define \'load\'.')
			return False
		protocols = dict(protocols.items() + load().items())
	except:
		log('Protocol \"' + name + '\" failed to load.')
		return False
	try:
		admins = dict(admins.items() + plugAdmins.items())
	except:
		log('Protocol \"' + name + '\" has not specified any admins.')
	log('Protocol \"' + name + '\" loaded.')
	return True	

#Load all protocols from "protoList".
def loadProtocols():
	global protocols
	protocols = {}
	for i in protoList:
		loadProtocol(protoFolder + i, i)

def loadPlugin(location, name):
	global funcs, genFuncs, plugName, load
	plugName = None
	load = None
	try:
		eval(compile(open(location, 'U').read(), name, 'exec'), globals())
		if plugName: name = plugName
		if not load:
			log('Plugin \"' + name + '\" must define \'load\'.')
			return False
		plugin = load()
		if type(plugin).__name__ == 'dict':
			funcs = dict(funcs.items() + plugin.items())
		elif type(plugin).__name__ == 'function':
			genFuncs += [plugin]
		else:
			log('Plugin \"' + name + '\" must return \'dict\' or \'function\'.')
			return False
	except:
		log('Plugin \"' + name + '\" failed to load.')
		return False

	log('Plugin \"' + name + '\" loaded.')
	return True		

#Load all plugins from "plugList".
def loadPlugins():
	global funcs, genFuncs
	funcs = {}
	genFuncs = []
	for i in plugList:
		loadPlugin(plugFolder + i, i)

def isAdmin(inMSG):
	try:
		for i in admins[inMSG[1]]:
			if re.search(re.sub('\\\\\\*', '.*', re.escape(i)), inMSG[5]):
				return True
	except:
		return False
	return False

#Handles general plugins
class handleGenFunc(threading.Thread):

	def __init__(self, command=None):
		self.command = command
		threading.Thread.__init__(self)

	def run(self):
		global outMSG
		for i in genFuncs:
			try:
				i(self.command)
			except:
				#TODO Output function name which had the error.
				outMSG.append(['A plugin had an error.', self.command[1], self.command[2],
						self.command[3]])		

#Parses a command.
class parseCommand(threading.Thread):

	def __init__(self, command):
		self.command = command
		threading.Thread.__init__(self)

	def run(self):
		global outMSG
		if len(self.command[0]) > 1 and self.command[0][0] == funcPrefix:
			try:
				funcs[self.command[0].split(None, 1)[0][len(funcPrefix):].lower()](
					self.command)
			except:
				if not quiet:
					outMSG.append(['Invalid command.', self.command[1], self.command[2],
						self.command[3]])
		elif len(self.command[0]) > 1 and self.command[0][0] == protoPrefix:
			if not isAdmin(self.command):
				if not quiet:
					outMSG.append(['Not authorized.', self.command[1], self.command[2],
							self.command[3]])
				return
			try:
				protocols[self.command[0].split(None, 1)[0][len(protoPrefix):].lower()](
					self.command)
			except:
				if not quiet:
					outMSG.append(['Invalid command.', self.command[1], self.command[2],
						self.command[3]])

log('Loading Protocols...')
loadProtocols()
log('Loading Plugins...')
loadPlugins()
log('Entering main loop...')

while True:
	if not change:
		#General plugins should prepare for "None".
		handleGenFunc().start()
		#As long as plugins are handling their timeouts properly 10ms should be plenty.
		time.sleep(0.01)
	else:
		change = False
	for i in inMSG:
		if not change: change = True
		parseCommand(i).start()
		handleGenFunc(i).start()
		del inMSG[0]
