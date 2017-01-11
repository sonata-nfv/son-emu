var API_HOST = "http://127.0.0.1:5001";
var ERROR_ALERT = true;
var TIMESTAMP = 0;



function updateMessageTable(msg_list) {
   
}

function updateMessageCount(msg_list) {
    $("#lbl_msg_count").text(msg_list.length);
}

function fetchMessages() {
   
}


function autoFetchMessages() {
    fetchMessages();
    // do periodic update
    if(AUTO_REFRESH)
	    setTimeout(autoFetchMessages, AUTO_REFRESH_INTERVAL);
}

function updateLateness() {
    lateness = (Date.now() - LAST_UPDATE_TIMESTAMP) / 1000;
    $("#lbl_lateness").text("Lateness: " + Number(lateness).toPrecision(3) + "s")
    setTimeout(updateLateness, LATENESS_UPDATE_INTERVAL)
}

function errorAjaxConnection()
{
    // only do once
    if(!ERROR_ALERT)
    {
        ERROR_ALERT = true;
        // show message
        bootbox.alert("ERROR!\nAPI request failed.\n\n Please check the backend connection.", function() {
            // callback
            ERROR_ALERT = false;
        });
    }
}

function change_auto_refresh(event)
{
    console.debug("trigger btn_auto_refresh");
    AUTO_REFRESH = !AUTO_REFRESH;
    if(AUTO_REFRESH) {
        $("#btn_autorefresh").addClass("active");
        autoFetchMessages();
    }
    else {
        $("#btn_autorefresh").removeClass("active");
    }
}


$(document).ready(function(){
    console.info("document ready");
	// setup global connection error handling
	$.ajaxSetup({
      "error": errorAjaxConnection
	});

    // add listeners
    //TODO

    // activate message fetching
    autoFetchMessages();
    LAST_UPDATE_TIMESTAMP = Date.now();
    updateLateness();


    // refresh on window focus
    $(window).focus(function () {
        // TODO observe if this works well
        fetchMessages();
    });

});
