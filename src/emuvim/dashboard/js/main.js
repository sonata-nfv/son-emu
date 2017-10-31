var API_HOST = "http://127.0.0.1:5001";
var ERROR_ALERT = false;
var TIMESTAMP = 0;
var CONNECTED = false;
var LATENESS_UPDATE_INTERVAL = 50;
var DATA_UPDATE_INTERVAL = 1000 * 10;
var LAST_UPDATE_TIMESTAMP_CONTAINER = 0;
var LAST_UPDATE_TIMESTAMP_DATACENTER = 0;


function update_lateness_loop() {
    lateness_datacenter= (Date.now() - LAST_UPDATE_TIMESTAMP_DATACENTER) / 1000;
    $("#lbl_lateness_datacenter").text("Lateness: " + Number(lateness_datacenter).toPrecision(3) + "s");
    lateness_container= (Date.now() - LAST_UPDATE_TIMESTAMP_CONTAINER) / 1000;
    $("#lbl_lateness_container").text("Lateness: " + Number(lateness_container).toPrecision(3) + "s");
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
        alert("ERROR!\nAPI request failed.\n\n Please check the backend connection.", function() {
            // callback
            ERROR_ALERT = false;
        });
    }
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
        row_str += '<td>' + item.label + '1</td>';
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
    $("#table_container").append('<tr class="tbl-head"><td>Datacenter</td><td>Container</td><td>Image</td><td>docker0</td><td>--Networking--<div id="table_network"></div></td></tr>');
    // fill table
    $.each(data, function(i, item) {
        var row_str = "";
        row_str += '<tr class="tbl-row clickable_row" id="container_row_' + item[0] +'">';
        row_str += '<td>' + item[1].datacenter + '</td>';
        row_str += '<td>' + item[0] + '</td>';
        row_str += '<td>' + item[1].image + '</td>';
        row_str += '<td><code>' + item[1].docker_network + '</code></td>';
        row_str += '<td><table class="interface_table" id="network_list_' + item[0] + '">';
        //row_str += build_network_table(item[1].network, item[0]);
        row_str += '</table></td>';
        row_str += '</tr>';
	    $("#table_container").append(row_str);
	    build_network_table(item[1].network, item[0]);
    });
    $("#lbl_container_count").text(data.length);
    $("#table_network").append('<table class="interface_table"><tr class="interface_row"><td class="interface_port">datacenter port</td><td class="interface_name">interface</td><td class="interface_ip">ip</td><td class="interface_mac">mac</td><td class="vlan_tag">vlan</td></tr></table>')
    // update lateness counter
    LAST_UPDATE_TIMESTAMP_CONTAINER = Date.now();
}

function build_network_table(network_list, id)
{
    console.debug('network list ' + id)
    console.debug(network_list)
    var row_str = "";
    network_list.forEach(function(interface) {
        row_str += '<tr class="interface_row">';
        row_str += '<td class="interface_port">' + interface.dc_portname + '</td>';
        row_str += '<td class="interface_name">' + interface.intf_name + '</td>';
        row_str += '<td class="interface_ip">' + interface.ip + '</td>';
        row_str += '<td class="interface_mac">' + interface.mac + '</td>';
        row_str += '<td class="vlan_tag">' + interface.vlan + '</td>';
        row_str += '</tr>';
    });
    $("#network_list_" + id).append(row_str)
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


function fetch_d3graph()
{
    // do HTTP request and trigger gui update on success
    var request_url = API_HOST + "/restapi/network/d3jsgraph";
    console.debug("fetching from: " + request_url);
    //$.getJSON(request_url,  update_graph);
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
    API_HOST = "http://" + $("#text_api_host").val();
    console.debug("API address: " + API_HOST);
    // reset data
    LAST_UPDATE_TIMESTAMP_DATACENTER = Date.now();
    LAST_UPDATE_TIMESTAMP_CONTAINER = Date.now();
    CONNECTED = true;
    // restart lateness counter
    update_lateness_loop();
    // restart data fetch loop
    fetch_loop();
    // gui updates
    $("#btn_disconnect").removeClass("disabled");
    $("#btn_connect").addClass("disabled");
}

function disconnect()
{
    console.info("disconnect()");
    CONNECTED = false;
     // gui updates
    $("#btn_connect").removeClass("disabled");
    $("#btn_disconnect").addClass("disabled");
}


$(document).ready(function(){
    console.info("document ready");
    // setup global connection error handling
    /*
    $.ajaxSetup({
        "error": errorAjaxConnection
    });

    // add listeners
    $("#btn_connect").click(connect);
    $("#btn_disconnect").click(disconnect);
    */
    setTimeout(fetch_datacenter, 500);//fetch_datacenter();
    setTimeout(fetch_container, 1000);//fetch_container();


    // additional refresh on window focus
    $(window).focus(function () {
        if(CONNECTED)
        {
            fetch_datacenter();
            fetch_container();  
        }
    });

});
