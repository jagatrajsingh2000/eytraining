import json
import logging
import os
import time

import requests
from azure.servicebus import AutoLockRenewer, ServiceBusClient
from azure.servicebus.exceptions import MessageLockLostError
from dotenv import load_dotenv

from app.main import ProcessMealInput, process_meal
from app.observability.langsmith import traceable

load_dotenv()

SERVICE_BUS_CONNECTION_STRING = os.getenv("SERVICE_BUS_CONNECTION_STRING")
SERVICE_BUS_QUEUE_NAME = os.getenv("SERVICE_BUS_QUEUE_NAME", "meal-events")
SERVICE_BUS_LOCK_RENEWAL_SECONDS = int(os.getenv("SERVICE_BUS_LOCK_RENEWAL_SECONDS", "300"))
BACKEND_API_URL = os.getenv("BACKEND_API_URL")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
BUILD_MARKER = "orchestrator-deploy-probe-2026-07-02"
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("nutriguard.orchestrator.worker")


@traceable(name="NutriGuard Service Bus Meal Event", run_type="chain")
def handle_message(payload: dict) -> None:
    trace_id = payload.get("trace_id")
    meal_log_id = payload.get("meal_log_id")
    user_id = payload.get("user_id")
    logger.info("Processing meal event trace_id=%s meal_log_id=%s user_id=%s", trace_id, meal_log_id, user_id)
    result = process_meal(ProcessMealInput(**payload))
    response = requests.post(
        f"{BACKEND_API_URL}/internal/meal-results",
        json={
            "trace_id": trace_id,
            "meal_log_id": payload["meal_log_id"],
            **result,
        },
        headers={"x-internal-api-key": INTERNAL_API_KEY or ""},
        timeout=30,
    )
    response.raise_for_status()
    logger.info("Saved meal result trace_id=%s meal_log_id=%s backend_status=%s", trace_id, meal_log_id, response.status_code)


def run_worker() -> None:
    if not SERVICE_BUS_CONNECTION_STRING:
        raise RuntimeError("SERVICE_BUS_CONNECTION_STRING is not set")
    if not BACKEND_API_URL:
        raise RuntimeError("BACKEND_API_URL is not set")

    logger.info("NutriGuard orchestrator worker started: %s", BUILD_MARKER)
    with ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STRING) as client:
        receiver = client.get_queue_receiver(queue_name=SERVICE_BUS_QUEUE_NAME, max_wait_time=10)
        with receiver, AutoLockRenewer(max_lock_renewal_duration=SERVICE_BUS_LOCK_RENEWAL_SECONDS) as renewer:
            while True:
                messages = receiver.receive_messages(max_message_count=1, max_wait_time=10)
                if not messages:
                    time.sleep(1)
                    continue

                for message in messages:
                    try:
                        payload = json.loads(str(message))
                        renewer.register(
                            receiver,
                            message,
                            max_lock_renewal_duration=SERVICE_BUS_LOCK_RENEWAL_SECONDS,
                        )
                        logger.info(
                            "Received Service Bus message trace_id=%s message_id=%s",
                            payload.get("trace_id"),
                            message.message_id,
                        )
                        handle_message(payload)
                    except Exception:
                        logger.exception("Failed to process Service Bus message message_id=%s", message.message_id)
                        try:
                            receiver.abandon_message(message)
                        except MessageLockLostError:
                            logger.warning(
                                "Could not abandon message because lock was lost message_id=%s",
                                message.message_id,
                            )
                        raise
                    else:
                        try:
                            receiver.complete_message(message)
                        except MessageLockLostError:
                            logger.warning(
                                "Processed message but lock expired before completion trace_id=%s message_id=%s",
                                payload.get("trace_id"),
                                message.message_id,
                            )
                        else:
                            logger.info(
                                "Completed Service Bus message trace_id=%s message_id=%s",
                                payload.get("trace_id"),
                                message.message_id,
                            )


if __name__ == "__main__":
    run_worker()
