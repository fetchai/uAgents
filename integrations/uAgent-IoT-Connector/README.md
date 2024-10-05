# uAgent_IoT_Connector
Made by: [Aleen Dhar](https://www.linkedin.com/in/aleendhar/) 

The   uAgent IoT Connector bridges several powerful technologies to create a robust, real-time interaction framework between an ESP32 microcontroller, AWS EC2 instances, and Fetch.ai's DeltaV platform. The architecture is designed to facilitate data collection, processing, and control for sensors and GPS modules integrated into the ESP32. It uses MQTT, a lightweight messaging protocol, ensuring efficient, scalable, and low-latency communication for real-time applications.



## Architecture Design

![image](https://github.com/user-attachments/assets/b464731e-3f7e-4274-bcb5-03f260a5dab1)


## Key Components:
1. ESP32 Microcontroller: At the heart of this system, ESP32 is responsible for collecting sensor data from connected modules, including the MPU6050 (a motion-tracking device) and the Ublox Neo-6m GPS (for location tracking). The data is then transmitted via MQTT for further analysis or control operations.

2. AWS EC2 MQTT Broker: The communication backbone relies on an AWS EC2 instance running a Mosquitto MQTT Broker. This broker enables efficient and secure bidirectional communication between the ESP32 microcontroller and various clients, including a web-based frontend and the Fetch.ai platform. The broker facilitates the publish-subscribe model, allowing clients to either publish data or subscribe to relevant topics. [Setup Guide](https://aws.amazon.com/blogs/iot/how-to-bridge-mosquitto-mqtt-broker-to-aws-iot/)

3. Node.js Socket Server & Next.js Frontend: A Node.js Socket server enables real-time communication between a Next.js frontend and the ESP32 via MQTT. This server sends requests and receives data, providing a user-friendly interface for monitoring sensor outputs or controlling the ESP32. The frontend acts as a control dashboard, visualizing real-time data and enabling actions on the ESP32 device. [Checkout the Template here](https://github.com/AleenDhar/Ground_station)

4. Fetch.ai uAgent Integration: Fetch.ai’s uAgent communicates with the ESP32 system by subscribing to specific topic. I have created 2 agents one who can directly control(by publishing data to AWS EC2 mqtt broker) the ESP32 from DeltaV and one that is subscribed to the topic where ESP32 is publishing the Sensor data.

5. Sensor Modules:
   - MPU6050: A motion tracking device that captures accelerometer and gyroscope data, providing key metrics for movement or orientation-based applications.
   -  Ublox Neo-6m GPS: A GPS module that provides accurate location data, which is transmitted via the ESP32 for tracking purposes.

## Communication Flow:
1. Sensor Data Collection: The ESP32 collects real-time data from the MPU6050 motion sensor and the Ublox GPS module.

2. MQTT Publish/Subscribe:
  - The ESP32 publishes sensor data to topics on the MQTT broker hosted on AWS EC2.
  - Multiple clients, including the Next.js frontend, Node.js socket server, and Fetch.ai uAgent, subscribe to the ESP32’s data streams.
  - The MQTT broker ensures efficient routing of messages to all subscribed clients.

3. Frontend Communication: The Node.js Socket server handles communication between the MQTT broker and the Next.js frontend, ensuring real-time data visualization and control capabilities.

4. Fetch.ai uAgent: The uAgent listens for specific events or requests and interacts with the ESP32 accordingly, leveraging the Fetch.ai DeltaV platform for additional computational or decision-making tasks.


## Working on DeltaV





https://github.com/user-attachments/assets/ead8fd2b-f193-4985-aa89-e49f885ec9bd


## Applications:
1. Drone or Robotics Control: The system's integration of sensors (MPU6050) and GPS modules (Ublox Neo-6m) makes it ideal for drone navigation, real-time tracking, and motion analysis.
2. Remote Monitoring: With the Next.js dashboard and real-time data communication through AWS, users can remotely monitor and control their devices over the cloud.
3. Decentralized Data Management: By leveraging Fetch.ai's DeltaV and uAgent, the system supports decentralized, intelligent decision-making for automated processes.


## Conclusion:
This system architecture is a powerful example of how modern IoT solutions can integrate cloud platforms, microcontrollers, and decentralized agents to deliver scalable, efficient, and intelligent solutions. From sensor data collection to remote control via web and decentralized intelligence, this design is suitable for a variety of advanced applications including robotics, monitoring, and automation.


## Setup
1. In the main directory install all dependencies

    ```bash
    
    pip install uagents
    pip install paho-mqtt
    ```


