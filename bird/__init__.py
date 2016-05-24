import commands
import socket
import threading
import time
import re

from bird.agentx	import ax, axd

from pprint import pprint

state = {
	"idle":			1,
	"connect":		2,
	"active":		3,
	"opensent":		4,
	"openconfirm":	5,
	"established":	6,
}

fsm_errors = {
	1: { "Message Header Error": {
		1: "Connection Not Synchronized",
		2: "Bad Message Length",
		3: "Bad Message Type"
	}},
	2: { "OPEN Message Error": {
		1: "Unsupported Version Number",
		2: "Bad Peer AS",
		3: "Bad BGP Identifier",
		4: "Unsupported Optional Parameter",
		5: "Deprecated",
		6: "Unacceptable Hold Time",
	}},
	3: { "UPDATE Message Error": {
		1:  "Malformed Attribute List",
		2:  "Unrecognized Well-known Attribute",
		3:  "Missing Well-known Attribute",
		4:  "Attribute Flags Error",
		5:  "Attribute Length Error",
		6:  "Invalid ORIGIN Attribute",
		7:  "Deprecated",
		8:  "Invalid NEXT_HOP Attribute",
		9:  "Optional Attribute Error",
		10: "Invalid Network Field",
		11: "Malformed AS_PATH",
	}},
	4: { "Hold Timer Expired": {} },
	5: { "Finite State Machine Error": {} },
	6: { "Cease": {} },
}


class BirdConfig(threading.Thread):
	_cfg = {}
	_re_proto_begin = re.compile("^protocol bgp ([a-zA-Z0-9_]+) \{$")
	_re_proto_end = re.compile("^\}$")

	_re_local_as = re.compile("local as ([0-9]+);")
	_re_remote_peer = re.compile("neighbor ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) as ([0-9]+);")
	_re_bgp_begin = re.compile("([a-zA-Z0-9_]+) *BGP * [a-zA-Z0-9]+ * [a-zA-Z0-9]+ * ([a-zA-Z0-9:]+) *")
	_re_bgp_end = re.compile("^$")
	_re_peer = {
		"bgpPeerIdentifier": re.compile("Neighbor ID:.* ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"),
		"bgpPeerState": re.compile("BGP state:.* ([a-zA-Z]+)"),
		"bgpPeerLocalAddr": re.compile("Source address:.* ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"),
		"bgpPeerRemoteAddr": re.compile("Neighbor address:.* ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"),
		"bgpPeerRemoteAs": re.compile("Neighbor AS:.* ([0-9]+)"),
		"bgpPeerInUpdates": re.compile("Import updates:\ +([0-9]+) .*[0-9\-]+.*[0-9\-]+.*[0-9\-]+.*[0-9\-]+"),
		"bgpPeerOutUpdates": re.compile("Export updates:\ +([0-9]+) .*[0-9\-]+.*[0-9\-]+.*[0-9\-]+.*[0-9\-]+"),
		"bgpPeerHoldTime": re.compile("Hold timer:.* ([0-9]+)/[0-9]+"),
		"bgpPeerHoldTimeConfigured": re.compile("Hold timer:.* [0-9]+/([0-9]+)"),
		"bgpPeerKeepAlive": re.compile("Keepalive timer:.* ([0-9]+)/[0-9]+"),
		"bgpPeerKeepAliveConfigured": re.compile("Keepalive timer:.* [0-9]+/([0-9]+)"),
		"bgpPeerLastError": re.compile("Last error:\ +[a-zA-Z0-9-_\ ]+$")
	}

	_c2a = {
		"bgpPeerInUpdates":					"c",
		"bgpPeerOutUpdates":				"c",
		"bgpPeerInTotalMessages":			"c",
		"bgpPeerOutTotalMessages":			"c",
		"bgpPeerLastError":					"o",
		"bgpPeerFsmEstablishedTransitions":	"g",
		"bgpPeerFsmEstablishedTime":		"g",
		"bgpPeerInUpdateElapsedTime":		"g",
	}

	def __init__(self, cfgfile, cli):
		self.cfgfile = cfgfile
		self.cli = cli
		self.fetch_cfg()
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.start()

	def __getitem__(self, key):
		try: return self._cfg[key]
		except: return None

	def get_all_peers(self):
		tmp = {}
		peers = []
		for peer in self._cfg.keys():
			if peer == "bgpLocalAs": continue
			tmp[socket.inet_aton(peer)] = peer
		tmp_k = tmp.keys()
		tmp_k.sort()
		for aton in tmp_k:
			peers.append(tmp[aton])
		return peers

	def _get_values(self):
		cfg = {}
		proto = None
		for line in open(self.cfgfile, "r").readlines():
			match = self._re_proto_begin.search(line)
			if match:
				proto = match.group(1)
				cfg[proto] = {}
			if proto:
				match = self._re_local_as.search(line)
				if match:
					cfg[proto]["bgpPeerLocalAs"] = int(match.group(1))
					if not "local_as" in cfg.keys():
						cfg['bgpLocalAs'] = int(match.group(1))
				match = self._re_remote_peer.search(line)
				if match:
					cfg[proto]["bgpPeerRemoteAddr"] = match.group(1)
					cfg[proto]["bgpPeerRemoteAs"] = int(match.group(2))
			match = self._re_proto_end.search(line)
			if match:
				proto = None

		cur_proto = None
		for line in commands.getoutput("%s show protocols all" % (self.cli)).split("\n"):
			print('line: %s' % line)
			match = self._re_bgp_begin.search(line)
			if match:
				cur_proto = match.group(1)
				t = int(match.group(2))
				cur = int(time.time())
				print('cur_proto: %s' % cur_proto)
				if not cur_proto in cfg:
					print('failed to find %s in config, skipping' % cur_proto)
					continue
				cfg[cur_proto]["bgpPeerFsmEstablishedTime"] = cur - t
			if cur_proto:
				for k in self._re_peer.keys():
					match = self._re_peer[k].search(line)
					if match:
						if k == 'bgpPeerState':
							cfg[cur_proto][k] = state[match.group(1).lower()]
						elif k in ['bgpPeerIdentifier', 'bgpPeerLocalAddr', 'bgpPeerRemoteAddr']:
							cfg[cur_proto][k] = match.group(1)
						else:
							cfg[cur_proto][k] = int(match.group(1))

			match = self._re_bgp_end.search(line)
			if match:
				cur_proto = None

		for proto in cfg.keys():
			if proto == 'bgpLocalAs': continue
			raddr = cfg[proto]['bgpPeerRemoteAddr']
			cfg[proto]['bgpPeerLocalPort'] = 0
			cfg[proto]['bgpPeerRemotePort'] = 0
			for line in commands.getoutput("netstat -an | grep '%s' | grep ':179'" % (raddr)).split("\n"):
				if "ESTABLISHED" in line:
					t = line.split()
					cfg[proto]['bgpPeerLocalPort'] = t[3].split(":")[1]
					cfg[proto]['bgpPeerRemotePort'] = t[4].split(":")[1]

		return cfg

	def check(self, cfg):
		for peer in cfg.keys():
			if peer == 'bgpLocalAs': continue
			if not 'bgpPeerHoldTime' in cfg[peer].keys():
				cfg[peer]['bgpPeerHoldTime'] = 0
			if not 'bgpPeerHoldTimeConfigured' in cfg[peer].keys():
				cfg[peer]['bgpPeerHoldTimeConfigured'] = 0
			if not 'bgpPeerIdentifier' in cfg[peer].keys():
				cfg[peer]['bgpPeerIdentifier'] = '0.0.0.0'
			if not 'bgpPeerKeepAlive' in cfg[peer].keys():
				cfg[peer]['bgpPeerKeepAlive'] = 0
			if not 'bgpPeerKeepAliveConfigured' in cfg[peer].keys():
				cfg[peer]['bgpPeerKeepAliveConfigured'] = 0
			if not 'bgpPeerLocalAddr' in cfg[peer].keys():
				cfg[peer]['bgpPeerLocalAddr'] = '0.0.0.0'
		return cfg

	def fetch_cfg(self):
		cfg = self._get_values()
		for k in cfg.keys():
			if k == 'bgpLocalAs': continue
			cfg[cfg[k]['bgpPeerRemoteAddr']] = cfg[k]
			del(cfg[k])
		for peer in cfg.keys():
			if peer == 'bgpLocalAs': continue
			for k in cfg[peer].keys():
				if k == 'bgpLocalAs': continue
				if k in self._c2a.keys():
					cfg[peer][k] = "%s|%s" % (self._c2a[k], cfg[peer][k])
		
		self._cfg = self.check(cfg)
		#pprint(self._cfg)

	def run(self):
		while True:
			self.fetch_cfg()
			time.sleep(15)

class Bird:
	_keys = [
		'bgpPeerIdentifier',
		'bgpPeerState',
		'bgpPeerAdminStatus',
		'bgpPeerNegotiatedVersion',
		'bgpPeerLocalAddr',
		'bgpPeerLocalPort',
		'bgpPeerRemoteAddr',
		'bgpPeerRemotePort',
		'bgpPeerRemoteAs',
		'bgpPeerInUpdates',
		'bgpPeerOutUpdates',
		'bgpPeerInTotalMessages',
		'bgpPeerOutTotalMessages',
		'bgpPeerLastError',
		'bgpPeerFsmEstablishedTransitions',
		'bgpPeerFsmEstablishedTime',
		'bgpPeerConnectRetryInterval',
		'bgpPeerHoldTime',
		'bgpPeerKeepAlive',
		'bgpPeerHoldTimeConfigured',
		'bgpPeerKeepAliveConfigured',
		'bgpPeerMinASOriginationInterval',
		'bgpPeerMinRouteAdvertisementInterval',
		'bgpPeerInUpdateElapsedTime',
	]

	_unmapped = {
		'bgpPeerAdminStatus':					2,
		'bgpPeerNegotiatedVersion':				0,
		'bgpPeerInTotalMessages':				'c|0',
		'bgpPeerOutTotalMessages':				'c|0',
		'bgpPeerLastError':						'o|0',
		'bgpPeerFsmEstablishedTransitions':		'g|0',
		'bgpPeerFsmEstablishedTime':			'g|0',
		'bgpPeerConnectRetryInterval':			0,
		'bgpPeerMinASOriginationInterval':		15,
		'bgpPeerMinRouteAdvertisementInterval':	30,
		'bgpPeerInUpdateElapsedTime':			'g|0',

	}

	def __init__(self, cfgfile, cli):
		self.cfg = BirdConfig(cfgfile, cli)
		ax.Init(
			name = 'bird-bgp4-mib-agent',
			master = False,
			mibfile = '/usr/local/share/bird-snmp/BGP4-MIB.txt',
			rootoid = "BGP4-MIB::bgp",
		)

	def register_vars(self):
		axd.RegisterVar('bgp', 0)
		axd.RegisterVar('bgpVersion', '10')
		axd.RegisterVar('bgpLocalAs', self.cfg['bgpLocalAs'])
		for k in self._keys:
			axd.RegisterVar(k, 0)
			for peer in self.cfg.get_all_peers():
				if peer == 'bgpLocalAs': continue
				oid = "%s.%s" % (k, peer)
				if self.cfg[peer].has_key(k):
					#print "%s: %s" % (oid, self.cfg[peer][k])
					axd.RegisterVar(oid, self.cfg[peer][k])
				else:
					#print "%s: %s" % (oid, self._unmapped[k])
					axd.RegisterVar(oid, self._unmapped[k])

	def run(self):
		ax.TimerStart(15)
		while True:
			axd.clear()
			self.register_vars()
			ax.Process()

