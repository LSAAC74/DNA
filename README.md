# 《二重螺旋》夜航手册挂机脚本

基于 **OpenCV + ADB + uiautomator2** 的自动化挂机脚本，支持《二重螺旋》手游在 **MuMu 模拟器** 中自动完成夜航手册副本。

---

## 功能特性

- **多等级副本支持**：20 / 30 / 40 / 50 / 65 / 75 级
- **智能图像识别**：OpenCV 模板匹配，自动识别按钮、地图、战斗状态
- **地图识别（40/50级）**：自动区分不同地图并执行对应走位
- **倍率书自动选择**：支持 1~4 倍率书，自动匹配颜色
- **异常自动恢复**：模拟器异常或游戏崩溃时，自动重启模拟器并重新进入游戏
- **GUI 可视化界面**：Tkinter 图形界面，配置简单直观
- **走位录制工具**：支持录制 WASD 走位并生成配置
- **后台运行**：ADB 摇杆模式支持 MuMu 后台运行

---

## 环境要求

| 项目 | 要求 |
|------|------|
| **操作系统** | Windows 10/11 |
| **模拟器** | MuMu 模拟器 12（分辨率 1920×1080） |
| **ADB** | MuMu 自带 adb 或独立 adb |
| **Python** | 3.11+ |
| **分辨率** | 1920 × 1080（须与模拟器设置一致） |

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/LSAAC74/DNA.git
cd DNA
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置 ADB 路径

编辑 [config.py](config.py)，修改为你的 MuMu adb 路径：

```python
ADB_PATH = r"D:\Program Files\Netease\MuMu\nx_device\12.0\shell\adb.exe"
DEVICE_SERIAL = "127.0.0.1:16384"
```

### 5. 启动 GUI

```bash
python gui.py
```

或直接使用打包好的 exe：

```bash
dist\DnaAfkGui.exe
```

---

## 使用说明

### GUI 界面配置

| 参数 | 说明 |
|------|------|
| **等级** | 选择副本等级（20/30/40/50/65/75） |
| **前往序号** | 选择第几个副本（1 开始） |
| **倍率书** | 选择倍率书颜色（绿/蓝/紫/橙） |
| **倍率轮数** | 使用倍率书的轮数 |
| **循环轮数** | 总挂机轮数 |

### 等级特性

| 等级 | 前往数/页 | 特殊说明 |
|------|-----------|----------|
| 20 | 4 | 需先向下滑动列表 |
| 30 | 4 | 需先向下滑动列表 |
| 40 | 5 | **双地图识别**（40-1 / 40-2），先按 E 再走位 |
| 50 | 5 | **双地图识别**（50-1 / 50-2），共 7 个副本，先走位再按 E |
| 65 | 5 | 黎瑟标准挂机，先走位再按 E |
| 75 | 5 | 共 9 个副本 |

### 命令行模式

```bash
# 仅执行一轮（不含首次 start）
python main.py --once

# 含首次 start 的一轮
python main.py --once --with-start

# 调试模式
python main.py --once -v
```

---

## 项目结构

```
.
├── assets/                 # 图像模板资源
│   ├── levels/            # 等级数字模板（20~80）
│   ├── maps/              # 地图识别模板（40-1, 40-2, 50-1, 50-2...）
│   ├── multiply/          # 倍率书颜色模板（1~4）
│   ├── begin.png          # 开始挑战按钮
│   ├── fighting.png       # 战斗中标识
│   ├── go.png             # 前往按钮
│   ├── in.png             # 进入游戏按钮
│   ├── loading.png        # 加载中标识
│   ├── restart.png        # 重新开始按钮
│   └── start.png          # 开始按钮
├── core/                   # 核心模块
│   ├── actions.py         # 游戏操作封装（走位、按E、点击）
│   ├── device.py          # ADB 设备连接与控制
│   ├── dungeon_profile.py # 副本配置（等级、走位、地图）
│   ├── map_detect.py      # 地图识别引擎
│   ├── movement.py        # 摇杆/键盘走位控制
│   ├── recognizer.py      # OpenCV 模板匹配引擎
│   ├── runner.py          # 脚本总控（导航+挂机+异常恢复）
│   └── scroll.py          # 列表滚动控制
├── flows/                  # 业务流程
│   ├── lyser_afk.py       # 黎瑟挂机循环（走位、等结束、重开）
│   └── menu_flow.py       # 菜单导航（历练→夜航手册→选副本）
├── tools/                  # 辅助工具
│   ├── calibrate.py       # 摇杆中心校准
│   ├── input_path.py      # 手动输入走位路径
│   ├── record_path.py     # 录制 WASD 走位
│   ├── replay_path.py     # 回放走位路径
│   └── test_match.py      # 模板匹配测试
├── config.py              # 全局配置（ADB路径、分辨率、摇杆参数）
├── gui.py                 # Tkinter GUI 入口
├── main.py                # 命令行入口
├── move_path.py           # 当前走位路径（由录制工具生成）
└── requirements.txt       # Python 依赖
```

---

## 核心机制

### 1. 图像识别流程

```
截图 → OpenCV matchTemplate → 多尺度匹配 → 返回坐标+置信度
```

- 支持多分辨率缩放匹配（0.8~1.2 倍）
- 自动缓存模板图片，避免重复加载
- 可配置匹配阈值和轮询间隔

### 2. 异常恢复流程

```
脚本异常 → 重启 MuMu 模拟器 → 启动游戏 → 识别 in.png → 点击进入
         → 重新执行菜单导航 → 继续挂机
```

- 最多重试 2 次
- 支持模拟器进程管理（taskkill + 启动）

### 3. 地图识别（40/50级）

```
进入副本 → 截图 → 匹配 40-1.png / 40-2.png → 选择对应走位路径
```

- 识别失败时自动回退到默认路径

---

## 辅助工具

### 录制走位路径

```bash
python tools/record_path.py
```

1. 以管理员身份运行终端
2. 进入战斗后运行工具
3. 3 秒内切换到 MuMu 模拟器
4. 用 WASD 走一遍路线
5. 切回终端按 Enter 或 Q 结束

录制结果自动写入 `move_path.py`。

### 校准摇杆中心

```bash
python tools/calibrate.py
```

点击游戏内虚拟摇杆中心，自动计算坐标。

### 测试模板匹配

```bash
python tools/test_match.py --template assets/start.png
```

实时测试模板在当前截图中的匹配效果。

---

## 配置说明

[config.py](config.py) 中的关键配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `ADB_PATH` | adb 可执行文件路径 | MuMu 自带 adb |
| `DEVICE_SERIAL` | 设备序列号 | `127.0.0.1:16384` |
| `SCREEN_WIDTH/HEIGHT` | 屏幕分辨率 | 1920 / 1080 |
| `MOVEMENT_MODE` | 走位模式 | `joystick` |
| `JOYSTICK_CENTER` | 虚拟摇杆中心坐标 | (304, 802) |
| `MATCH_THRESHOLD` | 模板匹配最低置信度 | 0.75 |
| `POLL_INTERVAL` | 图像轮询间隔 | 1.0 秒 |
| `BATTLE_END_TIMEOUT` | 战斗结束超时时间 | 300 秒 |
| `MAX_RECOVERY_RETRIES` | 异常恢复最大重试次数 | 2 |

---

## 注意事项

1. **分辨率必须一致**：模拟器、脚本配置、截图必须都是 1920×1080
2. **MuMu 后台运行**：使用 `joystick` 模式时，MuMu 可以最小化到后台
3. **管理员权限**：录制走位工具需要管理员权限才能捕获键盘输入
4. **首次 start**：首轮挂机包含点击 `start.png`，后续轮次只点 `begin.png`
5. **倍率书**：选择倍率书后，会在前 N 轮自动选择对应颜色

---

## 技术栈

- [OpenCV](https://opencv.org/) — 图像识别与模板匹配
- [uiautomator2](https://github.com/openatx/uiautomator2) — Android UI 自动化
- [ADB](https://developer.android.com/studio/command-line/adb) — Android 调试桥
- [Tkinter](https://docs.python.org/3/library/tkinter.html) — GUI 界面
- [NumPy](https://numpy.org/) — 数值计算
- [keyboard](https://github.com/boppreh/keyboard) — 键盘监听（走位录制）

---

## 免责声明

本脚本仅供学习交流使用，请勿用于商业用途。使用脚本可能导致游戏账号受到处罚，请自行承担风险。

---

## License

MIT License
