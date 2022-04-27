// constant//s
const CHART_UPDATE_T = 1000

var socket = null

ModeEnum = {
    SOCKET: 0,
    HTTP: 1,
}

MODE = ModeEnum.HTTP;

devices = new Map();
current_lm_id = "";
reqInterval = null;
clickable = true;
var global_avg_lat = 0.0;
var N_ = 0;
var disconnected_cnt = 0;

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
            console.log("global average = ", global_avg_lat/N_);
            console.log("number disconnected = ", disconnected_cnt);
            global_avg_lat = 0.0;
            N_ = 0;
            disconnected_cnt = 0;
        });
    }

    $.ajax({
        method: "GET",
        url: "/laundromatlist",
    }).done(function(response) {
        var template = "<div id=\"lm_HTMLID\" class=\"lm_name button\">ID</div>"
        var lms = response.laundromats
        if (lms.length == 0) {
            $("#lm_list").html("Error: No laundromats connected to server..." +
                "Try refreshing when some are");
        } else {
            var html = "";
            for (var i = 0; i < lms.length; i ++) {
                htmlid = lms[i].replaceAll(" ", "_")
                html += template.replaceAll("HTMLID", htmlid).replaceAll("ID", lms[i])
            }
            $("#lm_list").html(html)
        }

        // apparently it is important to do this after building the html
        $(".lm_name").click(function(a) {
            if (!clickable) {
                return
            }

            $("#lm_selection_container").addClass("out")
            $("#device_list_container").removeClass("out")
            var lm_name = $("#" + a.target.id).html()
            $("#lm_title").html(lm_name)
            current_lm_id = lm_name

            requestDevicePowerUsage()
            reqInterval = setInterval(function() {
                requestDevicePowerUsage()
            }, CHART_UPDATE_T)
        });

        $("#return_button").click(function() {
            $("#lm_selection_container").removeClass("out")
            $("#device_list_container").addClass("out")
            clickable = false
            setTimeout(function() {
                $("#devices").html("Waiting for devices to begin transmitting data...")
                devices.clear()
                current_lm_id = ""
                clickable = true
            }, 1000)
            clearInterval(reqInterval)
        });

    });

    return;
});

function requestDevicePowerUsage() {
    if (current_lm_id == "") {
        return
    }
    data = {
        "laundromatid": current_lm_id
    }
    if (MODE == ModeEnum.SOCKET) {
        socket.emit("devicePowerUsageRequest", data)
    }
    else if (MODE == ModeEnum.HTTP) {
        $.ajax({
            method: "GET",
            url: "/devicePowerUsageRequest",
            data: data
        }).done(function(response) {
            num_devices_ = response.devices.length
            for (var i = 0; i < response.devices.length; i ++) {
                updateGraphData(response.devices[i])
            }
            console.log("global average = ", global_avg_lat/N_);
            global_avg_lat = 0.0;
            N_ = 0;
            disconnected_cnt = 0;
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
            $("#devices").html("")
        }
        $("#devices").append(buildDeviceHTML(data.id))

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
    N_ += 1;
    global_avg_lat += avg_lat;
    var avg_lat = (Math.round(avg_lat * 100) / 100).toFixed(2)
    // global_avg_lat += (1 - 1/N_)*global_avg_lat + (1/N_)*avg_lat;

    var lat_string = "latency: " + avg_lat + " s"

    if (graph.lat_print_count % 300 == 0) {
        console.log(data.id + " " + lat_string)
    }
    graph.lat_print_count ++

    if (avg_lat > 15) {
        lat_string += " (appears to be disconnected)"
        disconnected_cnt += 1;
    }

    $("#" + data.id + "latency").html(lat_string)
    $("#" + data.id + "state").html("State: " + data.state)
    $("#" + data.id + "ect").html("ECT: " + data.ect)

    // calculate the max value in the data. Add 1 so it is never 0
    var max = Math.max.apply(null, graph.data.datasets[0].data)
    if (max <= 0) {
        max = 1
    }
    DEFAULT_MAX = 6
    newgraphmax = DEFAULT_MAX > max ? DEFAULT_MAX : max
    graph.options.scales.y.max = newgraphmax * 1.05

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
            tension: 1.0,
            pointRadius: 0,
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

// add geographical map with laundromant locations to html
let geo_map;
let directions_renderer; 
let directions_service;

function init_map() {
    /*
     * renders map
     */
    $.ajax({
        method: "GET",
        url: "/locations"
    }).done(function(response) {
        let map_zoom = 11
        let min_lat = 10000
        let max_lon = -10000
        let markers = []
        
        geo_map = new google.maps.Map(document.getElementById("map"), {
            center: { lat: 38.63500, lng: -90.508 },
            zoom: map_zoom,
        });
        directions_renderer = new google.maps.DirectionsRenderer();
        directions_service = new google.maps.DirectionsService();
        directions_renderer.setMap(geo_map);

        console.log("length: ", response.laundromats.length)
        for (let i = 0; i < response.laundromats.length; i++) {
            loc = JSON.parse(response.laundromats[i]);

            let laundro_name = `laundromat ${i}`
            let marker = new google.maps.Marker({
                position: new google.maps.LatLng(loc.lat, loc.lon), 
                geo_map,
                title: laundro_name
            });
            marker.setMap(geo_map)

            let infowindow = new google.maps.InfoWindow({
                content: laundro_name
            });
            google.maps.event.addListener(marker, 'click', function() {
                infowindow.open(map,marker);
            });

            min_lat = Math.min(min_lat, loc.lat);
            max_lon = Math.max(max_lon, loc.lon);
        }

        geo_map.setCenter(new google.maps.LatLng(min_lat + 0.05 , max_lon));

    }); 

}

function _display_route_helper(user_pos) {
    let travel_mode = document.getElementById('mode').value;

    $.ajax({
        method: "GET",
        url: "/find_laundromat",
        data: {lat: user_pos.coords.latitude, lon: user_pos.coords.longitude}
    }).done(function (response) {
        let recommended_laundromat = response.laundromat;
        let directions_request = {
            origin: {lat: user_pos.coords.latitude, lng: user_pos.coords.longitude},
            destination: {lat: recommended_laundromat.lat, lng: recommended_laundromat.lon},
            travelMode: google.maps.TravelMode[travel_mode]
        };
        

        directions_service.route(directions_request, function (response, status_) {
            if (status_ == "OK") {
                directions_renderer.setDirections(response);
            }
        });
    });
}

function _display_route_err_handler(err) {
    console.log(err);
}

function display_route() {
    /*
     * computes and renders the route from one current user location to laundromat
     * TODO: receive laundromat recommendation from server
     */
    let user_lat = 0; let user_lon = 0;
    if (!navigator.geolocation) {
        return;
    }

    navigator.geolocation.getCurrentPosition(_display_route_helper, _display_route_err_handler); 
}

