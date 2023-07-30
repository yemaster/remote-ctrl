from PIL import ImageGrab
from io import BytesIO
import time
from base64 import b64encode
from flask import Flask, request
from flask_socketio import SocketIO
from pywinauto import mouse, keyboard
from pywinauto.timings import Timings

maxFps = 10


app = Flask(__name__, static_url_path="")
socketio = SocketIO(app, async_mode="eventlet")

Timings.after_setcursorpos_wait = 0
Timings.after_clickinput_wait = 0

startTime = time.time()
count = 0


def screencap():
    global count, startTime
    while True:
        img = ImageGrab.grab()
        buffer = BytesIO()
        img.save(buffer, 'jpeg')
        # yield (b'--frame\r\n'
        #       b'Content-Type: image/jpeg\r\n\r\n' + buffer.getvalue() + b'\r\n\r\n')
        socketio.emit('screenStream', buffer.getvalue())
        if count > 20:
            count = 0
            startTime = time.time()
        count += 1
        #print("fps: ", count / (time.time() - startTime))
        socketio.sleep(max(count / maxFps - time.time() + startTime, 0.005))


screen = ImageGrab.grab()
width, height = screen.size

isPress = False
isPinch = False


@app.route('/')
def index():
    return app.send_static_file('index.html')


"""
@app.route('/shot')
def shot():
    return Response(screencap(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
"""


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


pinchX = 0
pinchY = 0


@socketio.on("panstart")
def panstart(data):
    """鼠标移动开始"""
    global pinchX, pinchY, isPress
    # print("PanStart")
    if data["p"] == "pen":
        isPress = True
        mouse.press(
            coords=(int(data["x"] * width), int(data["y"] * height)), button="left")
    mouse.move(
        coords=(int(data["x"] * width), int(data["y"] * height)))
    pinchX = int(data["x"] * width)
    pinchY = int(data["y"] * height)


@socketio.on("panmove")
def panmove(data):
    """鼠标移动中"""
    global isPress, pinchX, pinchY
    if isPinch or data["p"] == "touch":
        mouse.scroll(coords=(int(data["x"] * width), int(data["y"] * height)), wheel_dist=(
            int(data["y"] * height)-pinchY) // 120)
        pinchX = int(data["x"] * width)
        pinchY = int(data["y"] * height)
    else:
        mouse.move(
            coords=(int(data["x"] * width), int(data["y"] * height)))


@socketio.on("panend")
def panend():
    """鼠标移动中"""
    global isPress, isPinch
    if isPress:
        isPress = False
        mouse.release()
    else:
        isPinch = False


@socketio.on("press")
def press(data):
    global isPress
    # print("Press")
    isPress = True
    mouse.press(
        coords=(int(data["x"] * width), int(data["y"] * height)), button="left")


@socketio.on("pressup")
def press():
    global isPress
    isPress = False
    mouse.release()


@socketio.on("pinchstart")
def pinchStart(data):
    global pinchX, pinchY, isPinch
    pinchX = int(data["x"] * width)
    pinchY = int(data["y"] * height)
    isPinch = True


@socketio.on("pinchend")
def pinchMove(data):
    """双指滑动"""
    global isPinch
    isPinch = False


@socketio.on("keydown")
def keydown(data):
    keyboard.send_keys(data)


if __name__ == '__main__':
    print("Remote Ctrl is running on :23333")
    socketio.start_background_task(screencap)
    socketio.run(app, port=23333, host='0.0.0.0')
