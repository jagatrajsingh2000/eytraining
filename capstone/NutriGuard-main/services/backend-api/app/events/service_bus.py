import json
import os

from azure.servicebus import ServiceBusClient, ServiceBusMessage


SERVICE_BUS_CONNECTION_STRING = os.getenv("SERVICE_BUS_CONNECTION_STRING")
SERVICE_BUS_QUEUE_NAME = os.getenv("SERVICE_BUS_QUEUE_NAME", "meal-events")


def publish_meal_event(payload: dict) -> None:
    if not SERVICE_BUS_CONNECTION_STRING:
        raise RuntimeError("SERVICE_BUS_CONNECTION_STRING is not set")

    message = ServiceBusMessage(json.dumps(payload))
    with ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STRING) as client:
        with client.get_queue_sender(queue_name=SERVICE_BUS_QUEUE_NAME) as sender:
            sender.send_messages(message)

