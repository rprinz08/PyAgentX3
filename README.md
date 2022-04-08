# Python3 AgentX Implementation

**PyAgentX3** is a pure Python3 implementation of the AgentX protocol (RFC 2741),
it will allow to extend an SNMP agent (e.g snmpd) by writing AgentX subagents,
without modifying the original SNMP agent.

[RFC 2741: Agent Extensibility (AgentX) Protocol](https://www.ietf.org/rfc/rfc2741.html)

This is a fork of the Python2 based PyAgentX package (available at
<https://github.com/hosthvo/pyagentx>)
modified for Python3 and enhanced (e.g. SNMP traps).


## Features

Currently the code is capable of the following:

* Open a session with AgentX master, e.g. net-snmpd snmpd, and register a new session.
* Send Ping request.
* Register multiple MIB regions.
* Multiple MIB update classes with custom frequency for each.
* Support snmpset operations.
* Reconnect/Retry to master, in case the master restarted.
* Support for SNMPv2 traps.


## Prerequisites

A running and correctly configured SNMP daemon (e.g. net-snmp) is required.
Install using your OS package manager or from [source](https://www.net-snmp.org/download.html).
For Ubuntu for example use:

```bash
apt install snmpd snmptrapd snmp-mibs-downloader
```

_Note_: For some licensing reasons `snmp-mibs-downloader` can only be downloaded
after enabling non-free software on some distributions. For Debian enable
*non-free* for Ubuntu *multiverse*.

```bash
# for Ubuntu
apt install software-properties-common
add-apt-repository multiverse
apt install snmp-mibs-downloader
```


## Installation

The package is registered on [Python Package Index](https://pypi.python.org/)
under the name "pyagentx3" [https://pypi.python.org/pypi/pyagentx3](https://pypi.python.org/pypi/pyagentx3).

You can install it by simply running:

```bash
pip install pyagentx3
```


## SNMP Agent Configuration

You need to make sure the SNMP agent `snmpd` will act as AgentX master:

```
master          agentx
```

Also make sure the SNMP agent accept requests for the wanted MIB region:

```
# NET-SNMP-EXAMPLES-MIB
view   systemview  included   .1.3.6.1.4.1.8072.2
```

__NOTE__: You need to change the OID to reflect your own OID.


## Minimal Agent

To implement an agent you need to provide one "Agent" class and one or more
"Updater" classes. A simple agent might look like:

```python
import pyagentx3

# Updater class that set OID values
class NetSnmpPlaypen(pyagentx3.Updater):
    def update(self):
        self.set_INTEGER('1.0', 1000)
        self.set_OCTETSTRING('3.0', 'String for NET-SNMP-EXAMPLES-MIB')

class MyAgent(pyagentx3.Agent):
    def setup(self):
        # Register Updater class that responsd to
        # the tree under "netSnmpPlaypen": 1.3.6.1.4.1.8072.9999.9999
        self.register('1.3.6.1.4.1.8072.9999.9999', NetSnmpPlaypen)

# Main
pyagentx3.setup_logging()
try:
    a = MyAgent()
    a.start()
except Exception as e:
    print "Unhandled exception:", e
    a.stop()
except KeyboardInterrupt:
    a.stop()
```

To test:

```bash
snmpwalk -v 2c -c public localhost NET-SNMP-MIB::netSnmpPlaypen
```


## Example agent and scripts

To test the implementation the [samples](samples) directory contains a sample
agent that implements some parts of
[NET-SNMP-EXAMPLES-MIB](http://www.net-snmp.org/docs/mibs/NET-SNMP-EXAMPLES-MIB.txt)
including a tables and traps.

Also in this directory some sample scripts exists which allow to query and
set OID's.


## FAQ


### What OID should I use for my agent?

If you are just playing and experminting you can put everything under
**NET-SNMP-MIB::netSnmpPlaypen** OID **1.3.6.1.4.1.8072.9999.9999** tree, but you
shouldn't use it for any public work.

If you need to publish your work you should apply for your own enterprise OID
on the IANA [PEN Application page](http://pen.iana.org/pen/PenApplication.page),
this will give you your own private tree, e.g. Net-Snmp uses **1.3.6.1.4.1.8072**,
Google uses **1.3.6.1.4.1.11129**

So your company would have an OID **1.3.6.1.4.1.xxxxx**

You also need to write your own MIB to allow your customer to use in thier
Network Managment System (NMS):

<http://www.net-snmp.org/wiki/index.php/Writing_your_own_MIBs>


### Are there other ways to extend SNMP agent?

Some SNMP agents can be extended using different mechanisms, e.g. net-snmp can
be extended using:

* running external commands (exec, extend, pass)
* loading new code dynamically (embedded perl, dlmod)
* communicating with other agents (proxy, SMUX, AgentX)

Check "EXTENDING AGENT FUNCTIONALITY" in `snmpd.conf` man page for more details.


### What's the difference between AgentX, SMUX and proxied SNMP?

Check the answer [here](http://net-snmp.sourceforge.net/wiki/index.php/FAQ:Agent_08)


### What is advatages of extending SNMP using AgentX instead of something like "pass\_perssist"?

One advantage is to decouple the master SNMP agent from its sub-agents, which
means you can start/stop one without affecting the other, and you don't have to
change the `snmpd.conf` every time you want to add or remove a sub-agent.

Another advantage is the support for traps in AgentX.


### Why do I need `sudo` to run my AgentX agent?

By default `snmpd` uses UNIX socket to communicate with AgentX sub-agents, it
uses special permisssions to prevent unauthorized agents.

If you don't want to use **root** to run the agent you can use `agentXPerms`
directive in `snmpd.conf`, check the man page for its options.


### My agent connected to the master but I couldn't get any results with snmpwalk?

First make sure you can get results from the agent, try something basic:

```bash
snmpwalk -v 2c -c public localhost .
```

If the command doesn't return anything, double check your agent community
and Access List.

If it works on standard OIDs but it doesn't work on your sub-agent, make sure
you include the correct OID view:

```
view   systemview  included   .1.3.6.1.4.1.8072.2
```


### How can I test it on Mac OSX?

SNMP agent from net-snmp is already installed on OSX, but first you need to load it:

```bash
sudo launchctl load -w /System/Library/LaunchDaemons/org.net-snmp.snmpd.plist
```

Then you can start and stop it with these commands:

```bash
sudo launchctl start org.net-snmp.snmpd
sudo launchctl start org.net-snmp.snmpd
```

The configuration file can be found on the default location `/etc/snmp/snmpd.conf`.

