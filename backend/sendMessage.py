import boto3
import logging
import time
import json

logger = logging.getLogger("handler_logger")
logger.setLevel(logging.DEBUG)

dynamodb = boto3.resource("dynamodb")


def _get_response(status_code, body):
    if not isinstance(body, str):
        body = json.dumps(body)
    return {"statusCode": status_code, "body": body}


def _get_body(event):
    try:
        return json.loads(event.get("body", ""))
    except:
        logger.debug("event body could not be JSON decoded.")
        return {}


def _send_to_connection(connection_id, data, event):
    gatewayapi = boto3.client("apigatewaymanagementapi",
            endpoint_url = "https://" + event["requestContext"]["domainName"] +
                    "/" + event["requestContext"]["stage"])
    return gatewayapi.post_to_connection(Data=json.dumps(data).encode('utf-8'), ConnectionId=connection_id)


def send_message(event, context):
    """
    When a message is sent on the socket, forward it to all connections.
    """
    logger.info("Message sent on WebSocket.")

    # Ensure all required fields were provided
    body = _get_body(event)
    for attribute in ["username", "content"]:
        if attribute not in body:
            logger.debug("Failed: '{}' not in message dict.".format(attribute))
            return _get_response(400, "'{}' not in message dict".format(attribute))

    table = dynamodb.Table("serverless-chat_Messages")
    response = table.query(KeyConditionExpression="Room = :room",
                           ExpressionAttributeValues={":room": "general"},
                           Limit=1, ScanIndexForward=False)
    items = response.get("Items", [])
    index = items[0]["Index"] + 1 if len(items) > 0 else 0

    # Add the new message to the database
    timestamp = int(time.time())
    username = body["username"]
    content = body["content"]
    table.put_item(Item={"Room": "general", "Index": index,
                         "Timestamp": timestamp, "Username": username,
                         "Content": content})

    # Get all current connections
    table = dynamodb.Table("serverless-chat_Connections")
    response = table.scan(ProjectionExpression="ConnectionID")
    items = response.get("Items", [])
    connections = [x["ConnectionID"] for x in items if "ConnectionID" in x]

    # Send the message data to all connections
    message = {"username": username, "content": content}
    logger.debug("Broadcasting message: {}".format(message))
    data = {"messages": [message]}
    for connectionID in connections:
        _send_to_connection(connectionID, data, event)

    return _get_response(200, "Message sent to all connections.")