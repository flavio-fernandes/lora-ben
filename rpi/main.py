#!/usr/bin/env python
import asyncio
import collections
from contextlib import AsyncExitStack

from asyncio_mqtt import Client, MqttError

from rpi import rpi_const as const
from rpi import log
from rpi.events import MqttMsgEvent
from rpi.basic_receive import (
    basic_receive_main,
    get_latest,
    stop_basic_receive,
)
from rpi.mqtt import (
    handle_mqtt_publish,
    handle_mqtt_messages,
)


async def handle_main_event_mqtt(mqtt_msg: MqttMsgEvent, mqtt_send_q: asyncio.Queue):
    if mqtt_msg.topic in const.SUB_TOPICS:
        msg = f"Mqtt event received {mqtt_msg.topic} {mqtt_msg.payload}"
        logger.info(msg)
        if mqtt_msg.topic.endswith("/ping"):
            curr_values = get_latest()
            await publish_values(curr_values, curr_values, mqtt_send_q)
        return

    msg = f"Ignoring Mqtt event received {mqtt_msg.topic} {mqtt_msg.payload}"
    logger.debug(msg)


async def handle_main_events(mqtt_send_q: asyncio.Queue, main_events_q: asyncio.Queue):
    handlers = {
        "MqttMsgEvent": handle_main_event_mqtt,
    }
    while not stop_gracefully:
        main_event = await main_events_q.get()
        logger.debug(f"Handling {main_event.event}...")
        handler = handlers.get(main_event.event)
        if handler:
            await handler(main_event, mqtt_send_q)
        else:
            logger.error(f"No handler found for {main_event.event}")
        main_events_q.task_done()


async def cancel_tasks(tasks):
    logger.info("Cancelling all tasks")
    for task in tasks:
        if task.done():
            continue
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def publish_values(curr_values, delta_values, mqtt_send_q: asyncio.Queue):
    logger.info(
        f"publishing {const.TOPIC_PUB_MSG}:{curr_values} and sub-topics {sorted(delta_values.keys())}"
    )

    await mqtt_send_q.put(
        MqttMsgEvent(topic=const.TOPIC_PUB_MSG, payload=f"{curr_values}")
    )
    for topic, payload in delta_values.items():
        await mqtt_send_q.put(
            MqttMsgEvent(topic=f"{const.TOPIC_PREFIX}{topic}", payload=f"{payload}")
        )


async def monitor_latest_receive(mqtt_send_q: asyncio.Queue):
    prev_values = {}
    while not stop_gracefully:
        await asyncio.sleep(1)
        curr_values = get_latest()

        if prev_values == curr_values:
            continue

        prev_set = set(prev_values.items())
        curr_set = set(curr_values.items())
        await publish_values(curr_values, dict(curr_set - prev_set), mqtt_send_q)
        prev_values = curr_values.copy()


async def main_loop():
    global stop_gracefully

    # https://pypi.org/project/asyncio-mqtt/
    logger.debug("Starting main event processing loop")
    mqtt_broker_ip = const.MQTT_BROKER_IP
    mqtt_username = const.MQTT_BROKER_USERNAME
    mqtt_password = const.MQTT_BROKER_PASSWORD
    mqtt_client_id = const.MQTT_CLIENT_ID
    mqtt_send_q = asyncio.Queue(maxsize=256)
    main_events_q = asyncio.Queue(maxsize=256)

    async with AsyncExitStack() as stack:
        # Keep track of the asyncio tasks that we create, so that
        # we can cancel them on exit
        tasks = set()
        stack.push_async_callback(cancel_tasks, tasks)

        client = Client(
            mqtt_broker_ip,
            username=mqtt_username,
            password=mqtt_password,
            client_id=mqtt_client_id,
        )
        await stack.enter_async_context(client)

        messages = await stack.enter_async_context(client.messages())
        task = asyncio.create_task(handle_mqtt_messages(messages, main_events_q))
        tasks.add(task)

        task = asyncio.create_task(handle_mqtt_publish(client, mqtt_send_q))
        tasks.add(task)

        for topic in const.SUB_TOPICS:
            await client.subscribe(topic)

        task = asyncio.create_task(handle_main_events(mqtt_send_q, main_events_q))
        tasks.add(task)

        quiet = not (const.LOG_TO_CONSOLE and const.LOG_LEVEL_DEBUG)
        task = asyncio.create_task(basic_receive_main(quiet=quiet))
        tasks.add(task)

        task = asyncio.create_task(monitor_latest_receive(mqtt_send_q))
        tasks.add(task)

        # Wait for everything to complete (or fail due to, e.g., network errors)
        await asyncio.gather(*tasks)

    logger.debug("all done!")


# cfg_globals
stop_gracefully = False
logger = None


async def main():
    global stop_gracefully

    # Run the loop indefinitely. Reconnect automatically if the connection is lost.
    reconnect_interval = const.MQTT_RECONNECT_INTERVAL
    while not stop_gracefully:
        try:
            await main_loop()
        except MqttError as error:
            logger.warning(
                f'MQTT error "{error}". Reconnecting in {reconnect_interval} seconds.'
            )
        except (KeyboardInterrupt, SystemExit):
            logger.info("got KeyboardInterrupt")
            stop_gracefully = True
            stop_basic_receive()
            break
        await asyncio.sleep(reconnect_interval)


if __name__ == "__main__":
    logger = log.getLogger()
    log.initLogger()

    if const.LOG_TO_CONSOLE:
        log.log_to_console()
    if const.LOG_LEVEL_DEBUG:
        log.set_log_level_debug()

    logger.info("main process started")
    asyncio.run(main())
    if not stop_gracefully:
        raise RuntimeError("main is exiting")
