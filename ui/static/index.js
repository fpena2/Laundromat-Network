
console.log("here");

var socket = null

$("body").ready(function() {
    console.log("running");

    socket = io();
    socket.on('connect', function() {
        console.log("connected")
    });

    socket.on("inputDataResponse", function(data) {
        console.log("received input data response. Data: " + data)
        $("#server_response").html(data)
    });

    // onclick functions below
    $(".device_list_title").click(function(e) {
        var underscore_location = e.target.id.indexOf("_")
        var device = e.target.id.substring(0, underscore_location);
        underscore_location = e.target.id.lastIndexOf("_")
        var id = e.target.id.substring(underscore_location + 1);

        var css_id = "#" + device + "_" + id;
        console.log("Toggling open on device list: " + css_id);

        $(css_id).toggleClass("open");
    });

    return;
});

function sendMessageToServer() {
    console.log("Sending message to server.")
    var message = $("#input").val()
    console.log("message: " + message)
    socket.emit("inputDataEvent", message)
    console.log("...done.")
}

