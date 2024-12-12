import logging, subprocess, time, datetime, os
import logging_config  

milliseconds_per_segment = 100

def start_camera(dir_path: str):
    logging_config.setup_logging()
    
    # Define the command as a list of arguments
    command = [
        "libcamera-vid",
        "-n",
        "-t", "0",
        "--flush", "1",
        "--segment", str(milliseconds_per_segment), "1",
        "-o", f"{dir_path}/vidsegment_%05d.h264",
    ]

    # Run the command
    cameraProcess = subprocess.Popen(command) #literal equivalent to execlp() in c
    syncProcess = subprocess.Popen(["./syncify.sh"])

    logging.info(f"CAMERA Process started with PID: {cameraProcess.pid} at {time.time()}\n")
    logging.info(f"SYNCIFY Process started with PID: {syncProcess.pid} at {time.time()}\n")
