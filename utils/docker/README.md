# Docker build scripts for son-emu

This directory holds the Dockerfile to build son-emu as a docker container.
This is an easy way to deploy son-emu.
To build this container:

(container tag can be freely chosen)
```
docker build -t registry.sonata-nfv.eu:5000/son-emu .
```

To deploy this container:

(choose an example topology to start in the emulator)
```
docker run -d -i --net='host' --pid='host' --privileged='true' --name 'son-emu' \
    -v '/var/run/docker.sock:/var/run/docker.sock' \
    -p 5000:5000 \
    -p 9091:9091 \
    -p 8081:8081 \
    -p 5001:5001 \
    registry.sonata-nfv.eu:5000/son-emu 'python src/emuvim/examples/sonata_simple_topology.py'
```