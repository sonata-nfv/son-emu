#!/bin/bash
export DOCKER_HOST="unix:///var/run/docker.sock"

set -e
set -x

W() {
    # Wait until a line appears in the screen session.
    # It starts from the beginning of the log and exits after the first match.
    local T=${2:-20s}
    #timeout -k 3s ${T} stdbuf -o0 grep -q -m 1 "^${1}" <(tail -F -n+0 screenlog.0)
    # (HACK) As Jenkins blocks subshell, we must use an intermediate script
    local SUBF=$(mktemp)
    chmod +x ${SUBF}
    cat > ${SUBF} <<- EOF
	#!/bin/bash -e
	set -x
	while true; do
	    if strings screenlog.0 | grep -m 1 "\${1}"; then
	        exit 0
	    fi
	    sleep 0.5s
	done
	EOF
    cat ${SUBF}
    timeout -k 3s ${T} ${SUBF} "${1}"
    local RES=$?
    rm -f ${SUBF}
    return ${RES}
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
if ! timeout --version; then
    # Install coreutils for the timeout command
    sudo apt-get update -qq -y
    sudo apt-get install -y coreutils
    timeout --version
fi
# Initial cleanup
pkill -f 'SCREEN -L -S sonemu' || true
screen -wipe || true
rm -f screenlog.0


# Start containernet with a topology
screen -L -S sonemu -d -m python src/emuvim/examples/simple_topology.py
# Setup screen for immediate flusing
screen -S sonemu -X logfile flush 0
# Wait for the cli to start
W '^*** Starting CLI:' 60s
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
sync # avoid test overlapping
Cmd 'vnf1 ifconfig && echo "... checked vnf1"'
W "^... checked vnf1"
Cmd 'vnf2 ifconfig && echo "... checked vnf2"'
W "^... checked vnf2"
# Try to ping vnfs
Cmd 'vnf1 ping -c 2 vnf2 || echo "... checked ping"'
W "^... checked ping" 20s
Cmd 'quit'
# Wait for sonemu to end
W '^*** Done'

echo -e '\n\n******************* Result ******************\n\n'
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
