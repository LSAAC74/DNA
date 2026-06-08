"""录制走位路径 → 写入 move_path.py

用法：
  1. 以管理员身份打开终端（推荐）
  2. 进战斗后运行本工具
  3. 3 秒内切换到 MuMu
  4. 用 WASD 走一遍路线（可连续换方向，不必刻意松开）
  5. 切回终端按 Enter 结束，或按 Q 结束

原理：每 50ms 轮询按键状态（比事件钩子更可靠，MuMu 抢焦点时也能录到）
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "move_path.py"

try:
    import keyboard
except ImportError:
    print("请先安装: pip install keyboard")
    sys.exit(1)

KEY_ORDER = "wasd"
MIN_STEP_SEC = 0.08


def current_combo() -> str:
    return "".join(k for k in KEY_ORDER if keyboard.is_pressed(k))


def main() -> None:
    print("=" * 50)
    print("走位录制工具（轮询模式）")
    print("  3 秒后切换到 MuMu，用 WASD 走完整条路线")
    print("  结束后切回此窗口按 Enter，或在任意位置按 Q")
    print("=" * 50)
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    path: list[dict[str, object]] = []
    recording = True
    last_combo = ""
    segment_start = time.time()

    def stop() -> None:
        nonlocal recording
        recording = False

    def on_q(_event: keyboard.KeyboardEvent) -> None:
        stop()

    keyboard.on_press_key("q", on_q, suppress=False)

    print("\n录制中... (按 Q 结束)\n")

    try:
        while recording:
            combo = current_combo()
            now = time.time()

            if combo != last_combo:
                if last_combo:
                    duration = round(now - segment_start, 2)
                    if duration >= MIN_STEP_SEC:
                        path.append({"key": last_combo, "sec": duration})
                        print(f"  记录: {last_combo} {duration}s")

                last_combo = combo
                segment_start = now

            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        keyboard.unhook_all()

    # 结束前还有一段在按的键
    if last_combo:
        duration = round(time.time() - segment_start, 2)
        if duration >= MIN_STEP_SEC:
            path.append({"key": last_combo, "sec": duration})
            print(f"  记录: {last_combo} {duration}s")

    if not path:
        print("\n未录到任何步骤。请确认：")
        print("  1. 终端以管理员身份运行")
        print("  2. 录制时确实按了 W/A/S/D")
        print("  也可用: python tools/input_path.py 手动输入")
        return

    content = (
        '"""自动录制的走位路径 — 复制 MOVE_PATH 到 config.py"""\n\n'
        f"MOVE_PATH = {path!r}\n"
    )
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"\n共 {len(path)} 步，已保存到 {OUTPUT}")
    print("请将 MOVE_PATH 复制到 config.py")


if __name__ == "__main__":
    main()
