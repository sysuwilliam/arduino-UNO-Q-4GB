import time

from arduino.app_bricks.web_ui import WebUI
from arduino.app_utils import App


# Camera access is handled by python/debian_opencv_server.py on the host Debian
# system. This App Lab process only serves the WebUI page on port 7000.
ui = WebUI()


def loop():
    time.sleep(10)


print("OpenCV detection WebUI started. Run python/debian_opencv_server.py on Debian for the camera stream.")
App.run(user_loop=loop)
