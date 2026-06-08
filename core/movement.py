"""角色移动：WASD 路径回放（ADB 摇杆 / 键盘）"""

from __future__ import annotations

import logging
import math
import sys
import time

import config
from core.device import Device

logger = logging.getLogger(__name__)

# WASD → 方向向量 (x右, y下)
_DIRECTIONS: dict[str, tuple[float, float]] = {
    "w": (0.0, -1.0),
    "s": (0.0, 1.0),
    "a": (-1.0, 0.0),
    "d": (1.0, 0.0),
}


def _normalize_keys(keys: str) -> str:
    allowed = set(_DIRECTIONS)
    result = "".join(c for c in keys.lower() if c in allowed)
    if not result:
        raise ValueError(f"无效方向键: {keys!r}，请使用 w/a/s/d 组合")
    return result


def _combined_vector(keys: str) -> tuple[float, float]:
    keys = _normalize_keys(keys)
    vx = vy = 0.0
    for c in keys:
        dx, dy = _DIRECTIONS[c]
        vx += dx
        vy += dy
    length = math.hypot(vx, vy)
    if length == 0:
        return 0.0, 0.0
    return vx / length, vy / length


def move_via_joystick(device: Device, keys: str, duration_sec: float) -> None:
    """模拟摇杆按住指定方向 duration_sec 秒。"""
    cx, cy = config.JOYSTICK_CENTER
    radius = config.JOYSTICK_RADIUS
    vx, vy = _combined_vector(keys)
    tx = int(cx + vx * radius)
    ty = int(cy + vy * radius)

    logger.info(
        "摇杆按住 %s %.2fs: (%s,%s)→(%s,%s)",
        keys,
        duration_sec,
        cx,
        cy,
        tx,
        ty,
    )

    if config.JOYSTICK_HOLD_MODE == "touch":
        device.joystick_hold(cx, cy, tx, ty, duration_sec)
        return

    # fallback: 分段滑动
    deadline = time.time() + duration_sec
    chunk_ms = config.JOYSTICK_CHUNK_MS
    while time.time() < deadline:
        remaining_ms = int((deadline - time.time()) * 1000)
        if remaining_ms <= 0:
            break
        ms = max(50, min(chunk_ms, remaining_ms))
        device.swipe(cx, cy, tx, ty, ms)


def move_via_keyboard(keys: str, duration_sec: float) -> None:
    """向 MuMu 窗口发送 PC 键盘 WASD（需模拟器在前台且已映射键位）"""
    if sys.platform != "win32":
        raise RuntimeError("keyboard 模式仅支持 Windows")

    from core.win_input import key_down, key_up

    keys = _normalize_keys(keys)
    try:
        for c in keys:
            key_down(c)
        time.sleep(duration_sec)
    finally:
        for c in keys:
            key_up(c)


def execute_move_path(
    device: Device,
    path: list[dict] | None = None,
) -> None:
    mode = config.MOVEMENT_MODE
    move_path = path if path is not None else config.MOVE_PATH

    if mode == "tap":
        x, y = config.MOVE_TARGET
        logger.info("点击走位 (%s, %s)，等待 %.1fs", x, y, config.MOVE_WAIT_SEC)
        device.tap(x, y)
        time.sleep(config.MOVE_WAIT_SEC)
        return

    if not move_path:
        logger.warning("MOVE_PATH 为空，跳过走位")
        return

    use_joystick = mode in ("joystick", "adb")

    logger.info("执行走位路径 (%s)，共 %d 步", mode, len(move_path))
    for i, step in enumerate(move_path, 1):
        keys = step["key"]
        sec = float(step["sec"])
        logger.info("  步骤 %d: %s %.2fs", i, keys, sec)
        if use_joystick:
            move_via_joystick(device, keys, sec)
        elif mode == "keyboard":
            move_via_keyboard(keys, sec)
        else:
            raise ValueError(f"未知 MOVEMENT_MODE: {mode}")
        if config.MOVE_STEP_PAUSE_SEC > 0:
            time.sleep(config.MOVE_STEP_PAUSE_SEC)

    if config.MOVE_SETTLE_SEC > 0:
        time.sleep(config.MOVE_SETTLE_SEC)
