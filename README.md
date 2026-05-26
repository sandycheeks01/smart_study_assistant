Setup Instructions

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
