import ctypes
import time
from ctypes.wintypes import DWORD, WORD, SHORT, WCHAR, UINT, HANDLE

# 定义常量
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101


# 定义结构体
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', WORD),
        ('wScan', WORD),
        ('dwFlags', DWORD),
        ('time', DWORD),
        ('dwExtraInfo', ctypes.POINTER(DWORD)),
    ]



class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ('uMsg', DWORD),
        ('wParamL', WORD),
        ('wParamH', WORD),
    ]



# 定义函数原型
GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
AttachThreadInput = ctypes.windll.user32.AttachThreadInput
SendMessage = ctypes.windll.user32.SendMessageW
FindWindow = ctypes.windll.user32.FindWindowW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible
FindWindowEx = ctypes.windll.user32.FindWindowExW

# 键盘映射
VK_CODE = {
    'a': 0x41,
    'b': 0x42,
    'c': 0x43,
    'd': 0x44,
    'e': 0x45,
    'f': 0x46,
    'g': 0x47,
    'h': 0x48,
    'i': 0x49,
    'j': 0x4A,
    'k': 0x4B,
    'l': 0x4C,
    'm': 0x4D,
    'n': 0x4E,
    'o': 0x4F,
    'p': 0x50,
    'q': 0x51,
    'r': 0x52,
    's': 0x53,
    't': 0x54,
    'u': 0x55,
    'v': 0x56,
    'w': 0x57,
    'x': 0x58,
    'y': 0x59,
    'z': 0x5A,
    '1': 0x31,
    '2': 0x32,
    '3': 0x33,
    '4': 0x34,
    '5': 0x35,
    '6': 0x36,
    '7': 0x37,
    '8': 0x38,
    '9': 0x39,
    '0': 0x30,
    'return': 0x0D,
    'escape': 0x1B,
    'backspace': 0x08,
    'tab': 0x09,
    'spacebar': 0x20,
    'left': 0x25,
    'up': 0x26,
    'right': 0x27,
    'down': 0x28,
    'shift': 0x10,
    'ctrl': 0x11,
    'alt': 0x12,
    'win': 0x5B,
}


def send_key(hwnd, key):
    vk_code = VK_CODE[key]

    # 发送 WM_KEYDOWN 事件
    SendMessage(hwnd, WM_KEYDOWN, vk_code, 0)

    # 发送 WM_KEYUP 事件
    SendMessage(hwnd, WM_KEYUP, vk_code, 0)


def send_text(hwnd, text):
    for char in text:
        send_key(hwnd, char)


def find_window(class_name, window_name):
    hwnd = FindWindow(class_name, window_name)
    if hwnd and IsWindowVisible(hwnd):
        return hwnd
    return None


def attach_to_window_thread(hwnd):
    current_id = ctypes.windll.kernel32.GetCurrentThreadId()
    target_id = DWORD()
    GetWindowThreadProcessId(hwnd, ctypes.byref(target_id))
    AttachThreadInput(current_id, target_id.value, True)
    return current_id, target_id.value


def detach_from_window_thread(current_id, target_id):
    AttachThreadInput(current_id, target_id, False)


def main():
    # 查找目标窗口
    hwnd = find_window(None, "绝区零")  # 替换为你的窗口名称
    if not hwnd:
        print("Window not found.")
        return
    hwnd = ctypes.windll.user32.GetForegroundWindow()

    # 获取窗口线程 ID 并附加到当前线程
    current_id, target_id = attach_to_window_thread(hwnd)

    # 模拟按下并释放 Enter 键
    send_key(hwnd, 'o')

    # 解除线程附加
    detach_from_window_thread(current_id, target_id)


if __name__ == "__main__":
    time.sleep(1)
    main()
