from vidgear.gears import WriteGear, CamGear
import cv2

a, cap = cv2.VideoCapture('http://72.49.230.145:8080/?action=stream')
output_params = {"-f": "rtsp", "-rtsp_transport": "tcp"}
writer = WriteGear(output_filename='rtsp://localhost:8554/test', logging=True,
                   **output_params)

while True:
    frame = cap.read()
    writer.write(frame)
