import logging, subprocess, time
import logging_config  


def start_camera():
    logging_config.setup_logging()
    
    # Define the command as a list of arguments
    command = [
        "libcamera-vid",
        "-o", "videoFeed.h264",
        "-n",
        "--flush", "1",
        "-t", "0",
    ]

    # Run the command
    process = subprocess.Popen(command) #literal equivalent to execlp() in c

    logging.info(f"CAMERA Process started with PID: {process.pid} at {time.time()}")
