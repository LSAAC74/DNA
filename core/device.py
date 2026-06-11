"""ADB / uiautomator2 设备连接封装"""

from __future__ import annotations

import logging
import subprocess
import sys
import time
from typing import Optional

import numpy as np
import uiautomator2 as u2

import config

logger = logging.getLogger(__name__)

# 在 Windows 下避免打包为 windowed 应用时 subprocess 弹出黑色命令框
_SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class Device:
    def __init__(self, serial: Optional[str] = None):
        self.serial = serial or config.DEVICE_SERIAL
        self._d: Optional[u2.Device] = None

    def connect(self) -> u2.Device:
        if self._d is None:
            self._adb("connect", self.serial)
            self._d = u2.connect(self.serial)
        return self._d

    @property
    def d(self) -> u2.Device:
        return self.connect()

    def _adb(self, *args: str) -> subprocess.CompletedProcess:
        cmd = [config.ADB_PATH, "-s", self.serial, *args]
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            creationflags=_SUBPROCESS_FLAGS,
        )

    def screenshot_bgr(self) -> np.ndarray:
        import cv2

        raw = self.d.screenshot(format="opencv")
        if isinstance(raw, np.ndarray):
            return raw
        return cv2.cvtColor(np.array(raw), cv2.COLOR_RGB2BGR)

    def tap(self, x: int, y: int) -> None:
        self._adb("shell", "input", "tap", str(int(x)), str(int(y)))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int) -> None:
        """ADB 滑动/长按，模拟器在后台也可执行"""
        self._adb(
            "shell",
            "input",
            "swipe",
            str(int(x1)),
            str(int(y1)),
            str(int(x2)),
            str(int(y2)),
            str(max(1, int(duration_ms))),
        )

    def joystick_hold(
        self,
        cx: int,
        cy: int,
        tx: int,
        ty: int,
        hold_sec: float,
    ) -> None:
        """真正按住摇杆：按下中心 → 拖到方向 → 保持 → 抬起（后台可用）"""
        (
            self.d.touch.down(cx, cy)
            .move(tx, ty)
            .sleep(max(0.05, hold_sec))
            .up(tx, ty)
        )

    def key_e(self) -> None:
        self._adb("shell", "input", "keyevent", str(config.ANDROID_KEYCODE_E))

    def launch_game(self) -> None:
        """通过 adb monkey 启动游戏"""
        self._adb(
            "shell",
            "monkey",
            "-p",
            config.GAME_PACKAGE,
            "-c",
            "android.intent.category.LAUNCHER",
            "1",
        )

    # ------------------------------------------------------------------
    # 异常恢复：重启模拟器 + 重新进入游戏
    # ------------------------------------------------------------------

    def restart_emulator(self) -> bool:
        """杀掉并重启 MuMu 模拟器"""
        logger.info("正在关闭模拟器 (%s)...", config.MUMU_PROCESS_NAME)
        subprocess.run(
            ["taskkill", "/f", "/im", config.MUMU_PROCESS_NAME],
            capture_output=True,
            text=True,
            check=False,
            creationflags=_SUBPROCESS_FLAGS,
        )
        time.sleep(config.EMULATOR_RESTART_WAIT_SEC)

        logger.info("正在启动模拟器...")
        proc = subprocess.Popen(
            [config.MUMU_EMULATOR_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_SUBPROCESS_FLAGS,
        )
        # 等待 adb 就绪
        logger.info("等待模拟器启动 (adb 在线，最长 %ds)...", config.EMULATOR_BOOT_TIMEOUT)
        deadline = time.time() + config.EMULATOR_BOOT_TIMEOUT
        while time.time() < deadline:
            result = subprocess.run(
                [config.ADB_PATH, "connect", self.serial],
                capture_output=True,
                text=True,
                check=False,
                creationflags=_SUBPROCESS_FLAGS,
            )
            if "connected" in result.stdout.lower() or "already" in result.stdout.lower():
                logger.info("模拟器 adb 已就绪")
                time.sleep(3.0)  # 额外等 Android 启动完成
                self._d = None  # 重置连接
                return True
            time.sleep(2.0)

        logger.error("模拟器启动超时")
        return False

    def enter_game(self) -> bool:
        """检测 in.png（进入游戏按钮）并点击"""
        logger.info("启动游戏应用...")
        self.launch_game()

        logger.info("等待游戏加载 (%ds)...", config.GAME_LAUNCH_WAIT_SEC)
        time.sleep(config.GAME_LAUNCH_WAIT_SEC)

        from core.recognizer import Recognizer

        recognizer = Recognizer()
        in_path = config.TEMPLATES.get("in", "")
        if not in_path:
            logger.error("未配置 in.png 模板路径")
            return False

        logger.info("等待「进入游戏」按钮出现...")
        result = recognizer.wait_for(
            self, "in", config.IN_BUTTON_TIMEOUT, template_path=in_path
        )
        if not result.found or not result.center:
            logger.error(
                "未找到「进入游戏」按钮 (最高 %.2f)", result.confidence
            )
            return False

        x, y = result.center
        logger.info("点击「进入游戏」@ (%s, %s) 置信度 %.2f", x, y, result.confidence)
        self.tap(x, y)
        time.sleep(config.GAME_LAUNCH_WAIT_SEC)
        return True
