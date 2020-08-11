#!/bin/bash

# Setable integer
snmpset -v 2c -c public localhost 1.3.6.1.4.1.8072.2.1.1.0 i 42

