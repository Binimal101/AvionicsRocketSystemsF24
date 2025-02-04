# Software Systems & Electronics Integration for the Javelin Jr. NJITRC Fall 2024 Launch

<img src="src/static/images/rocketryLogo.png" alt="Rocketry Logo" width="300" height="auto">

## Overview
This project is designed to support data collection and transmission using a RYLR998 LoRa radio module in a rocket system. The system is integrated with a Flask web application that allows real-time data visualization and control via a web interface. The RYLR998 module is responsible for sending and receiving data, and the Flask web app manages communication with the module and provides a visual display of the transmitted data.


## Table of Contents
- [System Design](#system-design)
- [Features](#features)
- [Code Structure](#code-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Contributors](#Contributors)
- [License](#license)

## Features
- **Data Collection** - Collects sensor data from the LoRa module and sends it to the Flask server for visualization.
- **Flask Web Interface** - Allows users to initiate data collection and visualize data through WebGL.
- **Socket Communication** - Real-time communication between the Flask server and the front-end using Flask-SocketIO.
- **Password Authentication** - Ensures that data collection can only start with the correct password.
- **WebGL Visualization** - Displays the received data in real-time using WebGL on the front-end.
- **LoRa Data Transmission** - Encodes and sends quaternion data over the LoRa radio module.
- **Quaternion Based Interpolation** - Responsible for silky smooth rotational animations, massively improves framerate
- **Livetime Visualization** - Utilizes WebGL to visualize 

## Code Structure

The project is structured into the following key files:

- **[`altimeter.py`](src/altimeter.py)**: Manages altitude measurement and data processing for the LoRa module.
- **[`camera.py`](src/camera.py)**: Handles video capture and logging from a Raspberry Pi camera module, supporting non-blocking video recording.
- **[`recieve.py`](src/recieve.py)**: Receives and decodes data from the LoRa module.
- **[`quaternion.html`](src/quaternion.py)**: Abstracts quaternion mathematics for zeroing upon calibration
- **[`metrics.py`](src/metrics.py)**: Provides functions for processing telemetry data, including time delta and quaternion encoding/decoding.
- **[`requirements.txt`](requirements.txt)**: Lists the Python dependencies required for the project.
- **[`transmit.py`](src/transmit.py)**: Encodes and transmits data to the LoRa module.
- **[`index.html`](src/templates/index.html)**: The homepage of the web application for password authentication.
- **[`visualize.html`](src/templates/visualize.html)**: Displays real-time visualizations of the transmitted data.
- **[`.env`](.env)**: Contains environment variables, including the hashed password for authentication.
- **[`RPI02W.py`](src/RPI02W.py)**: Manages interaction with the Raspberry Pi 2W for telemetry and sensor data collection.
- **[`RP15.py`](src/RP15.py)**: Runs the Flask server and handles socket communication for password validation and real-time data emission.

## Installation

1. Clone this repository to your local machine:
    ```bash
    git clone https://github.com/your-repo/javelin-jr.git
    ```

2. Install the necessary Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up the environment variables by creating a `.env` file in the root directory:
    ```bash
    hashedPassword=<your_hashed_password>
    ```

4. Ensure the RYLR998 LoRa module is connected and properly configured.

## Usage

After installation and configuration, start collecting and logging flight data with the following command:

```bash
python RP102W.py
```

Once the system is installed and configured, start the Flask application by running the following command:

```bash
python RP15.py
```

## Contributors

The following individuals have contributed to this project's software:

- [Matthew Tujague](https://github.com/Binimal101) - Lead Software Engineer/Avionics Manager
- [Victor Jimenez](https://github.com/VictorJimenez3) - Quaternion-based Interpolation Tech.
- [Eric Zhang](https://github.com/ezhang04) - Visualization Specialist
- [Ryan Ramos](https://github.com/ryanrnjit) - Visualization Specialist
- [Amogh Karee](https://github.com/AmoghKaree) - Flask Web Developer
- [Matthew Tolocka](https://github.com/mt657) - Software Optimization Specialist
- [Nick C Volpe](https://github.com/ncvolpe) - Support Engineer

These are the current contributors to the project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
