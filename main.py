from PIL import ImageGrab
import cv2
import numpy as np
from threading import Thread
from base64 import b64encode
from flask import Flask, request
from flask_socketio import SocketIO
from pywinauto import mouse, keyboard
from pywinauto.timings import Timings


app = Flask(__name__, static_url_path="")
socketio = SocketIO(app, async_mode="eventlet")

Timings.after_setcursorpos_wait = 0
Timings.after_clickinput_wait = 0


def screenshot():
    """获取屏幕截图，以base64输出"""
    shot = np.array(ImageGrab.grab())
    shot = cv2.cvtColor(shot, cv2.COLOR_RGB2BGR)
    encode_image = cv2.imencode('.jpg', shot)[1].tobytes()
    return b64encode(encode_image).decode("ascii")


nowScreenShot = ""


def getScreenShot():
    global nowScreenShot
    while True:
        nowScreenShot = screenshot()


screen = ImageGrab.grab()
width, height = screen.size

isPress = False


@app.before_first_request
def doScreenShot():
    Thread(target=getScreenShot, daemon=True).start()


@app.route('/')
def index():
    return app.send_static_file('index.html')


@socketio.on('connect')
def on_connect():
    print("Connected:", request.sid)
    socketio.emit("screenInfo", {"width": width, "height": height})


@socketio.on("tap")
def tap(data):
    """鼠标点击"""
    #print("Tap", int(data["x"] * width), int(data["y"] * height))
    mouse.click(
        coords=(int(data["x"] * width), int(data["y"] * height)))


@socketio.on("righttap")
def tap(data):
    """鼠标点击"""
    #print("Tap", int(data["x"] * width), int(data["y"] * height))
    mouse.right_click(
        coords=(int(data["x"] * width), int(data["y"] * height)))


panX = 0
panY = 0


@socketio.on("panstart")
def panstart(data):
    """鼠标移动开始"""
    global panX, panY
    print("PanStart")
    mouse.move(
        coords=(int(data["x"] * width), int(data["y"] * height)))
    panX = int(data["x"] * width)
    panY = int(data["y"] * height)


@socketio.on("panmove")
def panmove(data):
    """鼠标移动中"""
    global isPress, panX, panY
    mouse.move(
        coords=(int(data["x"] * width), int(data["y"] * height)))
    panX = int(data["x"] * width)
    panY = int(data["y"] * height)


@socketio.on("panend")
def panend():
    """鼠标移动中"""
    global isPress
    if isPress:
        isPress = False
        mouse.release()


@socketio.on("press")
def press(data):
    global isPress
    print("Press")
    isPress = True
    mouse.press(
        coords=(int(data["x"] * width), int(data["y"] * height)), button="left")


@socketio.on("pressup")
def press():
    global isPress
    isPress = False
    mouse.release()


pinchX = 0
pinchY = 0


@socketio.on("pinchstart")
def pinchStart(data):
    global pinchX, pinchY
    pinchX = int(data["x"] * width)
    pinchY = int(data["y"] * height)


@socketio.on("pinchmove")
def pinchMove(data):
    global pinchX, pinchY
    mouse.scroll(coords=(int(data["x"] * width), int(data["y"]
                                                     * height)), wheel_dist=(int(data["y"] * height)-pinchY) // 100)
    pinchX = int(data["x"] * width)
    pinchY = int(data["y"] * height)

@socketio.on("keydown")
def keydown(data):
    keyboard.send_keys(data)


@socketio.on("getShot")
def updateScreen():
    # print("getShot")
    socketio.emit("screenShow", nowScreenShot, room=request.sid)


if __name__ == '__main__':
    print("Mobile Touchpad is running on :23333")
    socketio.run(app, port=23333, host='0.0.0.0')
