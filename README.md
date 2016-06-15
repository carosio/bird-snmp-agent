## bird-snmp-agent

### What?

* implements an SNMP-AgentX extension for the bird-routing-daemon
* currently exposes a subset of BGP4-MIB (RFC4273)

### How?

To collect its data this agent:

* uses `birdc` CLI of bird
* calls netstat to query information about used tcp-ports
* reads the bird-configuration-files

