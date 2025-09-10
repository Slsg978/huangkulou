import os
import random
import logging
import sys
import traceback

import numpy as np
import pygetwindow as gw
import pyautogui
import cv2
from PIL import ImageGrab, Image
import time
import threading
import keyboard
from pathlib import Path
import json
from pywinauto.application import Application
import win32gui, win32con

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

# 图像匹配相似度阈值
threshold = 0.8

# 参数
x_overall = {}
y_overall = {}
total = {}
#挑战多少局
size = 600
#点击挑战后休息多久
time_per_game = 7

# 目标窗口标题列表 + 目标图片路径
window_titles = ["MuMu模拟器12","MuMu模拟器14"]
img_paths = "img/huodong/"
#是否是组队
is_team = False
# is_team = True

# 控制器字典（一个窗口一个）
controllers = {title: ThreadController() for title in window_titles}

# 配置日志系统
log_filename = "clicker.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(log_filename, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


# === 日志输出统一函数 ===
def log(msg):
    logging.info(msg)


# === 键盘监听线程 ===
def keyboard_listener():
    print("⌨️ 键盘监听已启动：按下 q 键可终止脚本")
    while True:
        if keyboard.is_pressed('q'):
            log("🚨 按下 q：停止所有线程")
            os._exit(0)
        elif keyboard.is_pressed('p'):
            for ctrl in controllers.values():
                ctrl.pause()
            log("⏸️ 按下 p：已暂停")
            time.sleep(0.5)
        elif keyboard.is_pressed('r'):
            for ctrl in controllers.values():
                ctrl.resume()
            log("▶️ 按下 r：恢复运行")
            time.sleep(0.5)
        time.sleep(0.1)

def get_max_val(screenshot,template):
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val,max_loc

def safe_activate_window(win):
    try:
        hwnd = win._hWnd
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"⚠️ 激活窗口失败: {e}")

def grab(left, top, right, bottom,img_path,x,y,win):
    global x_overall, y_overall, total
    while True:
        controllers[win.title].wait_if_paused()

        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))

        imgs = Image.open(img_path).convert('L')
        template = np.array(imgs)
        height, width = template.shape
        max_val,max_loc = get_max_val(screenshot,template)
        # print(img_path)
        if max_val >= threshold:
            if img_path.endswith("tiaozhan.png") and x_overall.get(win.title) is None and y_overall.get(win.title) is None:
                match_x, match_y = max_loc
                x_overall[win.title] = left + match_x + width // 2
                y_overall[win.title] = top + match_y + height // 2

            if x_overall.get(win.title) is not None and y_overall.get(win.title) is not None:
                offset_x = x_overall[win.title] + x
                offset_y = y_overall[win.title] + y
            else:
                match_x, match_y = max_loc
                offset_x = left + match_x + width // 2 + x
                offset_y = top + match_y + height // 2 + y

            safe_activate_window(win)
            pyautogui.moveTo(offset_x, offset_y, duration=0)
            lock = threading.Lock()
            with lock:
                pyautogui.moveTo(offset_x, offset_y, duration=0)
                pyautogui.click()
                if img_path.endswith("tiaozhan.png"):
                    time.sleep(1)
            time.sleep(0.2)

            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            max_val, max_loc = get_max_val(screenshot, template)
            if max_val >= threshold:
                safe_activate_window(win)
                lock = threading.Lock()
                with lock:
                    pyautogui.moveTo(offset_x, offset_y, duration=0)
                    pyautogui.click()
            time.sleep(0.2)

            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            max_val, max_loc = get_max_val(screenshot, template)
            if max_val >= threshold:
                safe_activate_window(win)
                lock = threading.Lock()
                with lock:
                    pyautogui.moveTo(offset_x, offset_y, duration=0)
                    pyautogui.click()


                # max_val, max_loc = get_max_val(screenshot, template)

            if img_path.endswith("tiaozhan.png"):
                log(f"挑战开始：休息{time_per_game}s")
                total[win.title] = total.get(win.title, 0) + 1
                if is_team:
                    for ctrl in controllers.values():
                        ctrl.pause()
                    time.sleep(time_per_game)
                    for ctrl in controllers.values():
                        ctrl.resume()
                else:
                    time.sleep(time_per_game)
                log(f'{win.title}已经打了{total[win.title]}')
            time.sleep(0.5)
            break
        else:
            break

def get_coordinate(file_path):
    with open(f"{file_path}/img.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        return data

def safe_activate(title):
    try:
        app = Application().connect(title=title)
        window = app.window(title=title)
        window.set_focus()
        window.move_window(x=None, y=None, width=1280, height=720, repaint=True)

        log(f"✅ 激活窗口成功: {title}")
        time.sleep(10)
    except Exception as e:
        log(f"❌ 激活窗口失败: {title}，错误：{e}")

def process_window(wins):
    log(f"激活窗口 {wins.title}")
    safe_activate(wins.title)

    time.sleep(1)
    left, top = wins.left, wins.top
    right = left + wins.width
    bottom = top + wins.height
    file_path = resource_path(img_paths)

    folder = Path(file_path)

    while True:
        controllers[wins.title].wait_if_paused()

        if total.get(wins.title) is not None and total[wins.title] >= size:
            if is_team:
                os._exit(0)
            else:
                break

        files = folder.iterdir()
        datas = get_coordinate(file_path)

        for f in files:
            controllers[wins.title].wait_if_paused()
            if f.name.endswith(".png"):
                time.sleep(0.3)
                temp = False
                for data in datas:
                    temp = False
                    if data["name"] == f.name.replace(".png",""):
                        left_coor, right_coor, top_coor, bottom_coor = map(int, data["coordinate"].split(","))
                        grab(left, top, right, bottom, f"{file_path}\\{f.name}", random.randint(left_coor, right_coor),
                             random.randint(top_coor, bottom_coor), wins)
                        temp = True
                        break
                if not temp:
                        grab(left, top, right, bottom, f"{file_path}\\{f.name}", random.randint(-40, 40), random.randint(-40, 40), wins)

def resource_path(relative_path):
    """获取兼容 PyInstaller 的资源文件路径"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 解压到的临时路径
        base_path = Path(sys._MEIPASS)
    else:
        # 脚本运行时所在路径
        base_path = Path(os.getcwd())
    return base_path / relative_path
def list_meipass_files():
    if hasattr(sys, '_MEIPASS'):
        meipass_dir = sys._MEIPASS
        log(f"📦 当前 _MEIPASS 路径: {meipass_dir}")
        for root, dirs, files in os.walk(meipass_dir):
            for name in files:
                log(f"📄 文件:{os.path.join(root, name)}")
            for name in dirs:
                log(f"📁 文件夹:{os.path.join(root, name)}")
    else:
        log("⚠️ 当前不是 PyInstaller 打包运行，_MEIPASS 不存在")

if __name__ == '__main__':
    try:
        seen_hwnds = set()
        windows = []
        for title in window_titles:
            found = gw.getWindowsWithTitle(title)
            if found:
                for win in found:
                    if win._hWnd not in seen_hwnds:
                        seen_hwnds.add(win._hWnd)
                        windows.append(win)
                        print(f"✅ 找到窗口: {win.title} - hwnd: {win._hWnd}")
                    else:
                        print(f"⚠️ 重复窗口忽略: {win.title} - hwnd: {win._hWnd}")
            else:
                print(f"❌ 找不到窗口: {title}")

        listener_thread = threading.Thread(target=keyboard_listener, daemon=True)
        listener_thread.start()
        # list_meipass_files()
        threads = []
        for win in windows:
            log(f"提交任务{win.title}")
            time.sleep(3)
            t = threading.Thread(target=process_window, args=(win,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()
    except Exception as e:
        log(traceback.print_exc())
    input("按回车退出...")

