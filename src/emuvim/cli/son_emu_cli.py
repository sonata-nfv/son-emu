#!/usr/bin/python
# Copyright (c) 2015 SONATA-NFV and Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
import sys
from emuvim.cli.rest import compute as restcom
from emuvim.cli.rest import datacenter as restdc
from emuvim.cli.rest import monitor as restmon
from emuvim.cli.rest import network as restnetw


def help():
    print("Missing arguments.\n")
    print("Usage: vim-emu compute|datacenter|network <arguments>\n")
    print("Get more help:")
    print("\tvim-emu compute --help")
    print("\tvim-emu datacenter --help")
    print("\tvim-emu network --help")
    exit(0)


def main():
    if len(sys.argv) < 2:
        help()
    elif sys.argv[1] == "monitor":
        restmon.main(sys.argv[2:])
    elif sys.argv[1] == "network":
        restnetw.main(sys.argv[2:])
    elif sys.argv[1] == "compute":
        restcom.main(sys.argv[2:])
    elif sys.argv[1] == "datacenter":
        restdc.main(sys.argv[2:])
    else:
        help()


if __name__ == '__main__':
    main()
