var url = "ws://" + location.host + "/tail/3";
var ws = new WebSocket(url);

ws.onmessage = function(event) {
    console.log(JSON.parse(event.data));}