# python-agentx module
# 
#  Copyright (C) 2010 Bozhin Zafirov, bozhin@abv.bg
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import ctypes, ctypes.util
import time
import signal
import os
import sys

# export names
__all__ = [
	'AgentX',
]

# snmp agentx library
snmp	= None
axl	= None
try:
	snmp	= ctypes.cdll.LoadLibrary(ctypes.util.find_library('netsnmphelpers'))
	axl	= ctypes.cdll.LoadLibrary(ctypes.util.find_library('netsnmpagent'))
except:
	print('ERROR: agentx module requires net-snmp libraries.')
	sys.exit(1)

# constants
NETSNMP_DS_APPLICATION_ID	= 1
NETSNMP_DS_AGENT_ROLE		= 1

# ASN constants
ASN_BOOLEAN			= 0x01
ASN_INTEGER			= 0x02
ASN_BIT_STR			= 0x03
ASN_OCTET_STR			= 0x04
ASN_NULL			= 0x05
ASN_OBJECT_ID			= 0x06
ASN_SEQUENCE			= 0x10
ASN_SET				= 0x11

ASN_UNIVERSAL			= 0x00
ASN_APPLICATION			= 0x40
ASN_CONTEXT			= 0x80
ASN_PRIVATE			= 0xC0

ASN_PRIMITIVE			= 0x00
ASN_CONSTRUCTOR			= 0x20

ASN_LONG_LEN			= 0x80
ASN_EXTENSION_ID		= 0x1F
ASN_BIT8			= 0x80

ASN_UNSIGNED			= ASN_APPLICATION | 0x2
ASN_TIMETICKS			= ASN_APPLICATION | 0x3
ASN_APP_FLOAT			= ASN_APPLICATION | 0x8
ASN_APP_DOUBLE			= ASN_APPLICATION | 0x9

# asn opaque
ASN_OPAQUE_TAG2			= 0x30
ASN_OPAQUE_FLOAT		= ASN_OPAQUE_TAG2 + ASN_APP_FLOAT
ASN_OPAQUE_DOUBLE		= ASN_OPAQUE_TAG2 + ASN_APP_DOUBLE

# handler constants
HANDLER_CAN_GETANDGETNEXT	= 0x01
HANDLER_CAN_SET			= 0x02
HANDLER_CAN_GETBULK		= 0x04
HANDLER_CAN_NOT_CREATE		= 0x08
HANDLER_CAN_BABY_STEP		= 0x10
HANDLER_CAN_STASH		= 0x20

HANDLER_CAN_RONLY		= HANDLER_CAN_GETANDGETNEXT
HANDLER_CAN_RWRITE		= HANDLER_CAN_GETANDGETNEXT | HANDLER_CAN_SET
HANDLER_CAN_SET_ONLY		= HANDLER_CAN_SET | HANDLER_CAN_NOT_CREATE
HANDLER_CAN_DEFAULT		= HANDLER_CAN_RONLY | HANDLER_CAN_NOT_CREATE

SNMP_ERR_NOERROR		= 0
SNMP_ERR_TOOBIG			= 1
SNMP_ERR_NOSUCHNAME		= 2
SNMP_ERR_BADVALUE		= 3
SNMP_ERR_READONLY		= 4
SNMP_ERR_GENERR			= 5

ASN_CONSTRUCTOR			= 0x20

SNMP_MSG_GET			= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x0
SNMP_MSG_GETNEXT		= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x1
SNMP_MSG_RESPONSE		= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x2
SNMP_MSG_SET			= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x3
SNMP_MSG_TRAP			= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x4
SNMP_MSG_GETBULK		= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x5
SNMP_MSG_INFORM			= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x6
SNMP_MSG_TRAP2			= ASN_CONTEXT | ASN_CONSTRUCTOR | 0x7

SNMP_MSG_INTERNAL_SET_BEGIN	= -1
SNMP_MSG_INTERNAL_SET_RESERVE1	= 0
SNMP_MSG_INTERNAL_SET_RESERVE2	= 1
SNMP_MSG_INTERNAL_SET_ACTION	= 2
SNMP_MSG_INTERNAL_SET_COMMIT	= 3
SNMP_MSG_INTERNAL_SET_FREE	= 4
SNMP_MSG_INTERNAL_SET_UNDO	= 5
SNMP_MSG_INTERNAL_SET_MAX	= 6


MAX_OID_LEN			= 128
OID_LEN				= MAX_OID_LEN*2+1

# --- agentx.py constants ---
PAX_RO				= 0x0
PAX_WO				= 0x1
PAX_RW				= 0x2

# --- low level routines ---


# types 
# oid type definition
oid_t = ctypes.c_ulong
oidOID_t = oid_t * MAX_OID_LEN
strOID_t = ctypes.c_char * OID_LEN


# structures

# dummy structures (pointers only)
class netsnmp_mib_handler(ctypes.Structure): pass
class netsnmp_handler_registration(ctypes.Structure): pass
class netsnmp_subtree(ctypes.Structure): pass
class netsnmp_agent_session(ctypes.Structure): pass
class counter64(ctypes.Structure): pass

class netsnmp_vardata(ctypes.Union):
	_fields_ = [
		('integer',		ctypes.POINTER(ctypes.c_long)),
		('string',		ctypes.c_char_p),
		('objid',		ctypes.POINTER(oid_t)),
		('bitstring',		ctypes.POINTER(ctypes.c_ubyte)),
		('counter64',		ctypes.POINTER(counter64)),
		('floatVal',		ctypes.POINTER(ctypes.c_float)),
		('doubleVal',		ctypes.POINTER(ctypes.c_double)),
	]

class netsnmp_variable_list(ctypes.Structure): pass
netsnmp_variable_list._fields_ = [
		('next_variable',	ctypes.POINTER(netsnmp_variable_list)),
		('name',		ctypes.POINTER(oid_t)),
		('name_length',		ctypes.c_size_t),
		('type',		ctypes.c_ubyte),
		('val',			netsnmp_vardata),
		('val_len',		ctypes.c_size_t),
		('name_loc',		oid_t * MAX_OID_LEN),
		('buf',			ctypes.c_ubyte * 40),
		('data',		ctypes.c_void_p),
		('dataFreeHook',	ctypes.c_void_p),
		('index',		ctypes.c_int),
	]
netsnmp_variable_list_p = ctypes.POINTER(netsnmp_variable_list)

class netsnmp_data_list(ctypes.Structure): pass
netsnmp_data_list._fields_ = [
		('next',		ctypes.POINTER(netsnmp_data_list)),
		('name',		ctypes.c_char_p),
		('data',		ctypes.c_void_p),
		('free_func',		ctypes.c_void_p),
	]

class netsnmp_agent_request_info(ctypes.Structure):
	_fields_ = [
		('mode',	ctypes.c_int),
		('asp',		ctypes.POINTER(netsnmp_agent_session)),
		('agent_data',	ctypes.POINTER(netsnmp_data_list)),
	]

class netsnmp_request_info(ctypes.Structure): pass
netsnmp_request_info._fields_ = [
		('requestvb',		ctypes.POINTER(netsnmp_variable_list)),
		('parent_data',		ctypes.POINTER(netsnmp_data_list)),
		('agent_req_info',	ctypes.POINTER(netsnmp_agent_request_info)),
		('range_end',		ctypes.POINTER(oid_t)),
		('range_end_len',	ctypes.c_size_t),
		('delegated',		ctypes.c_int),
		('processed',		ctypes.c_int),
		('inclusive',		ctypes.c_int),
		('status',		ctypes.c_int),
		('index',		ctypes.c_int),
		('repeat',		ctypes.c_int),
		('orig_repeat',		ctypes.c_int),
		('requestvb_start',	ctypes.POINTER(netsnmp_variable_list)),
		('next',		ctypes.POINTER(netsnmp_request_info)),
		('prev',		ctypes.POINTER(netsnmp_request_info)),
		('subtree',		ctypes.POINTER(netsnmp_subtree)),
	]


# various functions argument types
axl.read_objid.argtypes = [ctypes.c_char_p, ctypes.POINTER(oidOID_t), ctypes.POINTER(ctypes.c_size_t)]
axl.snmp_set_var_typed_value.argtypes = [ctypes.POINTER(netsnmp_variable_list), ctypes.c_ubyte, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]
axl.snprint_objid.argtypes = [strOID_t, ctypes.c_int, ctypes.POINTER(oid_t), ctypes.c_int]
axl.snmp_varlist_add_variable.argtypes = [ctypes.POINTER(netsnmp_variable_list_p), ctypes.POINTER(oid_t), ctypes.c_long, ctypes.c_ubyte, ctypes.c_char_p, ctypes.c_long]
axl.send_v2trap.argtypes = [netsnmp_variable_list_p]

# convert text oid to oid list
def ReadOID(TextOID):
	oidOID = oidOID_t()
	oidOID_len = ctypes.c_size_t(MAX_OID_LEN)
	if axl.read_objid(TextOID, ctypes.byref(oidOID), ctypes.byref(oidOID_len)) == 0:
		raise OperationalError('Incorrect OID (%(oid)s)' % { 'oid' : TextOID })
	newOID_t = oid_t * oidOID_len.value
	oid = newOID_t(*oidOID[0:oidOID_len.value])
	return oid

# convert to text oid
def ReadTOID(oid):
	strOID = strOID_t()
	oid_list = map(int, oid.split('.'))
	oid = (oid_t * len(oid_list))( *oid_list )
	axl.snprint_objid(strOID, OID_LEN, oid, len(oid))
	return strOID.value

# exceptions
class OperationalError(Exception): pass


# agentx data object
class AgentXData(dict):
	def __init__(self):
		dict.__init__(self)
		self.ResponseLast	= None
		self.container		= None

	# clear data
	def Clear(self):
		self.clear()
		self.ResponseLast = None

	# register variable
	def RegisterVar(self, oid, value=None):
		# normalize
		oid = self.NormOID(oid)
		if self:
			self[self.ResponseLast]['noid'] = oid
		self.ResponseLast = oid
		self[oid] = { 'value' : value, 'noid' : None }

	# prepare snmp table data
	def Table(self, entry, columns):
		self.RegisterVar('%(TableEntry)s.0'% { 'TableEntry' : entry }, 0)
		for column in columns:
			i = 1
			for value in columns[column]:
				self.RegisterVar('%(ColumnName)s.%(RowId)d'% { 'ColumnName': column, 'RowId': i }, value)
				i += 1

	# get next object id
	def GetNext(self, oid):
		return self[oid]['noid']

	# set value
	def Update(self, oid, value):
		if oid not in self:
			raise OperationalError('No such object registered: %(oid)s' % { 'oid' : oid })
		self[oid]["value"] = value

	# normalize text id
	def NormOID(self, tid):
		if tid.find('::') == -1:
			if not self.container:
				raise OperationalError('OID prefix is not yet available, run ax.Init first.')
			tid = '%(mib)s::%(oid)s' % { 'mib': self.container, 'oid': tid }
		return tid

# forward declaration
AXObject = None

# snmp agentx request object
class RequestObject(object):
	__slots__ = ['oid', 'mode', 'value', 'data', '__ax', '__request', '__reqinfo']
	# class constructor
	def __init__(self, ax, request, reqinfo):
		self.__ax	= ax
		self.__request	= request
		self.__reqinfo	= reqinfo

	# set next object id
	def SetNext(self, objid):
		oidOID = ReadOID(objid)
		axl.snmp_set_var_objid(self.__request.requestvb, oidOID,  len(oidOID))
		self.oid = objid

	# get next objid
	def GetNext(self, oid=None):
		if not oid:
			oid = self.oid
		return self.__ax.AXData.GetNext(oid)

	# set value
	def SetValue(self, value):
		# set object type
		otype = None
		size = 8
		if type(value) == str:
			otype = ASN_OCTET_STR
			size = len(value)
			value = ctypes.c_char_p(value)
		elif type(value) == int:
			otype = ASN_INTEGER
			value = ctypes.pointer(ctypes.c_int(value))
		elif type(value) == float:
			otype = ASN_APP_FLOAT
			value = ctypes.pointer(ctypes.c_float(value))
		axl.snmp_set_var_typed_value(self.__request.requestvb, otype, ctypes.cast(value, ctypes.POINTER(ctypes.c_ubyte)), size)
		self.value = value

	# set error
	def SetError(self, error):
		axl.netsnmp_set_request_error(self.__reqinfo, self.__request, error)

# callback function
HandlerWrapperFunc = ctypes.CFUNCTYPE(
	ctypes.c_int,
	ctypes.POINTER(netsnmp_mib_handler),
	ctypes.POINTER(netsnmp_handler_registration),
	ctypes.POINTER(netsnmp_agent_request_info),
	ctypes.POINTER(netsnmp_request_info)
)
# high level handler
def _handler_wrapper(handler, reginfo, reqinfo, requests):
	r = requests.contents
	# get current time
	timestamp = time.time()
	if AXObject.CacheInterval and timestamp - AXObject.UpdateTime > AXObject.CacheInterval:
		# need to update data now
		AXObject.AXData.Clear()
		AXObject.GlobalsRun('OnUpdate')
		AXObject.UpdateTime = timestamp
	# handler loop
	while True:
		# get object id
		strOID = strOID_t()
		axl.snprint_objid(strOID, OID_LEN, r.requestvb.contents.name, r.requestvb.contents.name_length)

		# do some magic here
		req = RequestObject(AXObject, r, reqinfo)
		req.oid = strOID.value
		# python 3.x stores oid in bytes object
		if type(req.oid) != str:
			req.oid = req.oid.decode()
		req.mode = reqinfo.contents.mode

		if req.mode == SNMP_MSG_GET:
			if req.oid in AXObject.AXData:
				req.SetValue(AXObject.AXData[req.oid]['value'])
				# run read-write and read-only handlers
				for handler in AXObject.RequestHandlers[PAX_RW] + AXObject.RequestHandlers[PAX_RO]:
					value = handler(req, AXObject, AXObject.AXData)
					if value:
						req.SetValue(value)
		elif req.mode == SNMP_MSG_GETNEXT:
			if req.oid in AXObject.AXData:
				if AXObject.AXData[req.oid]['noid'] is None:
					# only set current objid
					req.SetNext(req.oid)
				else:
					# req.SetNext changes req.oid value
					req.SetNext(AXObject.AXData[req.oid]['noid'])
					req.SetValue(AXObject.AXData[req.oid]['value'])
					# run read-write and read-only handlers
					for handler in AXObject.RequestHandlers[PAX_RW] + AXObject.RequestHandlers[PAX_RO]:
						value = handler(req, AXObject, AXObject.AXData)
						if value:
							req.SetValue(value)
		elif req.mode == SNMP_MSG_INTERNAL_SET_COMMIT:
			# FIXME: MAX-ACCESS is now ignored :(
			if r.requestvb.contents.type in (ASN_INTEGER, ASN_UNSIGNED):
				req.value = r.requestvb.contents.val.integer.contents.value
			elif r.requestvb.contents.type == ASN_OCTET_STR:
				req.value = r.requestvb.contents.val.string
			elif r.requestvb.contents.type in (ASN_OPAQUE_FLOAT, ASN_OPAQUE_DOUBLE):
				req.value = r.requestvb.contents.val.floatVal.contents.value
			# check special case oids
			if AXObject.ReloadOID and AXObject.ReloadOID == req.oid and req.value == 1:
				# reload requested by snmp
				AXObject.GlobalsRun('OnReload')
			if AXObject.StopOID and AXObject.StopOID == req.oid and req.value == 1:
				# stop agent
				AXObject.Shutdown()
			# run read-write and write-only handlers
			for handler in AXObject.RequestHandlers[PAX_RW] + AXObject.RequestHandlers[PAX_WO]:
				value = handler(req, AXObject, AXObject.AXData)
				if value:
					req.value = value
			# save value
			try:
				AXObject.AXData.Update(req.oid, req.value)
			except OperationalError:
				AXObject.AXData.RegisterVar(req.oid, req.value)
		if not r.next:
			break
		r = r.next.contents
	return SNMP_ERR_NOERROR
# low level handler
handler_wrapper = HandlerWrapperFunc(_handler_wrapper)


# AgentX object declaration
class AgentX(object):
	def __init__(self, Globals, **args):
		self.alarm	= 0
		self.loop	= False
		self.AXData	= AgentXData()
		self.Globals	= Globals
		self.UpdateTime	= 0

		# save global constants in object's namespace
		for c in globals():
			for prefix in ('ASN_', 'SNMP_', 'HANDLER_', 'PAX_'):
				if c.startswith(prefix):
					setattr(self, c, globals()[c])
					break

		# default settings
		defaults = {
			'Name'			: os.path.splitext(os.path.basename(sys.argv[0]))[0],
			'CacheInterval'		: 30,
			'TimerInterval'		: 30,
			'Master'		: False,
			'MIBFile'		: (),
			'RootOID'		: None,
			'ReloadOID'		: None,
			'StopOID'		: None,
		}

		# initialize variables
		for key in defaults:
			setattr(self, key, args.get(key, defaults[key]))

		# request handlers
		self.RequestHandlers = {
			PAX_RO	: [],
			PAX_WO	: [],
			PAX_RW	: [],
		}

		# set global object reference
		global AXObject
		AXObject = self

		# initialize agentx
		# setup log facility
		axl.snmp_enable_stderrlog()
		if not self.Master:
			axl.netsnmp_ds_set_boolean(NETSNMP_DS_APPLICATION_ID, NETSNMP_DS_AGENT_ROLE, 1)
		# init agent module
		# for win32: winsock_startup()
		axl.init_agent(self.Name)
		axl.init_snmp(self.Name)
		# register agent
		if not type(self.MIBFile) in (list, tuple):
			self.MIBFile = (self.MIBFile,)
		for mib in self.MIBFile:
			axl.read_mib(mib)

		# install low level handler
		if self.RootOID:
			self.AXData.container = self.RootOID.split('::', 1)[0]
			# register handler callback
			oidOID = ReadOID(self.RootOID)

			axl.netsnmp_create_handler_registration.restype = ctypes.POINTER(netsnmp_handler_registration)
			h = axl.netsnmp_create_handler_registration(
				self.Name,
				handler_wrapper,
				oidOID, len(oidOID),
				HANDLER_CAN_RWRITE,
			)
			if axl.netsnmp_register_handler(h) != 0:
				raise OperationalError('SNMP handler registration failure.')
		# register custom handlers
		for HandlerName, HandlerMode in (('OnSnmpRequest', PAX_RW), ('OnSnmpRead', PAX_RO), ('OnSnmpWrite', PAX_WO)):
			if HandlerName in self.Globals and '__call__' in dir(self.Globals[HandlerName]):
				self.RegisterHandler(self.Globals[HandlerName], HandlerMode)
		# ReloadOID and StopOID
		if self.ReloadOID:
			self.ReloadOID = self.AXData.NormOID(self.ReloadOID)
		if self.StopOID:
			self.StopOID = self.AXData.NormOID(self.StopOID)

		# attach HUP signal
		def HupHandler(signum, frame):
			# reload requested by HUP signal
			self.GlobalsRun('OnReload')
		signal.signal(signal.SIGHUP, HupHandler)

		# run custom init routine
		self.GlobalsRun('OnInit')
		if not self.loop:
			# start timer
			self.TimerStart(self.TimerInterval)
			self.loop = True
			while self.loop:
				self.GlobalsRun('OnTimer')
				self.Process()


	# register custom handler
	def RegisterHandler(self, handler, mode=PAX_RW):
		assert '__call__' in dir(handler), 'Callable object is required'
		self.RequestHandlers[mode].append(handler)

	# start itimer
	def TimerStart(self, interval):
		try:
			signal.setitimer(signal.ITIMER_REAL, interval, interval)
		except:
			# fallback to alarm clock which is more inacurate
			self.alarm = int(interval)
			if not self.alarm:
				self.alarm = 1
			return self.alarm
		return interval

	# stop alarm timer
	def TimerStop(self):
		try:
			signal.setitimer(signal.ITIMER_REAL, 0)
		except:
			self.alarm = 0

	# process snmp requests
	def Process(self, block=True):
		alarm_triggered = False
		loop = True
		result = True

		if self.alarm:
			# start alarm
			signal.alarm(self.alarm)
			block = True

		# alarm handler
		def sigalrm_handler(signum, frame):
			alarm_triggered = True

		# attach alarm signal handler
		signal.signal(signal.SIGALRM, sigalrm_handler)

		# process loop
		while loop and self.loop:
			r = axl.agent_check_and_process(block)
			if r == -1:
				if not alarm_triggered:
					result = False
				loop = False
			elif r == 0 and not block:
				loop = False

		# detach alarm signal
		signal.signal(signal.SIGALRM, signal.SIG_DFL)
		# stop alarm timer
		if self.alarm:
			signal.alarm(0)
		return result

	# run globals routine
	def GlobalsRun(self, name, *args):
		if name in self.Globals and '__call__' in dir(self.Globals[name]):
			# call 
			if args:
				self.Globals[name](self, self.AXData, *args)
			else:
				self.Globals[name](self, self.AXData)

	# end main loop
	def Shutdown(self):
		self.loop = False

	# send trap from within agentx module
	def Trap(self, oid, *args):
		sysUpTimeOID	= (oid_t * 9) (1, 3, 6, 1, 2, 1, 1, 3, 0)		# sysUpTimeInstance
		snmpTrapOID	= (oid_t * 11) (1, 3, 6, 1, 6, 3, 1, 1, 4, 1, 0)	# snmpTrapOID.0
		TrapOID		= ReadOID(self.AXData.NormOID(oid))

		TrapVars = netsnmp_variable_list_p()
		uptime = ctypes.c_long(axl.netsnmp_get_agent_uptime())

		# agent uptime
		axl.snmp_varlist_add_variable(
			ctypes.byref(TrapVars),
			ctypes.cast(ctypes.byref(sysUpTimeOID), ctypes.POINTER(oid_t)), len(sysUpTimeOID),
			ASN_TIMETICKS,
			ctypes.cast(ctypes.byref(uptime), ctypes.c_char_p), ctypes.sizeof(uptime),
		)

		# agent trap
		axl.snmp_varlist_add_variable(
			ctypes.byref(TrapVars),
			ctypes.cast(ctypes.byref(snmpTrapOID), ctypes.POINTER(oid_t)), len(snmpTrapOID),
			ASN_OBJECT_ID,
			ctypes.cast(ctypes.byref(TrapOID), ctypes.c_char_p), len(TrapOID)*ctypes.sizeof(oid_t),
		)

		# add variable
		for ArgOID, ArgData in args:
			ArgOID = ReadOID(
				self.AXData.NormOID(ArgOID)
			)

			ArgDataLen = 0
			ObjType = None
			if type(ArgData) == str:
				ObjType		= ASN_OCTET_STR
				ArgDataLen	= len(ArgData)
				ArgData		= ctypes.c_char_p(ArgData)
			elif type(ArgData) == int:
				ObjType		= ASN_INTEGER
				ArgData		= ctypes.c_int(ArgData)
				ArgDataLen	= ctypes.sizeof(ArgData)
				ArgData		= ctypes.cast(ctypes.byref(ArgData), ctypes.c_char_p)
			elif type(ArgData) == float:
				ObjType		= ASN_APP_FLOAT
				ArgData		= ctypes.c_float(ArgData)
				ArgDataLen	= ctypes.sizeof(ArgData)
				ArgData		= ctypes.cast(ctypes.byref(ArgData), ctypes.c_char_p)

			# add variable
			axl.snmp_varlist_add_variable(
				ctypes.byref(TrapVars),
				ctypes.cast(ctypes.byref(ArgOID), ctypes.POINTER(oid_t)), len(ArgOID),
				ObjType,
				ctypes.cast(ArgData, ctypes.c_char_p), ArgDataLen,
			)

		# send trap
		axl.send_v2trap(TrapVars)
		axl.snmp_free_varbind(TrapVars)
