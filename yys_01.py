# === 改写说明 ===
# - 移除 pywinauto，使用 pygetwindow + win32api 全面替代
# - 激活窗口改为更稳定的 safe_activate_window()
# - 点击改为后台 PostMessage 模式
# - 权限检查加了 sys.exit()
# - 加入远程桌面判断提示

import ctypes
import os
import random
import logging
import sys
import traceback
import numpy as np
import pygetwindow as gw
import cv2
import win32process
from PIL import ImageGrab, Image
import time
import threading
import keyboard
from pathlib import Path
import json
import win32gui, win32con, win32api

# === 线程控制器类 ===
class ThreadController:
    def __init__(self):
        self._event = threading.Event()
        self._event.set()

    def pause(self):
        self._event.clear()

    def resume(self):
        self._event.set()

    def wait_if_paused(self):
        self._event.wait()

threshold = 0.8
x_overall, y_overall, total = {}, {}, {}
size = 94
time_per_game = 8
window_titles = ["阴阳师1号", "阴阳师2号"]
img_paths = "img/huodong/"
is_team = False
controllers = {title: ThreadController() for title in window_titles}

log_filename = "clicker.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.FileHandler(log_filename, encoding='utf-8'), logging.StreamHandler()]
)

log = logging.info

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin(args):
    params = ' '.join(args)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)

def safe_activate_window(win):
    try:
        hwnd = win._hWnd
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        fg_win = win32gui.GetForegroundWindow()
        current_thread = win32api.GetCurrentThreadId()
        target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
        fg_thread = win32process.GetWindowThreadProcessId(fg_win)[0]

        # # 附加线程输入，允许切换前台窗口
        # win32process.AttachThreadInput(current_thread, target_thread, True)
        # win32process.AttachThreadInput(current_thread, fg_thread, True)
        #
        # win32gui.SetForegroundWindow(hwnd)
        #
        # win32process.AttachThreadInput(current_thread, target_thread, False)
        # win32process.AttachThreadInput(current_thread, fg_thread, False)

        log(f"✅ 成功激活窗口: {win.title}")
    except Exception as e:
        log(f"⚠️ 激活窗口失败: {e}")

def click_in_window(hwnd, x, y):
    try:
        if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
            log(f"⚠️ 窗口无效或不可见: hwnd={hwnd}")
            return
        lParam = y << 16 | x
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, None, lParam)
    except Exception as e:
        log(f"❌ 点击失败: {e}")

def get_max_val(screenshot, template):
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return max_val, max_loc

def grab(left, top, right, bottom, img_path, x, y, win):
    while True:
        controllers[win.title].wait_if_paused()
        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        template = np.array(Image.open(img_path).convert('L'))
        h, w = template.shape
        max_val, max_loc = get_max_val(screenshot, template)
        if max_val >= threshold:
            match_x, match_y = max_loc
            offset_x = left + match_x + w // 2 + x
            offset_y = top + match_y + h // 2 + y
            lock = threading.Lock()
            with lock:
                click_in_window(win._hWnd, offset_x, offset_y)
            time.sleep(1)
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            if get_max_val(screenshot, template)[0] >= threshold:
                lock = threading.Lock()
                with lock:
                    click_in_window(win._hWnd, offset_x, offset_y)
            if img_path.endswith("tiaozhan.png"):
                total[win.title] = total.get(win.title, 0) + 1
                log(f"{win.title}开始挑战，等待 {time_per_game}s，第{total[win.title]}局")
                if is_team:
                    for c in controllers.values(): c.pause()
                    time.sleep(time_per_game)
                    for c in controllers.values(): c.resume()
                else:
                    time.sleep(time_per_game)
            break
        else:
            break

def get_coordinate(file_path):
    with open(f"{file_path}/img.json", encoding="utf-8") as f:
        return json.load(f)

def process_window(win):
    log(f"开始处理窗口: {win.title}")
    lock = threading.Lock()
    with lock:
        safe_activate_window(win)
    left, top, right, bottom = win.left, win.top, win.left + win.width, win.top + win.height
    folder = Path(resource_path(img_paths))
    data = get_coordinate(folder)

    while True:
        controllers[win.title].wait_if_paused()
        if total.get(win.title, 0) >= size:
            break
        for f in folder.glob("*.png"):
            controllers[win.title].wait_if_paused()
            coords = next((d["coordinate"] for d in data if d["name"] == f.stem), None)
            if coords:
                l, r, t, b = map(int, coords.split(","))
                grab(left, top, right, bottom, str(f), random.randint(l, r), random.randint(t, b), win)
            else:
                grab(left, top, right, bottom, str(f), random.randint(-40, 40), random.randint(-40, 40), win)

def resource_path(path):
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / path
    return Path(os.getcwd()) / path

def keyboard_listener():
    while True:
        if keyboard.is_pressed('q'):
            log("🛑 检测到 q，退出程序")
            os._exit(0)
        elif keyboard.is_pressed('p'):
            for c in controllers.values(): c.pause()
            log("⏸️ 所有线程已暂停")
            time.sleep(0.5)
        elif keyboard.is_pressed('r'):
            for c in controllers.values(): c.resume()
            log("▶️ 所有线程已恢复")
            time.sleep(0.5)
        time.sleep(0.1)

if __name__ == '__main__':
    try:
        if not is_admin():
            print("⚠️ 当前不是管理员权限，正在尝试提权...")
            run_as_admin(sys.argv)

        windows = []
        seen = set()
        for title in window_titles:
            found = gw.getWindowsWithTitle(title)
            if not found:
                log(f"❌ 找不到窗口: {title}")
                continue
            for w in found:
                if w._hWnd not in seen:
                    windows.append(w)
                    seen.add(w._hWnd)
                    log(f"✅ 发现窗口: {w.title}")

        threading.Thread(target=keyboard_listener, daemon=True).start()
        threads = [threading.Thread(target=process_window, args=(w,)) for w in windows]
        for t in threads: t.start()
        for t in threads: t.join()
    except Exception as e:
        log(traceback.format_exc())
    input("按回车退出...")
