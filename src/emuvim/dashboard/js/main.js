/*
 Copyright (c) 2017 SONATA-NFV and Paderborn University
 ALL RIGHTS RESERVED.
 
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

 Neither the name of the SONATA-NFV, Paderborn University
 nor the names of its contributors may be used to endorse or promote
 products derived from this software without specific prior written
 permission.

 This work has been performed in the framework of the SONATA project,
 funded by the European Commission under Grant number 671517 through
 the Horizon 2020 and 5G-PPP programmes. The authors would like to
 acknowledge the contributions of their colleagues of the SONATA
 partner consortium (www.sonata-nfv.eu).
*/
var API_HOST = "";  // set to a remote url if dashboard is not served by REST API server
var ERROR_ALERT = false;
var TIMESTAMP = 0;
var CONNECTED = false;
var LATENESS_UPDATE_INTERVAL = 50;
var DATA_UPDATE_INTERVAL = 1000 * 10; // 30 seconds
var LAST_UPDATE_TIMESTAMP_CONTAINER = 0;
var LAST_UPDATE_TIMESTAMP_DATACENTER = 0;


function update_lateness_loop() {
    lateness_datacenter= (Date.now() - LAST_UPDATE_TIMESTAMP_DATACENTER) / 1000;
    $("#lbl_lateness_datacenter").text("Lateness: " + Number(lateness_datacenter).toPrecision(2) + "s");
    lateness_container= (Date.now() - LAST_UPDATE_TIMESTAMP_CONTAINER) / 1000;
    $("#lbl_lateness_container").text("Lateness: " + Number(lateness_container).toPrecision(2) + "s");
    // loop while connected
    if(CONNECTED)
        setTimeout(update_lateness_loop, LATENESS_UPDATE_INTERVAL)
}


function errorAjaxConnection()
{
    // only do once
    if(!ERROR_ALERT)
    {
        ERROR_ALERT = true;
        // show message
        //alert("API request failed. Is the emulator running?", function() {
        //    // callback
        //    ERROR_ALERT = false;
        //});
    }
    CONNECTED = false;
    console.error("API request failed. Is the emulator running?")
}


function update_table_datacenter(data)
{
    console.debug(data)
    // clear table
    $("#table_datacenter").empty();
    // header
    $("#table_datacenter").append('<tr class="tbl-head"><td>Label</td><td>Int. Name</td><td>Switch</td><td>Num. Containers</td><td>VNFs</td></tr>');
    // fill table
    $.each(data, function(i, item) {
        var row_str = "";
        row_str += '<tr class="tbl-row clickable_row" id="datacenter_row_' + i +'">';
        row_str += '<td>' + item.label + '</td>';
        row_str += '<td>' + item.internalname + '</td>';
        row_str += '<td>' + item.switch + '</td>';
        row_str += '<td><span class="badge">' + item.n_running_containers + '</span></td>';
        //row_str += '<td><span class="badge">' + Object.keys(item.metadata).length + '</span></td>';
        row_str += '<td>' + item.vnf_list + '</span></td>';
        row_str += '<tr>';
	$("#table_datacenter").append(row_str);
    });
    $("#lbl_datacenter_count").text(data.length);
    // update lateness counter
    LAST_UPDATE_TIMESTAMP_DATACENTER = Date.now();
}


function update_table_container(data)
{
    console.debug(data)
    // clear table
    $("#table_container").empty();
    // header
    $("#table_container").append('<tr class="tbl-head"><td>Datacenter</td><td>Container</td><td>Image</td><td>docker0</td><td>Status</td></tr>');
    // fill table
    $.each(data, function(i, item) {
        var row_str = "";
        row_str += '<tr class="tbl-row clickable_row" id="container_row_' + i +'">';
        row_str += '<td>' + item[1].datacenter + '</td>';
        row_str += '<td>' + item[0] + '</td>';
        row_str += '<td>' + item[1].image + '</td>';
        row_str += '<td><code>' + item[1].docker_network + '<code></td>';
        if(item[1].state.Status == "running")
            row_str += '<td><span class="label label-success">running</span></td>';
        else
            row_str += '<td><span class="label label-danger">stopped</span></td>';
        row_str += '<tr>';
	$("#table_container").append(row_str);
    });
    $("#lbl_container_count").text(data.length);
    // update lateness counter
    LAST_UPDATE_TIMESTAMP_CONTAINER = Date.now();
}


function fetch_datacenter()
{
    // do HTTP request and trigger gui update on success
    var request_url = API_HOST + "/restapi/datacenter";
    console.debug("fetching from: " + request_url);
    $.getJSON(request_url,  update_table_datacenter);
}


function fetch_container()
{
    // do HTTP request and trigger gui update on success
    var request_url = API_HOST + "/restapi/compute";
    console.debug("fetching from: " + request_url);
    $.getJSON(request_url,  update_table_container);
}


function fetch_loop()
{
    // only fetch if we are connected
    if(!CONNECTED)
        return;

    // download data
    fetch_datacenter();
    fetch_container();
    
    // loop while connected
    if(CONNECTED)
        setTimeout(fetch_loop, DATA_UPDATE_INTERVAL);
}


function connect()
{
    console.info("connect()");
    // get host address
    //API_HOST = "http://" + $("#text_api_host").val();
    console.debug("API address: " + API_HOST);
    // reset data
    LAST_UPDATE_TIMESTAMP_DATACENTER = Date.now();
    LAST_UPDATE_TIMESTAMP_CONTAINER = Date.now();
    CONNECTED = true;
    // restart lateness counter
    update_lateness_loop();
    // restart data fetch loop
    fetch_loop();
}


$(document).ready(function(){
    console.info("document ready");
    // setup global connection error handling
    
    $.ajaxSetup({
        "error": errorAjaxConnection
    });

    // connect
    connect();

    // additional refresh on window focus
    $(window).focus(function () {
        if(CONNECTED)
        {
            fetch_datacenter();
            fetch_container();  
        }
    });

});
