"""《二重螺旋》黎瑟挂机脚本配置 — 分辨率 1920×1080"""

import os
import sys


def _asset_path(relative_path: str) -> str:
    """PyInstaller 打包后正确解析资源文件的绝对路径"""
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


# MuMu ADB
ADB_PATH = r"D:\Program Files\Netease\MuMu\nx_device\12.0\shell\adb.exe"
DEVICE_SERIAL = "127.0.0.1:16384"

# 屏幕分辨率（与 MuMu 设置保持一致）
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# 主控角色
MAIN_CHARACTER = "黎瑟"

# ---------------------------------------------------------------------------
# 走位
# ---------------------------------------------------------------------------
# 模式:
#   joystick — ADB 模拟摇杆（推荐，MuMu 在后台也能执行）
#   adb      — 同 joystick
#   keyboard — PC 键盘 WASD（需 MuMu 在前台）
#   tap      — 点击地面（旧方式）
MOVEMENT_MODE = "joystick"

# joystick / keyboard 共用：按顺序按住方向的秒数
# 用 tools/record_path.py 或 tools/input_path.py 生成
# 注意：keyboard 录制的时间用于 joystick 时可能需要微调

MOVE_PATH = [{'key': 's', 'sec': 1.32}, {'key': 'a', 'sec': 6.43}, {'key': 'w', 'sec': 11.45}, {'key': 'a', 'sec': 31.26}]



# 虚拟摇杆 — 用 calibrate.py 点击摇杆中心
JOYSTICK_CENTER = (304, 802)
JOYSTICK_RADIUS = 120
JOYSTICK_HOLD_MODE = "touch"   # touch=真正按住 | chunk=分段滑动备用
JOYSTICK_CHUNK_MS = 250        # 仅 chunk 模式使用

# 旧版点击走位（tap 模式）
MOVE_TARGET = (960, 540)
MOVE_WAIT_SEC = 8.0

MOVE_STEP_PAUSE_SEC = 0.15   # 每步之间的停顿
MOVE_SETTLE_SEC = 0.5        # 走完路径后等待角色停稳

# E 技能：优先 ADB 点击技能按钮（后台可用）；keyevent 对部分映射无效
USE_KEYEVENT_FOR_E = False        # False=点击坐标，后台可用；True=ADB 发 E 键
SKILL_E_POSITION = (1460, 964)    # E 技能按钮屏幕坐标（USE_KEYEVENT_FOR_E=False 时使用）
ANDROID_KEYCODE_E = 33            # Android KeyEvent.KEYCODE_E

# ---------------------------------------------------------------------------
# 夜航手册 / 菜单导航
# ---------------------------------------------------------------------------
MENU_TOP_LEFT = (63, 54)
MENU_COMMISSION = (72, 276)       # 委托

LEVEL_SCROLL_POS = (678, 558)     # 等级列表滚动起点
# 20/30/40/50/60 级 UI 相似，须先向下滑过再模板匹配
LEVELS_SCROLL_DOWN_FIRST = (20, 30, 40, 50, 60)
GO_SCROLL_POS = (1052, 532)       # 前往列表滚动起点（序号>go_per_page 时向上滑）
# GO_PER_PAGE 由副本配置决定，见 core/dungeon_profile.py

# 固定坐标点击「前往」（推荐，避免误点铜币）
USE_FIXED_GO_COORDS = True
GO_BUTTON_X = 1774
GO_FIRST_Y = 273                  # 第 1 个前往
GO_ROW_STEP_Y = 133               # 行间距：273→408(+135)，408→540(+132)，取 133

# 序号>5 时滚动：拖得更久，滚完一屏后第 1 个「前往」= 第 5 项，之后每屏递进 4 项
GO_SCROLL_DISTANCE = 532          # 约 4 行 (4×133)
GO_SCROLL_DURATION_MS = 750       # 拖动时长（毫秒）
GO_SCROLL_PAUSE_SEC = 0.8         # 滚完等待

# 图像匹配备用（USE_FIXED_GO_COORDS=False 时）
GO_MATCH_X_MIN = 950
GO_ROW_Y_TOLERANCE = 45

SCROLL_DISTANCE = 350
SCROLL_DURATION_MS = 400
SCROLL_PAUSE_SEC = 0.6
MAX_LEVEL_SCROLLS = 15
MAX_GO_SCROLLS = 20

LEVEL_ASSETS_DIR = _asset_path("assets/levels")   # 等级图 assets/levels/65.png
LEVEL_FALLBACK_DIR = _asset_path("assets")          # 备选 assets/65.png

# ---------------------------------------------------------------------------
# OpenCV 模板（assets/ 目录，1920×1080 下截取）
# ---------------------------------------------------------------------------
TEMPLATES = {
    "tempering": _asset_path("assets/tempering.png"),   # 历练
    "book": _asset_path("assets/book.png"),             # 夜航手册
    "go": _asset_path("assets/go.png"),                 # 前往
    "start": _asset_path("assets/start.png"),
    "begin": _asset_path("assets/begin.png"),
    "restart": _asset_path("assets/restart.png"),
    "fighting": _asset_path("assets/fighting.png"),
    "loading": _asset_path("assets/loading.png"),
    "in": _asset_path("assets/in.png"),                     # 进入游戏
}

# 倍率书（assets/multiply/，从低到高：绿 → 蓝 → 粉 → 橙）
MULTIPLY_BOOKS = {
    "green": _asset_path("assets/multiply/1.png"),
    "blue": _asset_path("assets/multiply/2.png"),
    "pink": _asset_path("assets/multiply/3.png"),
    "orange": _asset_path("assets/multiply/4.png"),
}
MULTIPLY_BOOK_LABELS = {
    "green": "绿",
    "blue": "蓝",
    "pink": "粉",
    "orange": "橙",
}
MULTIPLY_BOOK_BY_LABEL = {v: k for k, v in MULTIPLY_BOOK_LABELS.items()}

MAP_MATCH_THRESHOLD = 0.55
MAP_MATCH_THRESHOLD_FALLBACK = 0.50
MAP_TEMPLATE_LARGE_WIDTH = 800   # 超过此宽度视为大图，启用缩小匹配

MATCH_THRESHOLD = 0.80
MATCH_SCALES = [0.90, 0.95, 1.0, 1.05, 1.10, 1.15]

# 各模板单独阈值（黑底 UI 条匹配分偏低，需单独设置）
TEMPLATE_THRESHOLDS = {
    "tempering": 0.65,
    "book": 0.65,
    "go": 0.72,
    "start": 0.75,
    "begin": 0.55,
    "restart": 0.55,
    "fighting": 0.65,
    "loading": 0.70,
    "in": 0.70,
    "map": 0.65,
    "multiply": 0.65,
}

TEMPLATE_SCALES = {
    "tempering": MATCH_SCALES,
    "book": MATCH_SCALES,
    "go": MATCH_SCALES,
    "start": MATCH_SCALES,
    "begin": MATCH_SCALES,
    "restart": MATCH_SCALES,
    "fighting": MATCH_SCALES,
    "loading": [1.0],
    "in": MATCH_SCALES,
    "map": MATCH_SCALES,
    "multiply": MATCH_SCALES,
}

# 只匹配模板左侧固定区域（fighting 右侧血量数字会变化）
TEMPLATE_CROP_LEFT_RATIO = {
    "fighting": 0.45,
}

# 点击点相对匹配框的比例 (x, y)，默认中心为 (0.5, 0.5)
TEMPLATE_CLICK_POINT_RATIO = {
    "multiply": (0.5, 0.85),  # 倍率书：水平居中、偏下方
}

# 小于该尺寸的模板视为无效（如 fighting.png 误截为 2x3）
MIN_TEMPLATE_SIZE = 20

UI_WAIT_TIMEOUT = 60              # 等待 start / begin / restart 出现
BATTLE_START_TIMEOUT = 90         # 点击 begin 后等待进入战斗
BATTLE_END_TIMEOUT = 300          # 单局最长等待（秒）
POLL_INTERVAL = 1.0               # 轮询间隔
AFTER_CLICK_SEC = 1.5             # 每次点击后等待界面响应

# fighting 模板无效时，点击 begin 后固定等待再走位
WAIT_AFTER_BEGIN_SEC = 12.0
MIN_WAIT_AFTER_BEGIN_SEC = 4.0        # 首轮：点击 begin 后至少等待
MIN_WAIT_AFTER_BEGIN_REPEAT_SEC = 7.0   # 第 2 轮起：加载更久，避免过早走位
FIGHTING_STABLE_SEC = 2.5             # fighting 连续出现多久才判定进战斗
BEGIN_GONE_CONFIRM_SEC = 2.0          # begin 消失判定（仅首轮备用）
USE_BEGIN_GONE_FALLBACK = False       # 严格只检测 fighting.png，不依赖 begin 消失判定
BEFORE_MOVE_SEC = 0.5                 # 确认进战斗后、走位前等待（首轮）
BEFORE_MOVE_REPEAT_SEC = 3.0          # 第 2 轮起走位前额外等待

# ---------------------------------------------------------------------------
# 异常恢复：重启模拟器 + 重新进入游戏
# ---------------------------------------------------------------------------
# MuMu 模拟器可执行文件路径（用于进程管理）
MUMU_EMULATOR_PATH = r"D:\Program Files\Netease\MuMu\nx_device\12.0\emulator\nemu\bin\NemuPlayer.exe"
MUMU_PROCESS_NAME = "NemuPlayer.exe"   # 用于 taskkill 的进程名
GAME_PACKAGE = "com.hero.dna.gf"       # 游戏 Android 包名

# 模拟器桌面点击「二重螺旋」图标的坐标（1920×1080 分辨率下）
# 若模拟器已安装该游戏且包名正确，也可通过 adb monkey 启动，不依赖该坐标
GAME_ICON_POS = (100, 100)

# 恢复流程超时（秒）
EMULATOR_RESTART_WAIT_SEC = 10.0       # 杀掉进程后等多久再启动
EMULATOR_BOOT_TIMEOUT = 60.0           # 等待模拟器 adb 在线
GAME_LAUNCH_WAIT_SEC = 15.0            # 启动游戏后等待加载
IN_BUTTON_TIMEOUT = 30.0               # 等待「进入游戏」按钮出现
MAX_RECOVERY_RETRIES = 2               # 最大恢复重试次数
