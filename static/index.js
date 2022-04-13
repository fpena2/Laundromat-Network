// constants
const CHART_UPDATE_T = 1000

var socket = null

ModeEnum = {
    SOCKET: 0,
    HTTP: 1,
}

MODE = ModeEnum.HTTP

devices = new Map();

$("body").ready(function() {
    console.log("running");

    if (MODE == ModeEnum.SOCKET) {
        socket = io();
        socket.on('connect', function() {
            console.log("websocket connected")
        });

        socket.on("devicePowerUsage", function(data) {
            for (var i = 0; i < data.devices.length; i ++) {
                updateGraphData(data.devices[i])
            }
        });
    }

    setInterval(function() {
        requestDevicePowerUsage()
    }, CHART_UPDATE_T)

    return;
});

function requestDevicePowerUsage() {
    // here is where we decide to use HTTP or SOCKET
    if (MODE == ModeEnum.SOCKET) {
        socket.emit("devicePowerUsageRequest")
    }
    else if (MODE == ModeEnum.HTTP) {
        $.ajax({
            method: "GET",
            url: "/devicePowerUsageRequest"
        }).done(function(response) {
            for (var i = 0; i < response.devices.length; i ++) {
                updateGraphData(response.devices[i])
            }
        });
    }
}

function updateGraphData(data) {
    var rcv_time = Date.now() / 1000
    var rcd_time = data.recorded_time;
    var difference = rcv_time - rcd_time

    // if the device id is not in devices,
    // add new HTML for it
    if (!devices.has(data.id)) {
        if (devices.size == 0) {
            $("#laundromats").html("")
        }
        $("#laundromats").append(buildDeviceHTML(data.id))

        var graph = getGraph(data.id)
        graph.lat_avgs = []
        graph.lat_print_count = 0
        devices.set(data.id, graph)
    }

    var graph = devices.get(data.id)

    var num = data.power_level
    graph.data.datasets[0].data.shift()
    graph.data.datasets[0].data.push(num)

    // calculate latency of data point
    if (graph.lat_avgs.length > 100) {
        graph.lat_avgs.shift()
    }
    graph.lat_avgs.push(difference)
    var avg_lat = graph.lat_avgs.reduce((a, b) => a + b) / graph.lat_avgs.length
    var avg_lat = (Math.round(avg_lat * 100) / 100).toFixed(2)

    var lat_string = "Latency: " + avg_lat + " s"

    if (graph.lat_print_count % 300 == 0) {
        console.log(lat_string)
    }
    graph.lat_print_count ++

    if (avg_lat > 15) {
        lat_string += " (appears to be disconnected)"
    }

    $("#" + data.id + "latency").html(lat_string)
    $("#" + data.id + "state").html("State: " + data.state)
    $("#" + data.id + "ect").html("ECT: " + data.ect)

    // calculate the max value in the data. Add 1 so it is never 0
    var max = Math.max.apply(null, graph.data.datasets[0].data)
    if (max <= 0) {
        max = 1
    }
    graph.options.scales.y.max = 1.05 * max

    graph.update()
}

function getGraph(id) {
    const NUM_DATA_POINTS = 30
    const MAX_VAL = 10

    const labels = new Array(NUM_DATA_POINTS)
    for (var i = 0; i < labels.length; i ++) {
        labels[i] = "T-" + (NUM_DATA_POINTS - (i + 2))
    }

    line_color = 'rgb(0, 200, 20)'
    point_color = line_color

    const data = {
        labels: labels,
        datasets: [{
            label: 'current (amps)',
            backgroundColor: point_color,
            borderColor: line_color,
            data: new Array(NUM_DATA_POINTS).fill(0),
            cubicInterpolationMode: 'monotone',
            tension: 1.0
        }]
    };

    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: MAX_VAL
                },
                x: {
                    min: 1,
                    max: NUM_DATA_POINTS - 2,
                }
            },
            animations: {
                x: {
                    easing: "linear",
                    duration: CHART_UPDATE_T,
                },
                y:{
                    easing: "linear",
                    duration: 0
                }
            }
        }
    };

    var graphname = "#" + id + "graph"
    const myChart = new Chart(
        $(graphname),
        config
    );
    return myChart
}
// builds and returns HTML for a list of devices
function buildDeviceHTML(id) {
    var html = ""

    var DEVICE_HTML =
        "<div class=\"devcontainer\">" +
            "<div><b>ID</b></div>" +
            "<div id=\"IDstate\">State: ...</div>" +
            "<div id=\"IDect\">ECT: ...</div>" +
            "<div id=\"IDlatency\">Latency: ...</div>" +
            "<div><canvas id='IDgraph'></canvas></div>" +
        "</div>"
    DEVICE_HTML = DEVICE_HTML.replaceAll("ID", id)

    html += DEVICE_HTML

    return html
}
