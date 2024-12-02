# pylint: disable=W0621, disable=E1101
"""
This module provides a Camera class for managing video capture and logging from
a Raspberry Pi camera module. It supports starting and stopping video recording
to a specified file in a given directory. The recording is handled in a separate
thread to avoid blocking the main program.
"""
import os
import threading
import time
import datetime
import logging
from picamera2 import Picamera2
import logging_config  # Import the logging configuration

# Call the setup function to configure logging
logging_config.setup_logging()

class Camera:
    """
    Camera class to capture and log video using a Raspberry Pi camera.

    Provides methods to start and stop video recording. The video is captured
    in raw frame format and logged to a file in the specified directory. Recording
    is done in a separate thread to ensure non-blocking execution.

    Methods:
        start(directory, filename): Starts video recording to the specified file.
        stop(): Stops the active video recording.
    """

    def __init__(self):
        """Initialize the video logger and configure the camera."""
        self.picam2 = Picamera2()
        self.video_config = self.picam2.create_video_configuration()
        self.picam2.configure(self.video_config)
        self.recording = False  # Flag to indicate if recording is active
        self.file_path = None
        self.thread = None
        logging.info("Camera initialized.")

    def _ensure_directory(self, directory):
        """Ensure the specified directory exists."""
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info("Directory created: %s", directory)
        else:
            logging.info("Directory already exists: %s", directory)

    def _log_video(self):
        """Internal method to log video to the specified file indefinitely."""
        with open(self.file_path, "ab") as file:  # Append mode
            logging.info("Recording started. Writing to %s", self.file_path)
            print(f"Recording started. Writing to {self.file_path}")
            while self.recording:
                # Capture a frame
                frame = self.picam2.capture_array()
                # Write raw frame bytes to file
                file.write(frame.tobytes())
                time.sleep(0.03)  # Approximate frame delay

        logging.info("Recording stopped.")
        print("Recording stopped.")

    def start(self, directory, filename):
        """
        Starts logging video to the specified directory and file.

        Args:
            directory (str): The directory where the video will be saved.
            filename (str): The name of the file to save the video as.
        """
        if self.recording:
            logging.warning("Recording is already active.")
            print("Recording is already active.")
            return

        # Ensure directory exists
        self._ensure_directory(directory)

        # Set file path
        self.file_path = os.path.join(directory, filename)

        # Start the camera
        self.picam2.start()
        logging.info("Camera started. Recording to %s", self.file_path)
        print(f"Camera started. Recording to {self.file_path}")

        # Start recording in a separate thread
        self.recording = True
        self.thread = threading.Thread(target=self._log_video)
        self.thread.start()

    def stop(self):
        """
        Stops the active video recording.

        If no recording is active, it will print a message and log the event.
        """
        if not self.recording:
            logging.warning("No recording is active.")
            print("No recording is active.")
            return

        # Stop recording
        self.recording = False

        # Wait for the logging thread to finish
        self.thread.join()
        self.thread = None

        # Stop the camera
        self.picam2.stop()
        logging.info("Camera stopped. Recording finished.")
        print("Camera stopped. Recording finished.")

# Example Usage
if __name__ == "__main__":
    cam = Camera()

    try:
        # Start logging to a file in the "videos" directory
        DIRECTORY = f"../flightLogs/{datetime.date.today().strftime('%m-%d-%Y')}"
        FILENAME = "recording.raw"
        cam.start(DIRECTORY, FILENAME)
        print("Press Ctrl+C to stop recording.")
        logging.info("Recording is in progress.")
        while True:
            time.sleep(1)  # Keep the main thread alive
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received. Stopping recording...")
        print("Stopping recording...")
        cam.stop()
