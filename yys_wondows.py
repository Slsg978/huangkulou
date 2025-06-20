import subprocess
import time
import win32gui
import win32con
import win32api
import ctypes

def move_window(hwnd, x, y, width, height):
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, x, y, width, height, 0)

def run_as_admin(path):
    # 使用ShellExecute以管理员权限启动
    ctypes.windll.shell32.ShellExecuteW(None, "runas", path, None, None, 1)

def main():
    launcher_path = r"D:\rj\yys\onmyoji\Launch.exe"
    target_title = "阴阳师-网易游戏"
    new_title_template = "阴阳师{}号"

    # 用户输入
    try:
        count = int(input("请输入要打开的窗口个数（最多4个）："))
        if count <= 0 or count > 4:
            raise ValueError
    except ValueError:
        print("❌ 输入无效，请输入 1~4 的整数！")
        input("按回车键退出...")
        return

    # 启动多个客户端：第一个用管理员权限，后面用普通方式
    for i in range(count):
        if i == 0:
            run_as_admin(launcher_path)
        else:
            subprocess.Popen(launcher_path)
        print(f"✅ 启动第 {i+1} 个客户端")
        time.sleep(3)

    time.sleep(15)

    # 获取屏幕宽高
    screen_width = win32api.GetSystemMetrics(0)
    screen_height = win32api.GetSystemMetrics(1)

    # 设置窗口宽高（自定义）
    win_w = int(screen_width / 2)
    win_h = int(screen_height / 2)

    # 四个角的位置坐标
    positions = [
        (0, 0),                              # 左上
        (screen_width - win_w, 0),          # 右上
        (0, screen_height - win_h),         # 左下
        (screen_width - win_w, screen_height - win_h)  # 右下
    ]

    matched_windows = []

    def enum_handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title == target_title:
                matched_windows.append(hwnd)

    win32gui.EnumWindows(enum_handler, None)

    for i, hwnd in enumerate(matched_windows[:count]):
        new_title = new_title_template.format(i + 1)
        win32gui.SetWindowText(hwnd, new_title)

        x, y = positions[i]
        move_window(hwnd, x, y, win_w, win_h)
        print(f"🎯 第 {i+1} 个窗口重命名并移动到 ({x}, {y})")

    input("✅ 全部完成，按回车键退出...")

if __name__ == "__main__":
    main()
