from picamera2 import Picamera2
import os, threading, time, datetime

class Camera:
    def __init__(self):
        """Initialize the video logger and configure the camera."""
        self.picam2 = Picamera2()
        self.video_config = self.picam2.create_video_configuration()
        self.picam2.configure(self.video_config)
        self.recording = False  # Flag to indicate if recording is active
        self.file_path = None
        self.thread = None

    def _ensure_directory(self, directory):
        """Ensure the specified directory exists."""
        if not os.path.exists(directory):
            os.makedirs(directory)

    def _log_video(self):
        """Internal method to log video to the specified file indefinitely."""
        with open(self.file_path, "ab") as file:  # Append mode
            print(f"Recording started. Writing to {self.file_path}")
            while self.recording:
                # Capture a frame
                frame = self.picam2.capture_array()
                # Write raw frame bytes to file
                file.write(frame.tobytes())
                time.sleep(0.03)  # Approximate frame delay

        print("Recording stopped.")

    def START(self, directory, filename):
        """
        Starts logging video to the specified directory and file.
        """
        if self.recording:
            print("Recording is already active.")
            return

        # Ensure directory exists
        self._ensure_directory(directory)

        # Set file path
        self.file_path = os.path.join(directory, filename)

        # Start the camera
        self.picam2.start()

        # Start recording in a separate thread
        self.recording = True
        self.thread = threading.Thread(target=self._log_video)
        self.thread.start()

    def STOP(self):
        if not self.recording:
            print("No recording is active.")
            return

        # Stop recording
        self.recording = False

        # Wait for the logging thread to finish
        self.thread.join()
        self.thread = None

        # Stop the camera
        self.picam2.stop()


# Example Usage
if __name__ == "__main__":
    cam = Camera()

    try:
        # Start logging to a file in the "videos" directory
        cam.START(directory=f"../flightLogs/{datetime.date.today().strftime('%m-%d-%Y')}", filename="recording.raw")
        print("Press Ctrl+C to stop recording.")
        while True:
            time.sleep(1)  # Keep the main thread alive
    except KeyboardInterrupt:
        print("Stopping recording...")
        cam.STOP()
