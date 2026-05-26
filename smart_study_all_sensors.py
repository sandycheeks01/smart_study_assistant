import RPi.GPIO as GPIO
import time
import board
import adafruit_dht
from gpiozero import MotionSensor, DigitalInputDevice


# Sensor setup

# DHT22: OUT -> GPIO4, physical pin 7
dht_device = adafruit_dht.DHT22(board.D4)

# SR602 Motion Sensor: OUT -> GPIO27, physical pin 13
motion_sensor = MotionSensor(27)

# Sound Sensor: OUT -> GPIO22, physical pin 11
sound_sensor = DigitalInputDevice(22)

# Sound Sensor: OUT -> GPIO22, physical pin 33
light_sensor = DigitalInputDevice(13)

print("Smart Study Assistant starting...")
print("Waiting for motion sensor to settle...")
motion_sensor.wait_for_no_motion()
print("System ready!")

while True:
    try:
        temperature = dht_device.temperature
        humidity = dht_device.humidity

        motion_status = "Motion detected" if motion_sensor.motion_detected else "No motion"

        sound_status = "Sound detected" if sound_sensor.value == 0 else "Quiet"

        light_status = "Dark" if light_sensor.value == 1 else "Bright"
        
        print("Smart Study Assistant Readings")

        if temperature is not None:
            print(f"Temperature: {temperature:.1f}°C")
        else:
            print("Temperature: No reading")

        if humidity is not None:
            print(f"Humidity: {humidity:.1f}%")
        else:
            print("Humidity: No reading")

        print(f"Motion: {motion_status}")
        print(f"Sound: {sound_status}")
        print(f"Light: {light_status}")

    except RuntimeError as error:
        print("DHT22 reading error:", error.args[0])

    except Exception as error:
        print("Unexpected error:", error)

    time.sleep(2)
