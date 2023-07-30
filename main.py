from PIL import ImageGrab
from io import BytesIO
import time
import json
from os import path
import webbrowser
from flask import Flask, request, render_template
from flask_socketio import SocketIO
from pywinauto import mouse, keyboard
from pywinauto.timings import Timings

# 获取设置
defaultConfig = {
    "maxFps": 10,
    "scrollFlexibility": 200,
    "port": 23333,
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
        socketio.sleep(max(count / config["maxFps"] - time.time() + startTime, 0.005))


screen = ImageGrab.grab()
width, height = screen.size

isPress = False
isPinch = False


@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/settings', methods=["POST", "GET"])
def settings():
    if request.method == "GET":
        return render_template("control.html", settings=config, suc=0)
    else:
        newFps = int(request.form.get('maxFps'))
        newScrollFlexibility = int(request.form.get('scrollFlexibility'))
        if type(newFps) == type(config["maxFps"]):
            config["maxFps"] = newFps
        if type(newScrollFlexibility) == type(config["scrollFlexibility"]):
            config["scrollFlexibility"] = newScrollFlexibility
        isSuccess = 1
        try:
            with open("config.json", "w") as f:
                json.dump(config, f)
        except Exception:
            isSuccess = 0
            print("[ERROR] Cannot save settings")
        return render_template("control.html", settings=config, suc=isSuccess)

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
    if (not isPress) and data["p"] == "touch":
        mouse.scroll(coords=(int(
            data["x"] * width), int(data["y"] * height)), wheel_dist=int(data["deltaY"] * height / config["scrollFlexibility"]))
    else:
        mouse.move(
            coords=(int(data["x"] * width), int(data["y"] * height)))


@socketio.on("panend")
def panend():
    global isPress, isPinch
    if isPress:
        isPress = False
        mouse.release()
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
