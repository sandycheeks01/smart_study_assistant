from awscrt import mqtt
from awsiot import mqtt_connection_builder
import json

ENDPOINT = ""
CLIENT_ID = ""
TOPIC = ""

PATH_TO_CERT = ""
PATH_TO_KEY = ""
PATH_TO_ROOT = ""

mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=PATH_TO_CERT,
    pri_key_filepath=PATH_TO_KEY,
    ca_filepath=PATH_TO_ROOT,
    client_id=CLIENT_ID,
    clean_session=False,
    keep_alive_secs=30
)

def connect_iot():
    mqtt_connection.connect().result()
    print("Connected to AWS IoT Core")

def publish_sensor_data(data):
    payload = json.dumps(data)
    mqtt_connection.publish(
        topic=TOPIC,
        payload=payload,
        qos=mqtt.QoS.AT_LEAST_ONCE
    )
    print("Published to AWS IoT:", payload)