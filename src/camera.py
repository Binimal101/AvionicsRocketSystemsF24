import logging, subprocess, time, datetime, os
import logging_config  

milliseconds_per_segment = 100

def start_camera(dir_path: str):
    logging_config.setup_logging()

    cleanScriptName = "processVideo.sh"    
    with open(f"{dir_path}/{cleanScriptName}", "w") as f:
        f.write('''#!/usr/bin/env bash
        #
        # merge_h264_segments.sh
        # ---------------------------------------------------------
        # 1. Collects all .h264 segments that match vidsegment_*.h264.
        # 2. Generates a "concat list" for FFmpeg.
        # 3. Merges them into rocketVision.mp4 (no re-encode, just copy).
        # 4. Moves original segments into a "segments/" subdir.
        # ---------------------------------------------------------

        # Name of the final merged MP4 file
        FINAL_OUTPUT="rocketVision.mp4"

        # Temporary file to hold list of segments
        LIST_FILE="segments_list.txt"

        # ---------------------------------------------------------
        # 1. Generate the concat list for ffmpeg
        # ---------------------------------------------------------
        # We only want files matching our known pattern.
        echo "Building file list..."
        ls vidsegment_*.h264 2>/dev/null | sort | sed "s|\(.*\)|file '\1'|" > "$LIST_FILE"

        # If there are no matching files, bail out
        if [ ! -s "$LIST_FILE" ]; then
        echo "No .h264 segment files found matching 'vidsegment_*.h264'. Exiting."
        rm -f "$LIST_FILE"
        exit 1
        fi

        # ---------------------------------------------------------
        # 2. Merge using ffmpeg concat
        #    - '-f concat': Tells ffmpeg we're feeding it a list of files to merge
        #    - '-safe 0':  Required if your paths or filenames contain special characters
        #    - '-c copy':  We do not re-encode, just copy video streams
        # ---------------------------------------------------------
        echo "Merging segments into $FINAL_OUTPUT..."
        ffmpeg -y -f concat -safe 0 -i "$LIST_FILE" -c copy "$FINAL_OUTPUT"

        # ---------------------------------------------------------
        # 3. Create 'segments' directory and move .h264 files there
        # ---------------------------------------------------------
        SEGMENTS_DIR="segments"
        if [ ! -d "$SEGMENTS_DIR" ]; then
        echo "Creating directory '$SEGMENTS_DIR'..."
        mkdir "$SEGMENTS_DIR"
        fi

        echo "Moving .h264 files to '$SEGMENTS_DIR'..."
        mv vidsegment_*.h264 "$SEGMENTS_DIR"/

        # ---------------------------------------------------------
        # 4. Cleanup
        # ---------------------------------------------------------
        echo "Removing temporary list file $LIST_FILE..."
        rm -f "$LIST_FILE"

        echo "Done!"
        echo "Final video: $FINAL_OUTPUT"
        echo "Segments archived in: $SEGMENTS_DIR/"
        ''')

        os.system(f"chmod 755 {dir_path}/{cleanScriptName}")

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
