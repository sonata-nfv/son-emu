#!/bin/bash
export DOCKER_HOST="unix:///var/run/docker.sock"

set -e
set -x

W() {
    # Wait until a line appears in the screen session
    local T=${2:-10s}
    timeout -k 3s ${T} grep -q "^${1}" <(tail -f screenlog.0)
}

Cmd() {
    # Send a command to the screen session, aka into the containernet prompt
    screen -S sonemu -X stuff "${1}^M"
}


if ! screen --version | grep 'Screen version'; then
    # Install screen and do an initial cleanup
    sudo apt-get update -qq -y
    sudo apt-get install -y screen
    screen --version | grep 'Screen version'
fi
# Initial cleanup
pkill 'screen' || true
screen -wipe || true
rm -f screenlog.0


# Start containernet with a topology
screen -L -S sonemu -d -m python src/emuvim/examples/simple_topology.py
# Setup screen for immediate flusing
screen -S sonemu -X logfile flush 0
# Wait for the cli to start
W '*** Starting CLI:'
# Print nodes
Cmd 'nodes'
# Start vnf1
son-emu-cli compute start -d datacenter1 -n vnf1 && sleep 1s
# Start vnf2
son-emu-cli compute start -d datacenter1 -n vnf2 && sleep 1s
# List compute nodes
son-emu-cli compute list && sleep 1s
# Gather some infos
Cmd 'sh echo "... starting various checks"'
Cmd 'vnf1 ifconfig && echo "... checked vnf1"'
W "... checked vnf1"
Cmd 'vnf2 ifconfig && echo "... checked vnf2"'
W "... checked vnf2"
# Try to ping vnfs
Cmd 'vnf1 ping -c 2 vnf2 || echo "... checked ping"'
W "... checked ping" 20s
Cmd 'quit'
# Wait for sonemu to end
W '*** Done'

echo -e '\n\n************i****** Result ******************\n\n'
strings screenlog.0
echo -e '\n\n*********************************************\n\n'


# Check the ping result
if grep ', 2 received' screenlog.0; then
    echo 'No problems detected'
    exit 0
else
    echo 'Ping is broken !'
    exit 1
fi


# Cleanup
rm -f screenlog.0
