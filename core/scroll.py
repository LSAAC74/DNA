"""在屏幕中滚动查找模板"""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional

import config
from core.device import Device
from core.recognizer import MatchResult, Recognizer

logger = logging.getLogger(__name__)


def scroll_up(
    device: Device,
    x: int,
    y: int,
    distance: int | None = None,
    duration_ms: int | None = None,
    pause_sec: float | None = None,
) -> None:
    dist = distance if distance is not None else config.SCROLL_DISTANCE
    dur = duration_ms if duration_ms is not None else config.SCROLL_DURATION_MS
    pause = pause_sec if pause_sec is not None else config.SCROLL_PAUSE_SEC
    device.swipe(x, y, x, y - dist, dur)
    time.sleep(pause)


def scroll_down(
    device: Device,
    x: int,
    y: int,
    distance: int | None = None,
    duration_ms: int | None = None,
    pause_sec: float | None = None,
) -> None:
    dist = distance if distance is not None else config.SCROLL_DISTANCE
    dur = duration_ms if duration_ms is not None else config.SCROLL_DURATION_MS
    pause = pause_sec if pause_sec is not None else config.SCROLL_PAUSE_SEC
    device.swipe(x, y, x, y + dist, dur)
    time.sleep(pause)


def scroll_go_list(device: Device) -> None:
    """前往列表专用：拖得更久，滚完一屏后第一项对应序号 5"""
    sx, sy = config.GO_SCROLL_POS
    scroll_up(
        device,
        sx,
        sy,
        distance=config.GO_SCROLL_DISTANCE,
        duration_ms=config.GO_SCROLL_DURATION_MS,
        pause_sec=config.GO_SCROLL_PAUSE_SEC,
    )


def find_with_scroll(
    device: Device,
    recognizer: Recognizer,
    template_path: str,
    scroll_x: int,
    scroll_y: int,
    *,
    template_key: str = "",
    threshold: float | None = None,
    max_scrolls: int | None = None,
    matcher: Optional[Callable] = None,
) -> MatchResult:
    """当前屏找不到则向上滚动继续找"""
    max_scrolls = max_scrolls if max_scrolls is not None else config.MAX_LEVEL_SCROLLS
    best = MatchResult(found=False, confidence=0.0)

    for i in range(max_scrolls + 1):
        screen = device.screenshot_bgr()
        if matcher:
            result = matcher(screen)
        else:
            result = recognizer.match(
                screen, template_path, threshold=threshold, template_key=template_key
            )

        if result.confidence > best.confidence:
            best = result

        if result.found:
            logger.info("找到模板 %s (置信度 %.2f, 第 %d 屏)", template_path, result.confidence, i + 1)
            return result

        if i < max_scrolls:
            logger.info("未找到 %s (最高 %.2f)，向上滚动 (%d/%d)", template_path, result.confidence, i + 1, max_scrolls)
            scroll_up(device, scroll_x, scroll_y)

    best.found = False
    return best
