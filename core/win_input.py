"""Windows 键盘输入（用于 MuMu WASD 键位映射）"""

from __future__ import annotations

import ctypes

user32 = ctypes.windll.user32

VK = {
    "w": 0x57,
    "a": 0x41,
    "s": 0x53,
    "d": 0x44,
}

KEYEVENTF_KEYUP = 0x0002


def key_down(key: str) -> None:
    vk = VK[key.lower()]
    user32.keybd_event(vk, 0, 0, 0)


def key_up(key: str) -> None:
    vk = VK[key.lower()]
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def tap_key(key: str, duration_sec: float = 0.05) -> None:
    import time

    key_down(key)
    time.sleep(duration_sec)
    key_up(key)
