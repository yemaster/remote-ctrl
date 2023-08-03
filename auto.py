from win32 import win32api, win32gui, win32print
from win32.lib import win32con
import mss


# 获取屏幕真实大小
def get_real_screen_resolution():
    hDC = win32gui.GetDC(0)
    width = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
    height = win32print.GetDeviceCaps(hDC, win32con.DESKTOPVERTRES)
    return (width, height)


# 获取屏幕缩放后大小
def get_screen_size():
    width = win32api.GetSystemMetrics(0)
    height = win32api.GetSystemMetrics(1)
    return (width, height)


rw, rh = get_real_screen_resolution()
nw, nh = get_screen_size()
#print(rw, rh, nw, nh)


# 截图
screenCapture = mss.mss()


def screengrab():
    return screenCapture.grab({
        "left": 0,
        "top": 0,
        "width": rw,
        "height": rh
    })


# 鼠标移动
def mouse_move(x, y):
    win32api.SetCursorPos((x, y))

# 鼠标单击


def mouse_click(x, y, button="left", n=1):
    win32api.SetCursorPos((x, y))
    for i in range(n):
        if button == "left":
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        elif button == "right":
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


# 鼠标按下
def mouse_press(x, y, button="left"):
    win32api.SetCursorPos((x, y))
    if button == "left":
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    elif button == "right":
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)


# 鼠标松开
def mouse_release(x, y, button="left"):
    win32api.SetCursorPos((x, y))
    if button == "left":
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif button == "right":
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


# 鼠标滚动
def mouse_scroll(h, v):
    if v is not None:
        v = int(v)
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, v, 0)
    if h is not None:
        h = int(h)
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, h, 0)


# 键盘按键
keyNumber = {
    "BACKSPACE": 8,
    "TAB": 9,
    "ENTER": 13,
    "SHIFT": 16,
    "CTRL": 17,
    "ALT": 18,
    "CAPE": 20,
    "ESC": 27,
    "SPACEBAR": 32,
    "PAGEUP": 33,
    "PAGEDOWN": 34,
    "END": 35,
    "HOME": 36,
    "LEFTARROW": 37,
    "UPARROW": 38,
    "RIGHTARROW": 39,
    "DOWNARROW": 40,
    "INSERT": 45,
    "DELETE": 46,
    "WIN": 91,
    "NUMLOCK": 144,
    ";": 186,
    "=": 187,
    "-": 189,
    ".": 190,
    "/": 191,
    "`": 192,
    "[": 219,
    "/": 220,
    "]": 221,
    "F1": 112,
    "F2": 113,
    "F3": 114,
    "F4": 115,
    "F5": 116,
    "F6": 117,
    "F7": 118,
    "F8": 119,
    "F9": 120,
    "F10": 121,
    "F11": 122,
    "F12": 123,
}


def translate_key(key) -> int:
    val = -1
    if type(key) == int:
        val = key
    elif type(key) == str:
        key = key.upper()
        print(key, key in keyNumber)
        if len(key) == 1 and ("A" <= key <= "Z" or "0" <= key <= "9"):
            val = ord(key)
        elif key in keyNumber:
            val = keyNumber[key]
    if val == -1:
        return None
    else:
        return val


def press_key(key):
    val = translate_key(key)
    #print(val)
    if val is not None:
        win32api.keybd_event(val, 0, 0, 0)


def release_key(key):
    val = translate_key(key)
    #print(val)
    if val is not None:
        win32api.keybd_event(val, 0, win32con.KEYEVENTF_KEYUP, 0)


def tap_key(key, n=1):
    for _ in range(n):
        press_key(key)
        release_key(key)


def press_keys(keys):
    for _ in keys:
        press_key(_)
    for _ in keys:
        release_key(_)
