#!/bin/bash

# Walk all subnodes under given OID
snmpwalk -v 2c -c public localhost 1.3.6.1.4.1.8072.2.1
echo

# Access node by node
# Scalars

# integer
snmpget -v 2c -c public localhost 1.3.6.1.4.1.8072.2.1.1.0
# data object
snmpget -v 2c -c public localhost 1.3.6.1.4.1.8072.2.1.2.0
# string
snmpget -v 2c -c public localhost 1.3.6.1.4.1.8072.2.1.3.0
# OID
snmpget -v 2c -c public localhost 1.3.6.1.4.1.8072.2.1.4.0
# ip address
snmpget -v 2c -c public localhost 1.3.6.1.4.1.8072.2.1.5.0
# counter 32
snmpget -v 2c -c public localhost 1.3.6.1.4.1.8072.2.1.6.0
# gauge 32
snmpget -v 2c -c public localhost 1.3.6.1.4.1.8072.2.1.7.0
# time ticks
snmpget -v 2c -c public localhost 1.3.6.1.4.1.8072.2.1.8.0
# opaque
snmpget -v 2c -c public localhost 1.3.6.1.4.1.8072.2.1.9.0
# counter 64
snmpget -v 2c -c public localhost 1.3.6.1.4.1.8072.2.1.10.0
echo

# Table
snmptable -v 2c -c public -Ci localhost 1.3.6.1.4.1.8072.2.2.1

