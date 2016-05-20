#!/usr/bin/python
"""
 Simple CLI client to interact with a running emulator.

 (c) 2016 by Manuel Peuster <manuel.peuster@upb.de>

 The CLI offers different tools, e.g., compute, network, ...
 Each of these tools is implemented as an independent Python
 module.

 cli compute start dc1 my_name flavor_a
 cli network create dc1 11.0.0.0/24
"""

import sys
from emuvim.cli import compute
from emuvim.cli import network
from emuvim.cli import datacenter
from emuvim.cli import monitor

def main():
    if len(sys.argv) < 2:
        print("Usage: son-emu-cli <toolname> <arguments>")
        exit(0)
    if sys.argv[1] == "compute":
        compute.main(sys.argv[2:])
    elif sys.argv[1] == "network":
        network.main(sys.argv[2:])
    elif sys.argv[1] == "datacenter":
        datacenter.main(sys.argv[2:])
    elif sys.argv[1] == "monitor":
        monitor.main(sys.argv[2:])

if __name__ == '__main__':
    main()
