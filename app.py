from flask import Flask, render_template, jsonify, request
from datetime import datetime
import board
import adafruit_dht
from gpiozero import MotionSensor, DigitalInputDevice
from flask import Flask, redirect, url_for, session, render_template
from authlib.integrations.flask_client import OAuth
from functools import wraps
from dotenv import load_dotenv
from functools import wraps
from dynamodb_db import save_sensor_reading
import boto3
import json
import os
from iot_publisher import connect_iot, publish_sensor_data
from decimal import Decimal
from dynamodb_db import thresholds_table
from zoneinfo import ZoneInfo
from datetime import datetime


app = Flask(__name__)

connect_iot()

load_dotenv()

app.secret_key = os.getenv("SECRET_KEY", "smart-study-dev-secret-key")

oauth = OAuth(app)

COGNITO_REGION = os.getenv("COGNITO_REGION")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")

# registers AWS Cognito with Authlib using OpenID connect
oauth.register(
    name="oidc",
    client_id=os.getenv("COGNITO_CLIENT_ID"),
    client_secret=os.getenv("COGNITO_CLIENT_SECRET"),
    server_metadata_url=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

# custom decorator used to protect routes that require authentication from users

def login_required(route):
    @wraps(route)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return route(*args, **kwargs)
    return wrapper

# Sensor setup
dht_device = adafruit_dht.DHT22(board.D4)   # DHT22 OUT -> GPIO4
motion_sensor = MotionSensor(27)            # Motion OUT -> GPIO27
sound_sensor = DigitalInputDevice(22)       # Sound OUT -> GPIO22
light_sensor = DigitalInputDevice(13)       # Light OUT -> GPIO13

# Default settings
thresholds = {
    "temp_min": 18,
    "temp_max": 28,
    "humidity_min": 30,
    "humidity_max": 70,
    "require_motion": True,
    "allow_noise": False,
    "require_bright_light": True
}

history = []

# Calculate Comfort Scores

def calculate_comfort_score(temp, humidity, motion, sound, light):
    score = 100

    if temp is not None:
        if temp < thresholds["temp_min"] or temp > thresholds["temp_max"]:
            score -= 25

    if humidity is not None:
        if humidity < thresholds["humidity_min"] or humidity > thresholds["humidity_max"]:
            score -= 20

    if thresholds["require_motion"] and not motion:
        score -= 10

    if not thresholds["allow_noise"] and sound:
        score -= 20

    if thresholds["require_bright_light"] and not light:
        score -= 60

    return max(score, 0)


# Generate recommendations
def generate_recommendations(temp, humidity, motion, sound, light):
    recommendations = []

    if temp is not None:
        if temp > thresholds["temp_max"]:
            recommendations.append("Room is too hot. Consider opening a window or using a fan.")
        elif temp < thresholds["temp_min"]:
            recommendations.append("Room is too cold. Consider warming the room.")

    if humidity is not None:
        if humidity > thresholds["humidity_max"]:
            recommendations.append("Humidity is too high. The room may feel uncomfortable.")
        elif humidity < thresholds["humidity_min"]:
            recommendations.append("Humidity is too low. The air may feel dry.")

    if thresholds["require_motion"] and not motion:
        recommendations.append("No student detected. Study session may be inactive.")

    if not thresholds["allow_noise"] and sound:
        recommendations.append("Room is noisy. Try reducing background noise.")

    if thresholds["require_bright_light"] and not light:
        recommendations.append("Room is too dark. Turn on a light for better study comfort.")

    if not recommendations:
        recommendations.append("Environment looks comfortable for studying.")

    return recommendations

# Displays main dashboard for login users
@app.route("/")
@login_required
def index():
    user = session.get("user")
    return render_template("index.html", user=user)


# API route that gets sensor data from raspberry pi sensors

@app.route("/api/current")
@login_required
def current_data():

    # read temperature and humidity from sensor
    try:
        temperature = dht_device.temperature
        humidity = dht_device.humidity
    except RuntimeError:
        temperature = None
        humidity = None

    # motion detection for PIR sensor

    motion = motion_sensor.motion_detected

    # read sound and light sensor states

    sound = sound_sensor.value == 0

    light = light_sensor.value == 0

# calculation of overall comfort score
    comfort_score = calculate_comfort_score(
        temperature, humidity, motion, sound, light
    )

# generates study environment recommendations

    recommendations = generate_recommendations(
        temperature, humidity, motion, sound, light
    )

# Creates timestamp for current sensor readings
    timestamp = datetime.now().strftime("%H:%M:%S")

# Save temperature readings into history for charts
    if temperature is not None:
      history.append({
    "timestamp": datetime.now(
        ZoneInfo("Pacific/Auckland")
    ).strftime("%Y-%m-%d %H:%M:%S"),

    "temperature": temperature
})

    if len(history) > 30:
        history.pop(0)

    # Save sensor data to DynamoDB
    try:
        save_sensor_reading(
            temperature=temperature,
            humidity=humidity,
            motion_detected=motion,
            sound_level=int(sound),
            light_level=int(light),
            comfort_score=comfort_score
        )
    except Exception as e:
        print("DynamoDB save error:", e)

    # AWS IoT Publish
    try:
        sensor_payload = {
            "temperature": temperature,
            "humidity": humidity,
            "motion": motion,
            "sound": sound,
            "light": light,
            "comfort_score": comfort_score,
            "timestamp": timestamp
        }

        print("DynamoDB upload successful:", temperature,
    humidity,
    motion,
    sound,
    light,
    comfort_score)

        publish_sensor_data(sensor_payload)

    except Exception as e:
        print("AWS IoT publish error:", e)

    return jsonify({
        "temperature": temperature,
        "humidity": humidity,
        "motion": motion,
        "sound": sound,
        "light": light,
        "comfort_score": comfort_score,
        "recommendations": recommendations
    })

# API route that returns historical temperature data in JSON format
@app.route("/api/history")
def get_history():
    return jsonify(history)

# API route for updating threshold settings on the web interface
@app.route("/api/thresholds", methods=["POST"])
def update_thresholds():
    try:
        data = request.get_json()

        response = thresholds_table.get_item(
            Key={"settings_id": "default"}
        )

        current = response.get("Item", {})

        validated, error = validate_thresholds(data, current)

        if error:
            return jsonify({
                "success": False,
                "error": error
            }), 400

        updated_item = {
            "settings_id": "default",

            "temp_min": Decimal(str(validated["temp_min"])),
            "temp_max": Decimal(str(validated["temp_max"])),

            "humidity_min": Decimal(str(validated["humidity_min"])),
            "humidity_max": Decimal(str(validated["humidity_max"])),

            "light_enabled": validated["light_enabled"],
            "sound_enabled": validated["sound_enabled"],
            "motion_enabled": validated["motion_enabled"]
        }

        thresholds_table.put_item(Item=updated_item)

        return jsonify({
            "success": True,
            "message": "Threshold settings saved"
        })

    except Exception as e:
        print("Threshold update error:", e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

#LOGIN PRROTECTION HELPER
def login_required(route):
    @wraps(route)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return route(*args, **kwargs)
    return wrapper

#COGNITO ROUTES

@app.route("/login")
def login():

    if "user" in session:

        user_email = session["user"].get("email")

        return f"""
        <html>
        <head>
            <link rel="stylesheet" href="/static/style.css">
        </head>

        <body class="login-page">

            <div class="login-card">

                <h2 class="login-title">
                    You are already logged in as
                    <br><br>
                    {user_email}
                </h2>

                <a href="/" class="login-link">
                    <button class="login-button">
                        Go Back to Smart Study Assistant
                    </button>
                </a>

                <a href="/logout" class="login-link">
                    <button class="login-button">
                        Logout
                    </button>
                </a>

            </div>

        </body>
        </html>
        """

    redirect_uri = url_for("authorize", _external=True)

    return oauth.oidc.authorize_redirect(
        redirect_uri,
        prompt="login"
    )

# Handles authentication response after user log in 

@app.route("/authorize")
def authorize():
    token = oauth.oidc.authorize_access_token()
    user = token.get("userinfo")

    session["user"] = user

    return redirect(url_for("index"))

# logs user out of the smart study assitant
@app.route("/logout")
def logout():
    session.clear()

    cognito_logout_url = (
        f"{os.getenv('COGNITO_DOMAIN')}/logout"
        f"?client_id={os.getenv('COGNITO_CLIENT_ID')}"
        f"&logout_uri=http://localhost:5000/logged-out"
    )

    return redirect(cognito_logout_url)

# shows the page that confirms the user has logged out
@app.route("/logged-out")
def logged_out():
    return render_template("loggedout.html")

# AWS LAMBDA

lambda_client = boto3.client("lambda", region_name="us-east-1")

@app.route("/api/lambda-analysis")
def lambda_analysis():
    try:
        response = lambda_client.invoke(
            FunctionName="SmartStudyAnalysisLambda",
            InvocationType="RequestResponse",
            Payload=json.dumps({})
        )

        payload_text = response["Payload"].read().decode("utf-8")
        print("Raw Lambda payload text:", payload_text)

        payload = json.loads(payload_text)

        body = json.loads(payload.get("body", "{}"))

        return jsonify({
            "comfort_score": body.get("comfort_score", 0),
            "status": body.get("status", "Unknown"),
            "recommendation": body.get("recommendation", "No recommendation returned.")
        })

    except Exception as e:
        print("Lambda error:", repr(e))
        return jsonify({
            "status": "Error",
            "recommendation": str(e)
        }), 500

# Threshold validation

def validate_thresholds(data, current_thresholds):
    """
    Validate threshold values submitted by the user.
    """

    if not data:
        return None, "No threshold data was provided."

    validated = {}

    try:

        validated["temp_min"] = float(
            data.get("temp_min", current_thresholds.get("temp_min", 18))
        )

        validated["temp_max"] = float(
            data.get("temp_max", current_thresholds.get("temp_max", 30))
        )

        validated["humidity_min"] = float(
            data.get("humidity_min", current_thresholds.get("humidity_min", 30))
        )

        validated["humidity_max"] = float(
            data.get("humidity_max", current_thresholds.get("humidity_max", 70))
        )

    except (TypeError, ValueError):
        return None, "Temperature and humidity values must be numeric."

    # Temperature range validation
    if not (-20 <= validated["temp_min"] <= 60 and
            -20 <= validated["temp_max"] <= 60):

        return None, "Temperature thresholds must be between -20°C and 60°C."

    # Humidity range validation
    if not (0 <= validated["humidity_min"] <= 100 and
            0 <= validated["humidity_max"] <= 100):

        return None, "Humidity thresholds must be between 0% and 100%."

    # Logical validation
    if validated["temp_min"] >= validated["temp_max"]:
        return None, "Temperature min must be lower than temperature max."

    if validated["humidity_min"] >= validated["humidity_max"]:
        return None, "Humidity min must be lower than humidity max."

    # Checkbox settings
    validated["light_enabled"] = data.get(
        "light_enabled",
        current_thresholds.get("light_enabled", True)
    )

    validated["sound_enabled"] = data.get(
        "sound_enabled",
        current_thresholds.get("sound_enabled", True)
    )

    validated["motion_enabled"] = data.get(
        "motion_enabled",
        current_thresholds.get("motion_enabled", True)
    )

    return validated, None

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True, use_reloader=False)

