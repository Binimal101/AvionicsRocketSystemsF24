import logging, subprocess, time, datetime
import logging_config  

milliseconds_per_segment = 100

def start_camera():
    logging_config.setup_logging()
    
    # Define the command as a list of arguments
    command = [
        "libcamera-vid",
        "-n",
        "-t", "0",
        "--flush", "1",
        "--segment", str(milliseconds_per_segment), "1",
        "-o", f"../flightLogs/{datetime.date.today().strftime('%m-%d-%Y')}/vidsegment_%05d.h264",
    ]

    # Run the command
    process = subprocess.Popen(command) #literal equivalent to execlp() in c

    logging.info(f"CAMERA Process started with PID: {process.pid} at {time.time()}")
