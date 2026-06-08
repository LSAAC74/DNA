"""游戏内操作：走位、放 E、模板点击"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

import config
from core.device import Device
from core.movement import execute_move_path

if TYPE_CHECKING:
    from core.recognizer import Recognizer

logger = logging.getLogger(__name__)


def move_to_afk_position(
    device: Device,
    path: list[dict[str, Any]] | None = None,
) -> None:
    execute_move_path(device, path)


def press_skill_e(device: Device) -> None:
    if config.USE_KEYEVENT_FOR_E:
        logger.info("发送 E 键 (keyevent %s)", config.ANDROID_KEYCODE_E)
        device.key_e()
    else:
        x, y = config.SKILL_E_POSITION
        logger.info("点击 E 技能按钮 (%s, %s)", x, y)
        device.tap(x, y)
    time.sleep(0.5)


def wait_and_click(
    device: Device,
    recognizer: Recognizer,
    template_key: str,
    timeout: float | None = None,
    *,
    template_path: str | None = None,
) -> bool:
    timeout = timeout if timeout is not None else config.UI_WAIT_TIMEOUT
    path = template_path or config.TEMPLATES.get(template_key, "")
    if not path:
        logger.error("未配置模板路径: [%s]", template_key)
        return False
    result = recognizer.wait_for(
        device, template_key, timeout, template_path=path
    )

    if not result.found or not result.center:
        th = config.TEMPLATE_THRESHOLDS.get(template_key, config.MATCH_THRESHOLD)
        logger.error(
            "未找到 [%s] (%s)，最高置信度 %.2f (阈值 %.2f)",
            template_key,
            path,
            result.confidence,
            th,
        )
        return False

    x, y = result.center
    logger.info(
        "点击 [%s] 置信度 %.2f 缩放 %.2f @ (%s, %s)",
        template_key,
        result.confidence,
        result.scale,
        x,
        y,
    )
    device.tap(x, y)
    time.sleep(config.AFTER_CLICK_SEC)
    return True
