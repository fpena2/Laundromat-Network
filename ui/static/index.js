
// constants
const CHART_UPDATE_T = 1000

var socket = null

testChart = null

device_graphs = new Map();

$("body").ready(function() {
    console.log("running");

    socket = io();
    socket.on('connect', function() {
        console.log("websocket connected")
    });

    socket.on("inputDataResponse", function(data) {
        console.log("received input data response. Data: " + data)
        $("#server_response").html(data)
    });

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

function sendMessageToServer() {
    console.log("Sending message to server.")
    var message = $("#input").val()
    console.log("message: " + message)
    socket.emit("inputDataEvent", message)
    console.log("...done.")
}

function getLaundromatData() {
    console.log("Requesting laundromat data from server")
    $.ajax({
        method: "GET",
        url: "/laundromats"
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
                var num = Math.random() * 10 + 1
                graph.data.datasets[0].data.shift()
                graph.data.datasets[0].data.push(num)
                graph.update()
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
    html += buildDevicesHTML("drier", lm_info.num_driers, lm_info.id)
    
    return html
}

function addGraphs(lm) {
    for(var i = 0; i < lm.num_driers; i ++) {
        var key = "" + lm.id + "drier" + i
        var graph = getGraph(lm.id, "drier", i)
        device_graphs.set(key, graph)
    }

    for(var i = 0; i < lm.num_washers; i ++) {
        var key = "" + lm.id + "washer" + i
        var graph = getGraph(lm.id, "washer", i)
        device_graphs.set(key, graph)
    }
}

function getGraph(lmid, d_name, d_id) {
    const NUM_DATA_POINTS = 30
    const MAX_VAL = 11

    const labels = new Array(NUM_DATA_POINTS)
    for (var i = 0; i < labels.length; i ++) {
        labels[i] = "T-" + (NUM_DATA_POINTS - (i + 1))
    }

    const data = {
        labels: labels,
        datasets: [{
            label: 'power (watts)',
            backgroundColor: 'rgb(255, 99, 132)',
            borderColor: 'rgb(255, 99, 132)',
            data: new Array(NUM_DATA_POINTS).fill(0),
            cubicInterpolationMode: 'monotone',
            tension: 0.4
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

    var DEVICE_STATUS_HTML = "<div id='DEVICENAME_DEVICEID_LMID'> DEVICENAME DEVICEID: <span class='device_off'>OFF</span></div>"
    var DEVICE_GRAPH_HTML = "<div class='chart_container'><canvas id='LMIDDEVICENAMEDEVICEIDgraph'></canvas></div>"
    for(var i = 0; i < num_devices; i ++) {
        html += DEVICE_STATUS_HTML.replaceAll("DEVICENAME", d_name).replaceAll("DEVICEID", i).replaceAll("LMID", lmid)
        html += DEVICE_GRAPH_HTML.replaceAll("DEVICENAME", d_name).replaceAll("DEVICEID", i).replaceAll("LMID", lmid)
    }

    html += "</div>"

    return html
}

