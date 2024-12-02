# Software Systems & Electronics Integration for the Javelin Jr. NJITRC Fall 2024 Launch

![Rocketry Logo](src/static/rocketryLogo.png)

## Overview
This project is designed to support data collection and transmission using a RYLR998 LoRa radio module in a rocket system. The system is integrated with a Flask web application that allows real-time data visualization and control via a web interface. The RYLR998 module is responsible for sending and receiving data, and the Flask web app manages communication with the module and provides a visual display of the transmitted data.

Key functionalities of the system include:
1. **Real-time Data Collection** - Collects and transmits sensor data via the RYLR998 LoRa module.
2. **Flask Web Interface** - Allows users to initiate data collection and visualize data through WebGL.
3. **Socket Communication** - Real-time communication between the Flask server and the front-end using Flask-SocketIO.

## Table of Contents
- [System Design](#system-design)
- [Features](#features)
- [Code Structure](#code-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## System Design
The system is composed of several components that interact to ensure efficient data collection, transmission, and visualization.

Key components include:
1. **Flask Web Application** - Handles routes for web pages and manages real-time communication with the front-end.
2. **RYLR998 LoRa Communication** - Handles data reception and transmission between the rocket and the ground control.
3. **SocketIO Communication** - Enables real-time data transfer between the server and the client.
4. **Password Authentication** - Ensures that data collection starts only when the correct password is provided.

The system uses a combination of Flask-SocketIO and the RYLR998 module to collect, transmit, and visualize data, while ensuring secure and authenticated operations.

## Features
- **Data Collection** - Collects sensor data from the LoRa module and sends it to the Flask server for visualization.
- **Real-time Communication** - Uses Flask-SocketIO for real-time updates to the client.
- **Password Authentication** - Ensures that data collection can only start with the correct password.
- **WebGL Visualization** - Displays the received data in real-time using WebGL on the front-end.
- **LoRa Data Transmission** - Encodes and sends quaternion data over the LoRa radio module.

## Code Structure

The project is structured into the following key files:

- **`app.py`**: The main Flask application that handles routes, authentication, and real-time communication.
- **`recieve.py`**: Contains the `RYLR998_Recieve` class for receiving and decoding data from the LoRa module.
- **`transmit.py`**: Contains the `RYLR998_Transmit` class for encoding and transmitting data to the LoRa module.
- **`requirements.txt`**: Lists the Python dependencies required for the project.
- **`index.html`**: The homepage of the web application for password authentication.
- **`visualize.html`**: Displays real-time visualizations of the transmitted data.
- **`.env`**: Contains environment variables, including the hashed password for authentication.

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

Once the system is installed and configured, run the Flask application:

```bash
python app.py


## Contributors

The following individuals have contributed to this project:

- [Contributor Matthew Tolocka](https://github.com/mt657) - Software Optimization Specialist
- [Contributor Matthew Tujague](https://github.com/Binimal101) - Lead Software Engineer/Avionics Lead
- [Contributor Amogh Karee](https://github.com/AmoghKaree) - Flask Web Developer
- [Contributor Nick C Volpe](https://github.com/ncvolpe) - Support Engineer

These are the current contributors to the project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
