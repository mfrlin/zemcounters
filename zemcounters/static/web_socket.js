var url = "ws://localhost:8888/tail/";
console.log(url);
var ws = new WebSocket(url);

ws.onmessage = function(event) {
    console.log(JSON.parse(event.data));}