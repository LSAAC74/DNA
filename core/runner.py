"""脚本总控：菜单导航 + 黎瑟挂机循环"""

from __future__ import annotations

import logging
import threading
from threading import Event
from typing import Callable, Optional

import config
from core.device import Device
from flows.lyser_afk import LyserAfkFlow
from flows.menu_flow import MenuFlow

logger = logging.getLogger(__name__)


class ScriptRunner:
    def __init__(
        self,
        level: int = 65,
        go_index: int = 1,
        multiply_book: str | None = None,
        multiply_rounds: int = 0,
        on_status: Optional[Callable[[str], None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
    ):
        self.level = level
        self.go_index = go_index
        self.multiply_book = multiply_book
        self.multiply_rounds = multiply_rounds
        self.on_status = on_status
        self.on_finished = on_finished
        self._stop_event = Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _notify(self, msg: str) -> None:
        logger.info(msg)
        if self.on_status:
            self.on_status(msg)

    def start(self) -> bool:
        if self.is_running:
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop_event.set()
        self._notify("正在停止...")

    def _recover(self) -> bool:
        """重启模拟器 + 重新进入游戏"""
        self._notify("尝试恢复：重启模拟器...")
        device = Device()
        if not device.restart_emulator():
            self._notify("重启模拟器失败")
            return False

        self._notify("尝试恢复：进入游戏...")
        if not device.enter_game():
            self._notify("进入游戏失败")
            return False

        self._notify("恢复完成，准备重新导航")
        return True

    def _run(self) -> None:
        try:
            for attempt in range(1, config.MAX_RECOVERY_RETRIES + 2):  # 首次 + 重试
                if self._stop_event.is_set():
                    return

                if attempt > 1:
                    self._notify(
                        f"第 {attempt - 1}/{config.MAX_RECOVERY_RETRIES} 次恢复重试..."
                    )
                    if not self._recover():
                        self._notify("恢复失败，放弃重试")
                        break

                try:
                    self._notify("连接模拟器...")
                    menu = MenuFlow(
                        level=self.level,
                        go_index=self.go_index,
                        stop_event=self._stop_event,
                    )
                    if self._stop_event.is_set():
                        return

                    self._notify("执行菜单导航...")
                    if not menu.run():
                        if self._stop_event.is_set():
                            self._notify("已停止")
                        else:
                            self._notify("菜单导航失败")
                        # 导航失败也触发恢复
                        if attempt <= config.MAX_RECOVERY_RETRIES:
                            continue
                        break

                    if self._stop_event.is_set():
                        self._notify("已停止")
                        return

                    self._notify("开始战斗挂机循环...")
                    afk = LyserAfkFlow(
                        stop_event=self._stop_event,
                        dungeon_level=self.level,
                        go_index=self.go_index,
                        multiply_book=self.multiply_book,
                        multiply_rounds=self.multiply_rounds,
                    )
                    afk.run_loop()

                    if self._stop_event.is_set():
                        self._notify("脚本已停止")
                    else:
                        self._notify("脚本结束")
                    return  # 正常结束，不重试

                except Exception as e:
                    logger.exception("脚本异常")
                    self._notify(f"错误: {e}")
                    if attempt > config.MAX_RECOVERY_RETRIES:
                        self._notify("已达最大重试次数，停止")
                        break
                    self._notify(
                        f"将在 {attempt}/{config.MAX_RECOVERY_RETRIES} 次后尝试恢复..."
                    )
                    continue

            self._notify("脚本异常退出")
        finally:
            if self.on_finished:
                self.on_finished()
