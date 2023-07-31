from PIL import ImageGrab
import mss
import cv2
import time
import json
import numpy as np
from os import path, _exit
import webbrowser
from flask import Flask, request, render_template
from flask_socketio import SocketIO
from pywinauto import mouse, keyboard
from pywinauto.timings import Timings

# 获取设置
defaultConfig = {
    "maxFps": 10,
    "scrollFlexibility": 120,
    "port": 23333,
    "imgWidth": 1366
}

config = defaultConfig
if path.exists("./config.json"):
    tempConfig = {}
    try:
        with open("./config.json", "r", encoding="utf-8") as f:
            tempConfig = json.load(f)
    except Exception:
        pass
    for i in defaultConfig:
        if (not i in tempConfig) or (type(tempConfig[i]) != type(defaultConfig[i])):
            tempConfig[i] = defaultConfig[i]
    config = tempConfig


app = Flask(__name__, static_url_path="")
socketio = SocketIO(app, async_mode="eventlet")

Timings.after_setcursorpos_wait = 0
Timings.after_clickinput_wait = 0

startTime = time.time()
count = 0

screen = ImageGrab.grab()
width, height = screen.size


screenCapture = mss.mss()


def screencap():
    global count, startTime
    while True:
        #img = ImageGrab.grab()
        img = screenCapture.grab({
            "left": 0,
            "top": 0,
            "width": width,
            "height": height
        })
        img = np.array(img)
        imgWidth = config["imgWidth"]
        imgHeight = int(height * imgWidth / width)
        img = cv2.resize(img, (imgWidth, imgHeight))
        img = cv2.imencode(".jpg", img)[1].tobytes()
        # yield (b'--frame\r\n'
        #       b'Content-Type: image/jpeg\r\n\r\n' + buffer.getvalue() + b'\r\n\r\n')
        socketio.emit('screenStream', img)
        if count > 20:
            count = 0
            startTime = time.time()
        count += 1
        # print("fps: ", count / (time.time() - startTime))
        socketio.sleep(
            max(count / config["maxFps"] - time.time() + startTime, 0.005))


isPress = False
isPinch = False


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/settings', methods=["POST", "GET"])
def settings():
    if request.method == "GET":
        return render_template("control.html", settings=config, suc=-1)
    else:
        newFps = int(request.form.get('maxFps'))
        newScrollFlexibility = int(request.form.get('scrollFlexibility'))
        newImgWidth = int(request.form.get('imgWidth'))
        if type(newFps) == type(config["maxFps"]):
            config["maxFps"] = newFps
        if type(newScrollFlexibility) == type(config["scrollFlexibility"]):
            config["scrollFlexibility"] = newScrollFlexibility
        if type(newImgWidth) == type(config["imgWidth"]):
            config["imgWidth"] = newImgWidth
        isSuccess = 1
        try:
            with open("config.json", "w") as f:
                json.dump(config, f)
        except Exception:
            isSuccess = 0
            print("[ERROR] Cannot save settings")
        return render_template("control.html", settings=config, suc=isSuccess)


@app.route('/shutdown', methods=["POST"])
def shutdown():
    if request.form.get("shutdown") == "orz":
        _exit(0)


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
    # print("Tap", int(data["x"] * width), int(data["y"] * height))
    mouse.click(
        coords=(int(data["x"] * width), int(data["y"] * height)))


@socketio.on("righttap")
def tap(data):
    """鼠标点击"""
    # print("Tap", int(data["x"] * width), int(data["y"] * height))
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


sumDeltaY = 0


@socketio.on("panmove")
def panmove(data):
    """鼠标移动中"""
    global sumDeltaY, pinchX, pinchY
    #print(data["x"] * width, data["y"] * height)
    if (not isPress) and data["p"] == "touch":
        sumDeltaY += int(data["y"] * height) - pinchY
        if sumDeltaY > config["scrollFlexibility"]:
            mouse.scroll(
                coords=(int(data["x"] * width), int(data["y"] * height)), wheel_dist=1)
            sumDeltaY -= config["scrollFlexibility"]
        if sumDeltaY < -config["scrollFlexibility"]:
            mouse.scroll(
                coords=(int(data["x"] * width), int(data["y"] * height)), wheel_dist=-1)
            sumDeltaY += config["scrollFlexibility"]
        pinchX = int(data["x"] * width)
        pinchY = int(data["y"] * height)
    else:
        mouse.move(
            coords=(int(data["x"] * width), int(data["y"] * height)))


@socketio.on("panend")
def panend(data):
    global isPress, isPinch
    if isPress:
        isPress = False
        mouse.release(button="left", coords=(
            int(data["x"] * width), int(data["y"] * height)))
    if isPinch:
        isPinch = False


@socketio.on("press")
def press(data):
    global isPress
    # print("Press")
    isPress = True
    mouse.press(
        coords=(int(data["x"] * width), int(data["y"] * height)), button="left")


@socketio.on("pressup")
def press(data):
    global isPress
    isPress = False
    mouse.release(button="left", coords=(
        int(data["x"] * width), int(data["y"] * height)))


@socketio.on("pinchstart")
def pinchStart(data):
    global pinchX, pinchY, isPinch
    pinchX = int(data["x"] * width)
    pinchY = int(data["y"] * height)
    isPinch = True


@socketio.on("pinchend")
def pinchMove():
    """双指滑动"""
    global isPinch
    isPinch = False


@socketio.on("keydown")
def keydown(data):
    keyboard.send_keys(data)


if __name__ == '__main__':
    print("Votrl Remote Ctrl is running on :23333")
    socketio.start_background_task(screencap)
    webbrowser.open("http://localhost:" + str(config["port"]) + "/settings")
    socketio.run(app, port=config["port"], host='0.0.0.0')
