from setuptools import setup


setup(
    name = "pyagentx3",
    version = "0.1.1",
    author = "Richard Prinz",
    author_email = "richard.prinz@min.at",
    description = ("AgentX package to extend SNMP with pure Python3"),
    license = "BSD",
    keywords = "snmp network agentx ",
    url = "https://github.com/rprinz08/pyagentx3",
    packages=['pyagentx3'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Environment :: No Input/Output (Daemon)",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Telecommunications Industry",
    ],
    long_description='''\
PyAgentX3
--------------------
pyagentx3 is a pure Python3 implementation of AgentX protocol (RFC 2741), it
will allow you to extend an SNMP agent (e.g. snmpd) by writing AgentX subagents,
without modifying the original SNMP agent.

The agent can support the following commands:
- snmpget
- snmpwalk
- snmptable
- snmpset

It also allows sending notifications/traps.
''',
)

