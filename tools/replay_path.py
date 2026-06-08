"""测试走位路径（不跑完整挂机流程）"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config
from core.device import Device
from core.movement import execute_move_path


def main() -> None:
    print(f"模式: {config.MOVEMENT_MODE}")
    print(f"路径: {config.MOVE_PATH}")
    print("3 秒后开始走位（MuMu 可在后台，无需切窗口）...")
    time.sleep(3)

    device = Device()
    device.connect()
    execute_move_path(device)
    print("走位完成")


if __name__ == "__main__":
    main()
