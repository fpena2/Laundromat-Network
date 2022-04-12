// constants
const CHART_UPDATE_T = 1000

var socket = null

testChart = null

ModeEnum = {
    SOCKET: 0,
    HTTP: 1,
}

MODE = ModeEnum.SOCKET

device_graphs = new Map();

$("body").ready(function() {
    console.log("running");

    if (MODE == ModeEnum.SOCKET) {
        socket = io();
        socket.on('connect', function() {
            console.log("websocket connected")
        });

        socket.on("devicePowerUsage", function(data) {
            updateGraphData(data)
        });
    }

    getLaundromatData()

    return;
});

// adds the onclick function to device_list_title class
function addDeviceListTitleOnClick() {
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
}

function requestDevicePowerUsage(lmid, device, deviceid) {
    var data = {
        "lmid": lmid,
        "device": device,
        "deviceid": deviceid
    }

    // here is where we decide to use HTTP or SOCKET
    if (MODE == ModeEnum.SOCKET) {
        socket.emit("devicePowerUsageRequest", data)
    }
    else if (MODE == ModeEnum.HTTP) {
        $.ajax({
            method: "GET",
            url: "/devicePowerUsageRequest",
            data: data
        }).done(function(response) {
            updateGraphData(response)
        });

    }
}

function updateGraphData(data) {
    var rcv_time = Date.now() / 1000
    var rcd_time = data.recorded_time;
    var difference = rcv_time - rcd_time

    var key = "" + data.lmid + data.device + data.deviceid
    var graph = device_graphs.get(key)
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

    var lat_string = data.device + " " + data.deviceid + ". latency: " + avg_lat + " s"

    if (graph.lat_print_count % 300 == 0) {
        console.log(lat_string)
    }
    graph.lat_print_count ++

    if (avg_lat > 15) {
        lat_string += " (appears to be disconnected)"
    }

    $("#" + data.device + "_" + data.deviceid + "_" + data.lmid).html(lat_string)

    // calculate the max value in the data. Add 1 so it is never 0
    var max = Math.max.apply(null, graph.data.datasets[0].data)
    if (max <= 0) {
        max = 1
    }
    graph.options.scales.y.max = 1.05 * max

    graph.update()
}

function getLaundromatData() {
    console.log("Requesting laundromat data from server")
    $.ajax({
        method: "GET",
        url: "/laundromat",
        data: { "longitude": 38.78169995906734, "latitude": -90.52582140779946 }
    }).done(function(response) {
        console.log("received laundromat data... response:")
        console.log(response)
        var html = ""
        for(var i = 0; i < response.laundromats.length; i ++) {
            console.log("Building HTML for laundromat " + i);
            html += buildLaundromatHTML(response.laundromats[i])
        }

        $("#laundromats").html(html)

        addDeviceListTitleOnClick()

        for(var i = 0; i < response.laundromats.length; i ++) {
            addGraphs(response.laundromats[i])
        }

        setInterval(function() {
            for(const graph of device_graphs.values()) {
                requestDevicePowerUsage(graph.lmid, graph.device, graph.id)
            }
        }, CHART_UPDATE_T)
    });
}

// builds all HTML for a single laundromat
function buildLaundromatHTML(lm_info) {
    var html = ""

    // Build the lm name html first
    //    LMID = laundromat id i.e. 1234 or 15000
    var LM_NAME_HTML = "<div id='lmname_LMID'>LMNAME</div>"
    html += LM_NAME_HTML.replaceAll("LMID", lm_info.id).replaceAll("LMNAME", lm_info.name)

    html += buildDevicesHTML("washer", lm_info.num_washers, lm_info.id)
    html += buildDevicesHTML("dryer", lm_info.num_dryers, lm_info.id)

    return html
}

function addGraphs(lm) {
    for(var i = 0; i < lm.num_dryers; i ++) {
        var key = "" + lm.id + "dryer" + i
        var graph = getGraph(lm.id, "dryer", i)
        graph.lmid = lm.id
        graph.device = "dryer"
        graph.id = i
        graph.lat_avgs = []
        graph.lat_print_count = 0
        device_graphs.set(key, graph)
    }

    for(var i = 0; i < lm.num_washers; i ++) {
        var key = "" + lm.id + "washer" + i
        var graph = getGraph(lm.id, "washer", i)
        graph.lmid = lm.id
        graph.device = "washer"
        graph.id = i
        graph.lat_avgs = []
        graph.lat_print_count = 0
        device_graphs.set(key, graph)
    }
}

function getGraph(lmid, d_name, d_id) {
    const NUM_DATA_POINTS = 30
    const MAX_VAL = 10

    const labels = new Array(NUM_DATA_POINTS)
    for (var i = 0; i < labels.length; i ++) {
        labels[i] = "T-" + (NUM_DATA_POINTS - (i + 2))
    }

    line_color = 'rgb(186, 0, 6)'
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

    var graphname = "#" + lmid + d_name + d_id + "graph"
    const myChart = new Chart(
        $(graphname),
        config
    );
    return myChart
}

// builds and returns HTML for a list of devices
function buildDevicesHTML(d_name, num_devices, lmid) {
    var html = ""

    var DEVICE_LIST_TITLE_HTML = "<div class='device_list_title' id='DEVICENAME_title_LMID'> DEVICENAMEs </div>"
    html += DEVICE_LIST_TITLE_HTML.replaceAll("DEVICENAME", d_name).replaceAll("LMID", lmid);

    var DEVICE_LIST_HTML = "<div id='DEVICENAME_LMID' class='device_list'>"
    html += DEVICE_LIST_HTML.replaceAll("DEVICENAME", d_name).replaceAll("LMID", lmid)

    var DEVICE_STATUS_HTML = "<div id='DEVICENAME_DEVICEID_LMID'> DEVICENAME DEVICEID:</div>"
    var DEVICE_GRAPH_HTML = "<div class='chart_container'><canvas id='LMIDDEVICENAMEDEVICEIDgraph'></canvas></div>"
    for(var i = 0; i < num_devices; i ++) {
        html += DEVICE_STATUS_HTML.replaceAll("DEVICENAME", d_name).replaceAll("DEVICEID", i).replaceAll("LMID", lmid)
        html += DEVICE_GRAPH_HTML.replaceAll("DEVICENAME", d_name).replaceAll("DEVICEID", i).replaceAll("LMID", lmid)
    }

    html += "</div>"

    return html
}

