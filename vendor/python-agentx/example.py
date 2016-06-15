#!/usr/bin/python3
from agentx import AgentX
import time

## handle get and getnext requests
def OnSnmpRead(req, ax, axd):
	## request object methods:
	##   SetValue(value) -- set value to return (MODE_GET, MODE_GETNEXT)
	##   SetNext(oid)    -- set next object id
	##   SetError(error) -- set error, error is integer value
	##
	## request object members:
	##   oid   -- object id
	##   mode  -- request mode (MODE_GET, MODE_GETNEXT, MODE_SET_COMMIT, etc.)
	##   value -- new value for MODE_SET_*

	## new values set in handler have higher priority than those registered
	if req.oid == 'PAX-TUTORIAL-MIB::paxModuleIntVarRO.24':
		return 8851
	if req.oid == 'PAX-TUTORIAL-MIB::paxTableValue.3':
		return 'ten'

# handle set requests
def OnSnmpWrite(req, ax, axd):
	pass

# handle get, getnext and set requests
def OnSnmpRequest(req, ax, axd):
	pass

## initialize any ax and axd dependant code here
def OnInit(ax, axd):
	## register custom handler
	#ax.RegisterHandler(CustomRequestHandler, ax.PAX_RO)
	## handlers can be:
	##   PAX_RO read-only  (snmp get requests)
	##   PAX_WO write-only (snmp set requests)
	##   PAX_RW read-write (both, default if omited)
	pass

## register some variables
## this function is called when a new snmp request has been received and
## if CacheInterval has expired at that time
def OnUpdate(ax, axd):
	## ax is the agentx object
	## axd is reference to AXData
	## print "status line"
	print('OnUpdate: {0}'.format(time.time()))
	## register variables
	axd.RegisterVar('PAX-TUTORIAL-MIB::paxAgentData', 0)
	## NOTE: RegisterVar will automatically prefix variable name with PAX-TUTORIAL-MIB:: if necessary
	for i in range(0, 55):
		axd.RegisterVar(
			'paxModuleIntVarRO.%(id)d' % { 'id' :  i },		# oid 
			i * 7,							# value
		)

	axd.RegisterVar(
		'paxModuleIntVar',
		int(time.time())
	)
	axd.RegisterVar(
		'paxModuleStrVar',
		'python-agentx, v0.8'
	)

	## register example table
	axd.Table(
		'paxTableEntry',
		{
			'paxTableKey'		: [1, 3, 10, 15],
			'paxTableValue'		: ['one', 'three', 'hundred', 'fifteen'],
		}
	)

	# send trap
	if True:
		ax.Trap(
			# trap oid
			'PAX-TUTORIAL-MIB::paxModuleTrap',
			# trap variables
			('PAX-TUTORIAL-MIB::paxModuleIntVar', 5),
			('PAX-TUTORIAL-MIB::paxModuleStrVar', 'Trap Variable'),
		)

## this function is called on regulary every TimerInterval seconds.
## it may be used to update axd data, but the correct way to do this is to use OnUpdate function
## also have in mind that if axd data is updated here, axd.Clear() must be called first
def OnTimer(ax, axd):
	print('OnTimer: {0}'.format(time.time()))

# this is called on HUP signal or when a ReloadOID object is set to 1 (see below)
def OnReload(ax, axd):
	print('Reload Configuration')

# main program
if __name__ == '__main__':
	## initialize agentx module and run main loop
	AgentX(
		globals(),				# always start with this or a dict with reference to global functions (see above)
		Name		= 'test_agent',		# defaults to file name (without path and extension)
		#Master		= True,			
		MIBFile		= '/usr/share/snmp/mibs/PAX-TUTORIAL-MIB.mib',
		RootOID		= 'PAX-TUTORIAL-MIB::paxData',
		TimerInterval	= 3.2,			# time interval in seconds to run OnTimer function; defaults to 30
		CacheInterval	= 5.8,			# time interval in seconds to cache data before OnUpdate is called; defaults to 30
		## send 1 to this OIDs (must be defined as integers in MIB file) to cause module to reload or shutdown
		ReloadOID	= 'paxReload',
		StopOID		= 'paxShutdown',
	)
	print('Shutdown by request')

## the following lines give an example how to retrieve agent data
##   snmpwalk -v2c -c public localhost PAX-TUTORIAL-MIB::paxAgentData
##   snmptable -v2c -c public localhost PAX-TUTORIAL-MIB::paxTable

## to stop the agent it is sufficient to send 1 to the registered StopOID:
##   snmpset -v2c -c public localhost PAX-TUTORIAL-MIB::paxShutdown i 1

## to reload agent it is first necessary to define a Reload function that does
## the work and then send a ReloadOID with value of 1:
##   snmpset -v2c -c public localhost PAX-TUTORIAL-MIB::paxReload i 1
