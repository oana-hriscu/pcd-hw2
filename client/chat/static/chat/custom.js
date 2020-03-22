var socket;

var username = "client-" + Math.floor(Math.random() * 10000);

// Connect to the WebSocket and setup listeners
function setupWebSocket() {
    socket = new ReconnectingWebSocket("wss://iqbkep1qs7.execute-api.eu-west-1.amazonaws.com/dev");

    socket.onopen = function(event) {
        data = {"action": "getRecentMessages"};
        socket.send(JSON.stringify(data));
    };

    socket.onmessage = function(message) {
        var data = JSON.parse(message.data);
        data["messages"].forEach(function(message) {
            if ($("#message-container").children(0).attr("id") == "empty-message") {
                $("#message-container").empty();
            }
            if (message["username"] === username) {
                $("#message-container").append("<div class='message self-message'><b>(You)</b> " + message["content"]);
            } else {
                $("#message-container").append("<div class='message'><b>(" + message["username"] + ")</b> " + message["content"]);
            }
            $("#message-container").children().last()[0].scrollIntoView();
        });
    };
}


function postMessage() {
    console.log("test");
    var content = $("#post-bar").val();
    if (content !== "") {
        data = {"action": "sendMessage", "username": username, "content": content};
        socket.send(JSON.stringify(data));
        $("#post-bar").val("");
    }
}