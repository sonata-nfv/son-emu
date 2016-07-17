#! /bin/bash -e

# docker stop trap signals
# https://medium.com/@gchudnov/trapping-signals-in-docker-containers-7a57fdda7d86#.5d6q01x7q

pid=0
command=""
term_recvd=0

# send SIGTERM also to the executed command in the docker container (the containernet topology)
# SIGTERM-handler
function term_handler() { 
  echo $command	
  pid=$(pgrep -f "$command" | sed -n 1p)

  pid="$!"
  # avoid that the process triggers its own handler by sending sigterm
  if [ $pid -ne 0 ] && [ $term_recvd -eq 0 ]; then
    echo "sigterm received"
    echo $pid	
    term_recvd=1
    kill -SIGTERM "$pid"  
  fi

  wait "$pid"

  # do some manual cleanup
  # remove all containers started by son-emu
  docker ps -a -q --filter="name=mn.*" | xargs -r docker rm -f
  # cleanup remaining mininet
  mn -c

  sleep 5
  exit 143; # 128 + 15 -- SIGTERM
}

# setup handlers
# on callback, kill the last background process, which is `tail -f /dev/null` and execute the specified handler
trap 'term_handler' SIGTERM


service openvswitch-switch start

if [ ! -S /var/run/docker.sock ]; then
    echo 'Error: the Docker socket file "/var/run/docker.sock" was not found. It should be mounted as a volume.'
    exit 1
fi

# this cannot be done from the Dockerfile since we have the socket not mounted during build
echo 'Pulling the "ubuntu:trusty" image ... please wait'
docker pull 'ubuntu:trusty'

echo "Welcome to Containernet running within a Docker container ..."

if [[ $# -eq 0 ]]; then
    exec /bin/bash
else
    #remember command to send it also the SIGTERM via the handler
    command=$*
    echo $command	
    exec $* &
    # wait indefinetely
    while true
    do
      sleep 1
    done
    echo "done"
fi
