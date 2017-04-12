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
	while true; do
	    if strings screenlog.0 | grep -m 1 "\${1}"; then
	        exit 0
	    fi
	    sleep 0.5s
	done
	EOF
    local RES=0
    timeout -k 3s ${T} ${SUBF} "${1}" || RES=$?
    rm -f ${SUBF}
    if [ ! "$RES" = "0" ]; then
        sync
        echo -e "\n\n\n(Debug) Error while waiting for a pattern to appear in screenlog.0\n\n\n"
        strings screenlog.0
    fi
    return ${RES}
}

Cmd() {
    # Send a command to the screen session, aka into the containernet prompt
    screen -S sonemu -X stuff "${1}^M"
}

Vnf() {
    # Send a command inside the vnf1 container
    docker exec -t "mn.${1}" /bin/bash -c "${2}" && sync
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
pkill --signal KILL -f 'SCREEN -L -S sonemu' || true
sleep 1s
screen -wipe || true
rm -f screenlog.0


# Start containernet with a topology
screen -L -S sonemu -d -m sudo python src/emuvim/examples/simple_topology.py
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
sync # avoid text overlapping
# Gather some infos
Cmd 'sh sync'
Cmd 'sh echo "... starting various checks"'
sync # avoid text overlappin
Cmd 'links'
Vnf vnf1 'ifconfig'
Vnf vnf2 'ifconfig'
# Try to ping vnfs
IP_2=$(Vnf vnf2 'ip -f inet -o addr show vnf2-eth0' | cut -d\  -f 7 | cut -d/ -f 1)
# IP_1=$(Vnf vnf1 'ip -f inet -o addr show vnf1-eth0' | cut -d\  -f 7 | cut -d/ -f 1)
OUTPUT_A=$(Vnf vnf1 "ping -v -c 2 ${IP_2}")
Cmd 'quit'
# Wait for sonemu to end
W '*** Done'

echo -e '\n\n******************* Result ******************\n\n'
strings screenlog.0
echo -e '\n\n*********************************************\n\n'


# Check the ping result
if echo ${OUTPUT_A} | grep ', 2 received'; then
    echo 'No problems detected'
    exit 0
else
    echo 'Ping is broken !'
    exit 1
fi
