# import libraries
from vidgear.gears import WriteGear, CamGear

import cv2

# output_params = {"-s": "2048x2048", "-r": 30}  # define FFmpeg tweak parameters for writer
options = {"STREAM_RESOLUTION": "720p", "STREAM_PARAMS": {"nocheckcertificate": True}}
stream = cv2.VideoCapture(
    'https://cdn.wolfstream.app/stream/bYAmNbegnx86/manifest.m3u8?token=R6LFDiNwsSArOynyh7Avog&expires=1664360113'
) # Open live webcam video stream on first index(i.e. 0) device
output_params = {"-f": "rtsp", "-rtsp_transport":"tcp"}
writer = WriteGear(output_filename='rtsp://localhost:8554/stream', compression_mode=True, logging=True,
                   **output_params)  # Define writer with output filename 'Output.mp4'

# infinite loop
while True:

    (grabbed, frame) = stream.read()
    # read frames

    # check if frame empty
    if not grabbed:
        # if True break the infinite loop
        break

    writer.write(frame)

    # Show output window
    cv2.imshow("Output Frame", frame)

    key = cv2.waitKey(1) & 0xFF
    # check for 'q' key-press
    if key == ord("q"):
        # if 'q' key-pressed break out
        break

cv2.destroyAllWindows()
# close output window

stream.release()
# safely close video stream
writer.close()
# safely close writer
