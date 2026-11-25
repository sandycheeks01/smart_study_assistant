# Smart Study Assistant  
  
An IoT study-environment monitor built on a Raspberry Pi. Four physical sensors  
track temperature, humidity, motion, noise, and light levels in a study space.  
A Flask web app computes a live **Comfort Score (0–100)**, generates  
recommendations (e.g. "Room is too dark — turn on a light"), and displays  
everything on a real-time dashboard that refreshes every 5 seconds.  
  
Sensor data is also streamed to the cloud: readings are published to  
**AWS IoT Core** over MQTT (secured with mutual TLS certificates), stored in  
**AWS DynamoDB** for history, and analysed by an **AWS Lambda** function that  
returns an overall status and recommendation. Dashboard access is protected  
by **AWS Cognito** login (OpenID Connect).  
  
## Features  
  
- 📊 Live dashboard with temperature chart and comfort score gauge (Chart.js)  
- ⚠️ Active warnings panel with plain-English recommendations  
- 🎛️ User-configurable thresholds for temperature, humidity, and sensor toggles  
- 🔐 Cognito OIDC authentication protecting the dashboard  
- ☁️ MQTT telemetry to AWS IoT Core + persistent storage in DynamoDB  
- 🧠 Serverless analysis via AWS Lambda  
  
## Tech Stack  
  
| Layer | Technology |  
|---|---|  
| Hardware | Raspberry Pi, DHT22, SR602 PIR, sound & light sensors (GPIO) |  
| Backend | Python, Flask, gpiozero, Adafruit CircuitPython |  
| Frontend | HTML/CSS/JS, Chart.js |  
| Cloud | AWS IoT Core (MQTT/mTLS), DynamoDB, Lambda, Cognito |  
  
## How It Works  
  
1. The Flask server reads all four sensors on each `/api/current` request.  
2. `calculate_comfort_score()` starts at 100 and deducts points for  
   out-of-range temperature (−25), humidity (−20), noise (−20),  
   no motion (−10), or darkness (−60).  
3. `generate_recommendations()` turns violations into actionable advice.  
4. Each reading is saved to DynamoDB and published to AWS IoT Core.  
5. The dashboard polls every 5 seconds and also invokes  
   `SmartStudyAnalysisLambda` for higher-level insights.

## Setup Instructions

You will need to setup the sensors, jumper wires, breadboard, with the raspberry pi.

Hardware Sensor

- DHT22 humidity & temperature sensor AM2302 Module+ Cable
  Measures room temperature and humidity
- Optical Sensitive Resistance Light Detection Photosensitive Sensor
  Detects whether the room is bright or dark
- Sound Sensor Module
  Detect the noise level of the study environment
- SR602 MINI Pyroelectric Infrared Motion Sensor
  Detects whether a student is present

Other components

- Breadboard
- Dupont Wires (Jumper Wires) Male to Male
- T Cobbler

AWS certificates were excluded for security reasons

1. Download the Project

2. Setup AWS IoT Core. Update the certificates in the iot_publisher.py as needed.

3. Setup AWS DynamoDB

4. Setup AWS Lambda

5. Setup AWS Cognito User Pools

6. Open Project Folder and Create Virtual Environment

python3 -m venv venv
source venv/bin/activate

7. Install Dependencies

The project dependencies are defined in a requirements.txt file to ensure consistent setup across environments. Enter this in the VSCode terminal:

pip install -r requirements.txt

8. Configure AWS Credentials

Configure AWS credentials by typing this in the VSCode terminal:

aws configure

9. Run the Application by typing this in terminal:

python app.py

10. Then click the Ctrl + Click the link

http://localhost:5000
