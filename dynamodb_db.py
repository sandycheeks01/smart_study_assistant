import boto3
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1"
)

table = dynamodb.Table("smart-study-sensor-readings")
thresholds_table = dynamodb.Table("smart-study-thresholds")

def save_sensor_reading(
    temperature,
    humidity,
    motion_detected,
    sound_level=None,
    light_level=None,
    comfort_score=None
):
    timestamp = datetime.now(
        ZoneInfo("Pacific/Auckland")
    ).isoformat()

    item = {
        "device_id": "smart-study-pi-01",
        "timestamp": timestamp,
        "motion_detected": motion_detected,
        "sound_level": sound_level,
        "light_level": light_level
    }

    if temperature is not None:
        item["temperature"] = Decimal(str(temperature))

    if humidity is not None:
        item["humidity"] = Decimal(str(humidity))

    if comfort_score is not None:
        item["comfort_score"] = Decimal(str(comfort_score))

    table.put_item(Item=item)

    return item