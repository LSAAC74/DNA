"""坐标与模板采集工具 — 在 MuMu 1920×1080 下使用

操作：
  python tools/calibrate.py              # 点击取坐标，按 q 退出
  python tools/calibrate.py --capture  # 全屏截图保存到 assets/_raw/
  python tools/calibrate.py --crop     # 框选区域保存为模板
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import cv2

import config
from core.device import Device

RAW_DIR = ROOT / "assets" / "_raw"
ASSETS_DIR = ROOT / "assets"


def capture_screen(device: Device, name: str | None = None) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RAW_DIR / (name or f"screen_{stamp}.png")
    screen = device.screenshot_bgr()
    cv2.imwrite(str(path), screen)
    print(f"已保存: {path}")
    return path


def pick_points(device: Device) -> None:
    print("在窗口中左键点击取坐标，按 q 退出")
    print(f"设备: {config.DEVICE_SERIAL}  分辨率: {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
    print("-" * 50)

    while True:
        screen = device.screenshot_bgr()
        display = screen.copy()

        def on_mouse(event, x, y, _flags, _param):
            if event == cv2.EVENT_LBUTTONDOWN:
                print(f"  坐标: ({x}, {y})")
                cv2.circle(display, (x, y), 8, (0, 255, 0), 2)
                cv2.imshow("calibrate", display)

        cv2.namedWindow("calibrate", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("calibrate", 1280, 720)
        cv2.setMouseCallback("calibrate", on_mouse)
        cv2.imshow("calibrate", display)

        key = cv2.waitKey(500) & 0xFF
        if key == ord("q"):
            break
        if key == ord("s"):
            capture_screen(device)

    cv2.destroyAllWindows()


def crop_template(image_path: str, output_name: str) -> None:
    img = cv2.imread(image_path)
    if img is None:
        print(f"无法读取: {image_path}")
        return

    print("拖动鼠标框选区域，回车确认，c 取消")
    roi = cv2.selectROI("crop", img, fromCenter=False, showCrosshair=True)
    cv2.destroyAllWindows()

    x, y, w, h = roi
    if w == 0 or h == 0:
        print("未选择区域")
        return

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    out = ASSETS_DIR / output_name
    crop = img[y : y + h, x : x + w]
    cv2.imwrite(str(out), crop)
    print(f"模板已保存: {out}  尺寸: {w}x{h}")


def main() -> None:
    parser = argparse.ArgumentParser(description="坐标/模板校准")
    parser.add_argument("--capture", action="store_true", help="截图到 assets/_raw/")
    parser.add_argument("--crop", metavar="IMAGE", help="从截图框选模板")
    parser.add_argument("--out", default="template.png", help="--crop 输出文件名")
    args = parser.parse_args()

    device = Device()
    device.connect()

    if args.crop:
        crop_template(args.crop, args.out)
        return

    if args.capture:
        capture_screen(device)
        return

    pick_points(device)


if __name__ == "__main__":
    main()
