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
    $("#table_datacenter").append('<tr class="tbl-head"><td>Label</td><td>Int. Name</td><td>Switch</td><td>Num. Containers</td><td>Metadata Items</td></tr>');
    // fill table
    $.each(data, function(i, item) {
        var row_str = "";
        row_str += '<tr class="tbl-row clickable_row" id="datacenter_row_' + i +'">';
        row_str += '<td>' + item.label + '1</td>';
        row_str += '<td>' + item.internalname + '</td>';
        row_str += '<td>' + item.switch + '</td>';
        row_str += '<td><span class="badge">' + item.n_running_containers + '</span></td>';
        row_str += '<td><span class="badge">' + Object.keys(item.metadata).length + '</span></td>';
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
    $.ajaxSetup({
        "error": errorAjaxConnection
    });

    // add listeners
    $("#btn_connect").click(connect);
    $("#btn_disconnect").click(disconnect);

    // additional refresh on window focus
    $(window).focus(function () {
        if(CONNECTED)
        {
            fetch_datacenter();
            fetch_container();  
        }
    });

});
