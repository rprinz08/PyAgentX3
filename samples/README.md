# Samples

This directory contains a sample AgentX sub-agent `local-agent.py` and some
shell scripts to query `local-query.sh` and set `local-query.sh` OID's
from the **net-snmp** sample OID tree (1.3.6.1.4.1.8072.2).

To test, first ensure that you have a running **snmpd** and **snmptrapd**. Start
`local-query.sh` in one terminal window and try out the shell scripts in
another window. They allow to query scalar values (e.g. integer, strings
etc.) and tables of scaler values as well as setting a sample integer.

_Note_: Ensure to start `local-agent.py` as superuser (e.g. sudo).
More infos about this in the FAQ sections of the [project readme](../README.md).

The `local-agent.py` sub-agent also maintains an auto-incrementing counter
which triggers a trap every time it is fully divisible by 5 without remainder.
This can be seen in the **snmptrapd** logs.

Sample, working configuration files for net-snmp (snmpdm, snmptrapd) and start
(systemd) configurations can be found in the [configuration](configuration) subdirectory.

