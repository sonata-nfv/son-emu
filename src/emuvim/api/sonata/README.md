# SONATA dummy gatekeeper API:

## Upload a package (*.son) file:

To upload the file `simplest-example.son` do:

* `curl -i -X POST -F file=@simplest-example.son http://127.0.0.1:8000/api/packages/uploads`

To list all uploaded packages do:

* `curl http://127.0.0.1:8000/api/packages/uploads`

To instantiate (start) a service do:

* `curl ...`

To list all running services do:

* `curl ...`


## API definition

This page describes the dummy gatekeeper API. This gatekeeper fakes the original platform gatekeeper during development SDK tools like son-push. 

It is also able to deploy our example service package (not any arbitrary service package!) in the emulator for the Y1 demo.

_Note: This API should converge to the API of the original GK as much as possible!_

## REST API:
<table>
<tr>
<th>Endpoint:</th>
<th>Method:</th>
<th>Header:</th>
<th>Body:</th>
<th>Response:</th>
</tr>
<tr>
<td>/api/packages/uploads</td>
<td>POST</td>
<td>-</td>
<td>{file-content} as enctype=multipart/form-data</td>
<td>{"service_uuid": "c880aaab-f3b9-43ac-ac6b-3d27b46146b7", size=456, sha1=49ee6468dfa4ecbad440d669b249d523a38651be, error: null}</td>
</tr>
<tr>
<td>/api/packages/uploads</td>
<td>GET</td>
<td>-</td>
<td></td>
<td>{service_uuid_list: ["c880aaab-f3b9-43ac-ac6b-3d27b46146b7", "c880aaab-f3b9-43ac-ac6b-3d27b46146b8", "c880aaab-f3b9-43ac-ac6b-3d27b46146b9"]}</td>
</tr>
<tr>
<td>/api/instantiations</td>
<td>POST</td>
<td>-</td>
<td>{service_uuid: "c880aaab-f3b9-43ac-ac6b-3d27b46146b7"}</td>
<td>{service_instance_uuid: "de4567-f3b9-43ac-ac6b-3d27b461123"}</td>
</tr>
<tr>
<td>/api/instantiations</td>
<td>GET</td>
<td>-</td>
<td></td>
<td>{service_instance_uuid_list: ["de4567-f3b9-43ac-ac6b-3d27b461123", "de4567-f3b9-43ac-ac6b-3d27b461124", "de4567-f3b9-43ac-ac6b-3d27b461125"]}</td>
</tr>
</table>

## Run REST API in standalone mode (without emulator):

* `sudo python src/emuvim/api/sonata/dummygatekeeper.py`