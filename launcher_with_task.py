import sys
import subprocess
import time
import win32con
import ctypes
import win32api
import win32gui

launcher_path = r"D:\rj\yys\onmyoji\Launch.exe"  # 修改成你的实际路径
task_name = "LaunchOnmyoji"
target_title = "阴阳师-网易游戏"
new_title_template = "阴阳师{}号"

def move_window(hwnd, x, y, width, height):
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, x, y, width, height, 0)
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin(args):
    params = ' '.join(args)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)

def create_task():
    print("检测到任务计划不存在，正在创建任务计划（普通权限运行）...")
    # /RL LIMITED 表示普通权限运行
    cmd = (
        f'schtasks /Create /TN "{task_name}" /TR "{launcher_path}" /SC ONCE /ST 00:00 '
        f'/RL LIMITED /F'
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("任务计划创建成功！")
    else:
        print("任务计划创建失败：", result.stderr)
        sys.exit(1)

def task_exists():
    cmd = f'schtasks /Query /TN "{task_name}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

def start_task():
    cmd = f'schtasks /Run /TN "{task_name}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("通过任务计划启动了普通权限窗口。")
    else:
        print("任务计划启动失败：", result.stderr)
        sys.exit(1)

def start_admin_instance():
    print("启动第一个管理员权限阴阳师窗口...")
    subprocess.Popen([launcher_path])
    time.sleep(10)

def main():
    if len(sys.argv) < 2:
        print("用法: launcher_with_task.py <窗口总数>")
        input("按回车退出...")
        return

    try:
        total = int(sys.argv[1])
        if total < 1:
            raise ValueError
    except ValueError:
        print("请输入有效的正整数！")
        input("按回车退出...")
        return

    if not is_admin():
        print("当前不是管理员权限，尝试以管理员权限重启...")
        run_as_admin(sys.argv)
        return

    # 管理员权限下先启动第一个窗口
    start_admin_instance()

    # 检查任务计划是否存在，不存在则创建
    if not task_exists():
        create_task()

    # 通过任务计划启动剩余窗口（普通权限）
    remaining = total - 1
    if remaining > 0:
        for i in range(remaining):
            start_task()
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

    for i, hwnd in enumerate(matched_windows[:total]):
        new_title = new_title_template.format(i + 1)
        win32gui.SetWindowText(hwnd, new_title)

        x, y = positions[i]
        move_window(hwnd, x, y, win_w, win_h)
        print(f"🎯 第 {i+1} 个窗口重命名并移动到 ({x}, {y})")

    input("全部窗口启动完成，按回车退出...")

if __name__ == "__main__":
    main()
