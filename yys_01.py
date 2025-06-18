import random

import numpy as np
import pygetwindow as gw
import pyautogui
import cv2
from PIL import ImageGrab
import time
import threading
import keyboard
from pathlib import Path
import json
import datetime
from pywinauto.application import Application
import win32gui, win32con

# 全局退出标志
stop_flag = False
pause_flag = False
flag_lock = threading.Lock()

# 图像匹配相似度阈值
threshold = 0.8

#参数
x_overall = {}
y_overall = {}
total = {}
size = 200 # 局数q
time_per_game = 18 #单位s

# 目标窗口标题列表 + 目标图片路径
window_titles = ["MuMu模拟器13","MuMu模拟器12"]
# === 日志输出统一函数 ===
def log(msg):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    thread_name = threading.current_thread().name
    print(f"[{now}][{thread_name}] {msg}")


# === 键盘监听线程 ===
def keyboard_listener():
    global stop_flag, pause_flag,x_overall, y_overall, total
    print("⌨️ 键盘监听已启动：按下 q 键可终止脚本")
    while True:
        if keyboard.is_pressed('q'):
            with flag_lock:
                stop_flag = True
            log("🚨 按下 q：停止所有线程")
            break
        elif keyboard.is_pressed('p'):
            with flag_lock:
                pause_flag = True
            log("⏸️ 按下 p：已暂停")
            time.sleep(0.5)
        elif keyboard.is_pressed('r'):
            with flag_lock:
                pause_flag = False
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
        with flag_lock:
            if stop_flag:
                log(f"grab() 检测到停止标志，退出")
                return
            while pause_flag:
                log("grab() 暂停中...")
                time.sleep(1)
        # 4. 截图窗口区域
        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        # screenshot.save("dist/1.png")
        width, height = screenshot.size  # 返回 (宽, 高)
        # print(f"{img_path}截图大小: 宽={width}, 高={height}")
        template = cv2.imread(img_path, 0)  # 目标图像（按钮、图标等）
        height, width = template.shape  # 高度, 宽度
        # print(f"{img_path}模板尺寸: 宽={width}, 高={height}")
        # 5. 匹配图像特征点
        max_val,max_loc = get_max_val(screenshot,template)
        if max_val >= threshold:
            print(f"{img_path}{win.title}图像匹配成功")
            if img_path == "dist/huodong/tiaozhan.png" and x_overall.get(win.title) is None and y_overall.get(win.title)is None  :
                print("初始化")
                match_x, match_y = max_loc
                x_overall[win.title] = left + match_x + template.shape[1] // 2
                y_overall[win.title] = top + match_y + template.shape[0] // 2
            # print("图像匹配成功")
            if x_overall.get(win.title) is not None and y_overall.get(win.title)is not None  :
                offset_x = x_overall[win.title] + x
                offset_y = y_overall[win.title] + y
            else:
                match_x, match_y = max_loc
                offset_x = left + match_x + template.shape[1] // 2 + x
                offset_y = top + match_y + template.shape[0]  // 2 + y

            mouse_lock = threading.Lock()
            with mouse_lock:
                safe_activate_window(win)  # 激活窗口，使其显示在最前面
                pyautogui.moveTo(offset_x, offset_y, duration=0)
                pyautogui.click()
                # print(f"🎯 已点击 {win.title} 坐标: ({offset_x}, {offset_y})")
                # 判断是否跳转成功未成功在点击一次
                screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
                max_val, max_loc = get_max_val(screenshot, template)
                if max_val >= threshold:
                    safe_activate_window(win)
                    pyautogui.click()
            if img_path == "dist/huodong/tiaozhan.png":
                if total.get(win.title) is None:
                    total[win.title] = 0
                total[win.title]  += 1
                time.sleep(time_per_game)
                print(f'{win.title}已经打了{total[win.title]}')
            break
        else:
            # print(f"{img_path}图像未匹配 {win.title}")
            break

def get_coordinate(file_path):
    with open(f"{file_path}/img.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        return data

def safe_activate(titles):
    try:
        app = Application().connect(title=titles)
        window_spec = app.window(title=titles)
        window_spec.set_focus()
        window = window_spec.wrapper_object()  # 获取窗口wrapper对象
        window.move_window(x=None, y=None, width=1280, height=720, repaint=True)
        log(f"✅ 激活窗口成功: {window_spec.window_text()}")
        time.sleep(10)
    except Exception as e:
        log(f"❌ 激活窗口失败: {titles}，错误：{e}")

def process_window(wins):

    mouse_lock = threading.Lock()
    with mouse_lock:
        print(f"激活窗口 {win.title}")
        safe_activate(wins.title)

    time.sleep(1)
    left, top = wins.left, wins.top
    right = left + wins.width
    bottom = top + wins.height
    file_path = "img/huodong/"

    folder = Path(file_path)  # 这是一个 WindowsPath 对象

    while True:
        if total.get(wins.title) is not None and total[wins.title] >= size:
            break
        files = folder.iterdir()
        # 获取特点偏移量  为配置默认80
        datas = get_coordinate(file_path)
        # 循环匹配图片
        for f in files:
            with flag_lock:
                if stop_flag:
                    log(f"grab() 检测到停止标志，退出")
                    return
                while pause_flag:
                    log("grab() 暂停中...")
                    time.sleep(0.5)

            if f.name.endswith(".png"):
                time.sleep(0.3)
                for data in datas:
                    temp = False
                    if data["name"] == f.name.replace(".png","") :
                        left_coor, right_coor, top_coor,bottom_coor = map(int,data["coordinate"].split(","))
                        grab(left, top, right, bottom, f"{file_path}{f.name}", random.randint(left_coor, right_coor),
                             random.randint(top_coor, bottom_coor), wins)
                        temp = True
                        break
                    if not temp:
                        grab(left, top, right, bottom, f"{file_path}{f.name}",
                             random.randint(-40, 40), random.randint(-40, 40), wins)

if __name__ == '__main__':
    seen_hwnds = set()

    # 查找窗口句柄
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
    # 启动键盘监听线程




    listener_thread = threading.Thread(target=keyboard_listener, daemon=True)
    listener_thread.start()
    # for win in windows:
    #     process_window(win)
    #     # 遍历处理每个窗口
 # 提交多个任务
    threads = []
    for win in windows:
        log(f"提交任务{win.title}")
        time.sleep(3)
        t = threading.Thread(target=process_window, args=(win,))
        t.start()
        threads.append(t)

    # 等待所有线程结束
    for t in threads:
        t.join()