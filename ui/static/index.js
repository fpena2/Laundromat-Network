
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


    return;
});

function sendMessageToServer() {
    console.log("Sending message to server.")
    var message = $("#input").val()
    console.log("message: " + message)
    socket.emit("inputDataEvent", message)
    console.log("...done.")
}

