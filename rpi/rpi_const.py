MQTT_BROKER_IP = "192.168.10.238"  # set this!!!
MQTT_CLIENT_ID = None
MQTT_BROKER_USERNAME = None
MQTT_BROKER_PASSWORD = None
MQTT_RECONNECT_INTERVAL = 13  # [seconds]
LOG_TO_CONSOLE = False
LOG_LEVEL_DEBUG = False

TOPIC_PREFIX = "loraben/"
TOPIC_PUB_MSG = f"{TOPIC_PREFIX}msg"
SUB_TOPICS = frozenset(
    [
        TOPIC_PREFIX + t
        for t in [
            "ping",
            "noop",
        ]
    ]
)
