# uAgent_IoT_Connector
Made by: [Aleen Dhar](https://www.linkedin.com/in/aleendhar/) 

The   uAgent IoT Connector bridges several powerful technologies to create a robust, real-time interaction framework between an ESP32 microcontroller, AWS EC2 instances, and Fetch.ai's DeltaV platform. The architecture is designed to facilitate data collection, processing, and control for sensors and GPS modules integrated into the ESP32. It uses MQTT, a lightweight messaging protocol, ensuring efficient, scalable, and low-latency communication for real-time applications.



## Architecture Design

![chrome_8gCeOCHszO](https://github.com/user-attachments/assets/1eb6e0e7-7201-46c7-87ec-f6478c3554e5)

## Key Components:
1. ESP32 Microcontroller: At the heart of this system, ESP32 is responsible for collecting sensor data from connected modules, including the MPU6050 (a motion-tracking device) and the Ublox Neo-6m GPS (for location tracking). The data is then transmitted via MQTT for further analysis or control operations.

2. AWS EC2 MQTT Broker: The communication backbone relies on an AWS EC2 instance running a Mosquitto MQTT Broker. This broker enables efficient and secure bidirectional communication between the ESP32 microcontroller and various clients, including a web-based frontend and the Fetch.ai platform. The broker facilitates the publish-subscribe model, allowing clients to either publish data or subscribe to relevant topics. [Setup Guide](https://aws.amazon.com/blogs/iot/how-to-bridge-mosquitto-mqtt-broker-to-aws-iot/)

3. Node.js Socket Server & Next.js Frontend: A Node.js Socket server enables real-time communication between a Next.js frontend and the ESP32 via MQTT. This server sends requests and receives data, providing a user-friendly interface for monitoring sensor outputs or controlling the ESP32. The frontend acts as a control dashboard, visualizing real-time data and enabling actions on the ESP32 device. [Checkout the Template here](https://github.com/AleenDhar/Ground_station)

4. Fetch.ai uAgent Integration: Fetch.ai’s uAgent communicates with the ESP32 system by subscribing to specific topic. I have created 2 agents one who can directly control(by publishing data to AWS EC2 mqtt broker) the ESP32 from DeltaV and one that is subscribed to the topic where ESP32 is publishing the Sensor data.

5. Sensor Modules:
   - MPU6050: A motion tracking device that captures accelerometer and gyroscope data, providing key metrics for movement or orientation-based applications.
   -  Ublox Neo-6m GPS: A GPS module that provides accurate location data, which is transmitted via the ESP32 for tracking purposes.




## Working on DeltaV
![chrome_8i7w3JbuAG](https://github.com/AleenDhar/Youtube-shorts-creation/assets/86429480/8a300920-08f0-4a8c-a5ac-5496a42d17a6)



## Setup
1. In the main directory install all dependencies

    ```bash
    python -m poetry install
    ```


## Running The Main Script

To run the project, use the command:

    ```
    cd src
    pyhton -m poetry run python main.py
    ```
