"""夜航手册菜单导航：历练 → 委托 → 夜航手册 → 选等级 → 选前往"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from threading import Event
from typing import Optional

import config
from core.actions import wait_and_click
from core.device import Device
from core.dungeon_profile import DungeonProfile, get_dungeon_profile
from core.recognizer import MatchResult, Recognizer
from core.scroll import find_with_scroll, scroll_down, scroll_go_list, scroll_up

logger = logging.getLogger(__name__)


def collect_go_buttons(
    recognizer: Recognizer,
    screen,
    go_path: str,
) -> list[MatchResult]:
    """识别「前往」按钮，排除左侧铜币等误匹配"""
    raw = recognizer.match_all(
        screen, go_path, template_key="go", min_distance=40
    )

    xmin = config.GO_MATCH_X_MIN
    filtered = [b for b in raw if b.center and b.center[0] >= xmin]

    if len(filtered) < len(raw):
        logger.debug(
            "前往过滤: 全屏 %d 个 → 右侧 %d 个 (X>=%d)",
            len(raw),
            len(filtered),
            xmin,
        )

    if not filtered:
        return []

    filtered.sort(key=lambda b: b.center[1] if b.center else 0)
    rows: list[MatchResult] = []
    y_tol = config.GO_ROW_Y_TOLERANCE
    current: list[MatchResult] = []

    for btn in filtered:
        if not btn.center:
            continue
        if not current or abs(btn.center[1] - current[0].center[1]) <= y_tol:
            current.append(btn)
        else:
            rows.append(max(current, key=lambda b: b.center[0]))
            current = [btn]

    if current:
        rows.append(max(current, key=lambda b: b.center[0]))

    for i, btn in enumerate(rows, 1):
        if btn.center:
            logger.debug(
                "前往行 %d: (%.0f, %.0f) 置信度 %.2f",
                i,
                btn.center[0],
                btn.center[1],
                btn.confidence,
            )

    return rows


def _go_first_visible(scroll_count: int, go_per_page: int, level: int = 0) -> int:
    """滚动后当前屏第一个可见「前往」的序号（1-based）。
    50 级特殊：滑动一次后首项为 3（不是通用的 5）。"""
    if level == 50 and scroll_count > 0:
        return 3
    return 1 + scroll_count * (go_per_page - 1)


def go_button_coord(go_index: int, go_per_page: int, level: int = 0) -> tuple[int, int]:
    """根据序号计算「前往」固定坐标（1-based）"""
    scroll_count = go_scroll_pages(go_index, go_per_page, level)
    first_visible = _go_first_visible(scroll_count, go_per_page, level)
    row = go_index - first_visible
    y = config.GO_FIRST_Y + row * config.GO_ROW_STEP_Y
    return config.GO_BUTTON_X, y


def go_scroll_pages(go_index: int, go_per_page: int, level: int = 0) -> int:
    """序号超过每页数量时需滚动的次数"""
    if go_index <= go_per_page:
        return 0
    # 50 级特殊：7 个副本，滑一次后首项为 3，故 6/7 都只需滑 1 次
    if level == 50:
        return 1
    return (go_index - 2) // (go_per_page - 1)


def level_template_path(level: int) -> str:
    for base in (config.LEVEL_ASSETS_DIR, config.LEVEL_FALLBACK_DIR):
        path = Path(base) / f"{level}.png"
        if path.is_file():
            return str(path)
    return str(Path(config.LEVEL_ASSETS_DIR) / f"{level}.png")


class MenuFlow:
    def __init__(
        self,
        device: Device | None = None,
        *,
        level: int = 65,
        go_index: int = 1,
        stop_event: Optional[Event] = None,
    ):
        self.device = device or Device()
        self.recognizer = Recognizer()
        self.level = level
        self.go_index = go_index
        self.profile = get_dungeon_profile(level)
        self.stop_event = stop_event or Event()

    def _stopped(self) -> bool:
        return self.stop_event.is_set()

    def _tap(self, x: int, y: int, label: str = "") -> None:
        if self._stopped():
            return
        logger.info("点击 %s (%s, %s)", label or "坐标", x, y)
        self.device.tap(x, y)
        time.sleep(config.AFTER_CLICK_SEC)

    def open_night_manual(self) -> bool:
        if self._stopped():
            return False

        x, y = config.MENU_TOP_LEFT
        self._tap(x, y, "左上角菜单")

        if not wait_and_click(self.device, self.recognizer, "tempering"):
            return False
        if self._stopped():
            return False

        cx, cy = config.MENU_COMMISSION
        self._tap(cx, cy, "委托")

        if not wait_and_click(self.device, self.recognizer, "book"):
            return False

        time.sleep(0.8)
        return not self._stopped()

    def select_level(self) -> bool:
        if self._stopped():
            return False

        path = level_template_path(self.level)
        if not Path(path).is_file():
            logger.error("缺少等级模板: %s", path)
            return False

        logger.info("选择等级 %d (%s)", self.level, path)
        sx, sy = config.LEVEL_SCROLL_POS
        if self.level in config.LEVELS_SCROLL_DOWN_FIRST:
            logger.info(
                "等级 %d 与 50 级易混淆，先向下滑动列表 (%s, %s) 再检索",
                self.level,
                sx,
                sy,
            )
            scroll_down(self.device, sx, sy)
        result = find_with_scroll(
            self.device,
            self.recognizer,
            path,
            sx,
            sy,
            threshold=0.60,
            max_scrolls=config.MAX_LEVEL_SCROLLS,
        )

        if not result.found or not result.center:
            logger.error("未找到等级 %d (最高置信度 %.2f)", self.level, result.confidence)
            return False

        self._tap(*result.center, f"等级 {self.level}")
        time.sleep(0.5)
        return not self._stopped()

    def select_go(self) -> bool:
        if self._stopped():
            return False

        if self.go_index < 1:
            logger.error("前往序号须 >= 1")
            return False

        logger.info(
            "选择第 %d 个「前往」(副本 %d 级，每页 %d 个)",
            self.go_index,
            self.profile.level,
            self.profile.go_per_page,
        )

        if config.USE_FIXED_GO_COORDS:
            per_page = self.profile.go_per_page
            level = self.profile.level
            pages = go_scroll_pages(self.go_index, per_page, level)
            for i in range(pages):
                if self._stopped():
                    return False
                logger.info(
                    "前往列表向上滚动 (%d/%d)，滚完首项应对齐第 %d 条",
                    i + 1,
                    pages,
                    _go_first_visible(i + 1, per_page, level),
                )
                scroll_go_list(self.device)

            x, y = go_button_coord(self.go_index, per_page, level)
            first = _go_first_visible(pages, per_page, level)
            row = self.go_index - first + 1
            logger.info(
                "点击前往 #%d @ (%s,%s)（当前屏第 %d 行）",
                self.go_index,
                x,
                y,
                row,
            )
            self._tap(x, y, f"前往 #{self.go_index}")
            time.sleep(0.8)
            return not self._stopped()

        go_path = config.TEMPLATES["go"]
        sx, sy = config.GO_SCROLL_POS
        best_conf = 0.0

        for scroll_i in range(config.MAX_GO_SCROLLS + 1):
            if self._stopped():
                return False

            screen = self.device.screenshot_bgr()
            buttons = collect_go_buttons(self.recognizer, screen, go_path)

            if buttons:
                best_conf = max(best_conf, max(b.confidence for b in buttons))

            if len(buttons) >= self.go_index:
                target = buttons[self.go_index - 1]
                if target.center:
                    self._tap(*target.center, f"前往 #{self.go_index}")
                    time.sleep(0.8)
                    return True

            if self.go_index <= self.profile.go_per_page and scroll_i == 0 and not buttons:
                time.sleep(0.5)
                screen = self.device.screenshot_bgr()
                buttons = collect_go_buttons(self.recognizer, screen, go_path)
                if len(buttons) >= self.go_index and buttons[self.go_index - 1].center:
                    c = buttons[self.go_index - 1].center
                    self._tap(*c, f"前往 #{self.go_index}")
                    time.sleep(0.8)
                    return True

            if scroll_i < config.MAX_GO_SCROLLS:
                logger.info(
                    "当前仅找到 %d 个前往，需要第 %d 个，向上滚动 (%d/%d)",
                    len(buttons),
                    self.go_index,
                    scroll_i + 1,
                    config.MAX_GO_SCROLLS,
                )
                scroll_up(self.device, sx, sy)

        logger.error(
            "未找到第 %d 个前往 (最高置信度 %.2f)",
            self.go_index,
            best_conf,
        )
        return False

    def run(self) -> bool:
        logger.info("=== 夜航手册导航 | 等级 %d | 前往 #%d ===", self.level, self.go_index)
        self.device.connect()

        if not self.open_night_manual():
            return False
        if not self.select_level():
            return False
        if not self.select_go():
            return False

        logger.info("菜单导航完成，进入战斗挂机流程")
        return True
