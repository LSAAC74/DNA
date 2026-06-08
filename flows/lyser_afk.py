"""黎瑟挂机流程

循环逻辑：
  首次: start → (倍率书?) → begin → (识别地图) → 走位/按E → 等 restart → 点 restart
  之后: (倍率书?) → begin → ... → 重复

  65/30 级: 走位 → 按 E
  40 级:   按 E → 走位（进图先 E，地图识别）
  75 级:   按前往序号选副本，先 E 或先走位因本而异
"""

from __future__ import annotations

import logging
import time
from threading import Event
from typing import Any, Optional

import config
from core.actions import move_to_afk_position, press_skill_e, wait_and_click
from core.device import Device
from core.dungeon_profile import get_dungeon_profile, resolve_afk_config
from core.map_detect import detect_map_variant
from core.recognizer import Recognizer

logger = logging.getLogger(__name__)


class LyserAfkFlow:
    def __init__(
        self,
        device: Device | None = None,
        stop_event: Optional[Event] = None,
        *,
        dungeon_level: int = 65,
        go_index: int = 1,
        multiply_book: str | None = None,
        multiply_rounds: int = 0,
    ):
        self.device = device or Device()
        self.recognizer = Recognizer()
        self.stop_event = stop_event or Event()
        self.go_index = go_index
        self.multiply_book = multiply_book
        self.multiply_rounds = multiply_rounds
        self.profile = get_dungeon_profile(dungeon_level)
        self._afk_config = resolve_afk_config(self.profile, go_index)

    def _stopped(self) -> bool:
        return self.stop_event.is_set()

    def wait_fighting(self, *, repeat_round: bool = False) -> bool:
        if not self.recognizer.is_template_usable("fighting"):
            wait_sec = (
                config.WAIT_AFTER_BEGIN_SEC
                if not repeat_round
                else config.MIN_WAIT_AFTER_BEGIN_REPEAT_SEC + config.BEFORE_MOVE_REPEAT_SEC
            )
            logger.warning(
                "fighting.png 过小或缺失，改用固定等待 %.1fs",
                wait_sec,
            )
            time.sleep(wait_sec)
            return True

        label = "重复轮" if repeat_round else "首轮"
        min_wait = (
            config.MIN_WAIT_AFTER_BEGIN_REPEAT_SEC
            if repeat_round
            else config.MIN_WAIT_AFTER_BEGIN_SEC
        )
        logger.info(
            "等待进入战斗 (fighting) [%s] | 副本 %d 级...",
            label,
            self.profile.level,
        )
        time.sleep(min_wait)

        deadline = time.time() + config.BATTLE_START_TIMEOUT
        best = 0.0
        begin_gone_since: float | None = None
        fighting_stable_since: float | None = None
        allow_begin_fallback = config.USE_BEGIN_GONE_FALLBACK and not repeat_round

        while time.time() < deadline:
            if self._stopped():
                return False

            screen = self.device.screenshot_bgr()
            result = self.recognizer.match(
                screen,
                config.TEMPLATES["fighting"],
                template_key="fighting",
            )
            best = max(best, result.confidence)

            if result.found:
                if fighting_stable_since is None:
                    fighting_stable_since = time.time()
                elif time.time() - fighting_stable_since >= config.FIGHTING_STABLE_SEC:
                    settle = (
                        config.BEFORE_MOVE_REPEAT_SEC
                        if repeat_round
                        else config.BEFORE_MOVE_SEC
                    )
                    logger.info(
                        "已进入战斗 (置信度 %.2f, 稳定 %.1fs) [%s]，准备执行 %s",
                        result.confidence,
                        config.FIGHTING_STABLE_SEC,
                        label,
                        self._afk_flow_label(),
                    )
                    time.sleep(settle)
                    return True
            else:
                fighting_stable_since = None

            if allow_begin_fallback:
                begin = self.recognizer.match(
                    screen,
                    config.TEMPLATES["begin"],
                    template_key="begin",
                )
                if not begin.found:
                    if begin_gone_since is None:
                        begin_gone_since = time.time()
                    elif time.time() - begin_gone_since >= config.BEGIN_GONE_CONFIRM_SEC:
                        settle = config.BEFORE_MOVE_SEC
                        logger.info(
                            "「开始挑战」已消失，判定进入战斗 (fighting 最高 %.2f)，等待 %.1fs",
                            best,
                            settle,
                        )
                        time.sleep(settle)
                        return True
                else:
                    begin_gone_since = None

            time.sleep(config.POLL_INTERVAL)

        logger.error(
            "未进入战斗，请检查 assets/fighting.png (最高置信度 %.2f)",
            best,
        )
        return False

    def _afk_flow_label(self) -> str:
        if self._afk_config is None:
            return "未知"
        return (
            "先E后走位"
            if self._afk_config.skill_first
            else "先走位后E"
        )

    def _resolve_move_path(self) -> list[dict[str, Any]] | None:
        if self.profile.uses_go_variant:
            if self._afk_config is None:
                return None
            return list(self._afk_config.move_path)

        if not self.profile.uses_map_detect:
            return list(self.profile.move_path)

        variant = detect_map_variant(self.device, self.recognizer, self.profile)
        if variant is None:
            return None
        return list(variant.move_path)

    def _resolve_afk_runtime(self) -> tuple[list[dict[str, Any]], bool, float] | None:
        path = self._resolve_move_path()
        if path is None:
            return None

        if self.profile.uses_go_variant:
            if self._afk_config is None:
                return None
            cfg = self._afk_config
            return path, cfg.skill_first, cfg.after_skill_wait_sec

        if self.profile.uses_map_detect:
            return path, self.profile.skill_first, self.profile.after_skill_wait_sec

        if self._afk_config is None:
            return None
        cfg = self._afk_config
        return path, cfg.skill_first, cfg.after_skill_wait_sec

    def setup_afk(self) -> None:
        if self.profile.uses_go_variant:
            variant = self.profile.get_go_variant(self.go_index)
            if variant is None:
                raise RuntimeError(
                    f"75 级前往序号 {self.go_index} 无效（共 {len(self.profile.go_variants)} 个）"
                )
            if variant.placeholder:
                raise RuntimeError(
                    f"75 级第 {self.go_index} 个副本（{variant.name}）尚未配置，请稍后再试"
                )

        resolved = self._resolve_afk_runtime()
        if resolved is None:
            raise RuntimeError(f"无法确定 {self.profile.level} 级副本挂机参数")

        path, skill_first, after_skill_wait_sec = resolved
        variant_label = (
            self._afk_config.variant_name
            if self._afk_config and self._afk_config.variant_name
            else f"{self.profile.level}级"
        )

        if skill_first:
            logger.info("%s: 先进图放 E，再走位", variant_label)
            press_skill_e(self.device)
            if after_skill_wait_sec > 0:
                logger.info(
                    "等待技能生效 %.1fs...",
                    after_skill_wait_sec,
                )
                time.sleep(after_skill_wait_sec)
            if path:
                move_to_afk_position(self.device, path)
            else:
                logger.info("本图无需走位，原地挂机")
        else:
            if path:
                move_to_afk_position(self.device, path)
            press_skill_e(self.device)

        logger.info("挂机 setup 完成，等待战斗结束...")

    def wait_loading_complete(self, repeat_round: bool = False) -> bool:
        """等待 loading 界面完全消失，确认副本已经加载完成"""
        if not self.recognizer.is_template_usable("loading"):
            fallback = 2.0 if not repeat_round else 1.0
            logger.warning(
                "loading.png 不可用，固定等待 %.1fs 作为加载缓冲",
                fallback,
            )
            time.sleep(fallback)
            return True

        logger.info("等待加载完成 (loading 消失)...")
        deadline = time.time() + 30.0
        while time.time() < deadline:
            if self._stopped():
                return False
            screen = self.device.screenshot_bgr()
            result = self.recognizer.match(
                screen,
                config.TEMPLATES["loading"],
                template_key="loading",
            )
            if not result.found:
                logger.info("加载完成 (loading 已消失)")
                # 额外给游戏一点点稳定时间
                time.sleep(0.8)
                return True
            time.sleep(config.POLL_INTERVAL)

        logger.warning("等待加载超时，继续流程")
        return True

    def wait_battle_end(self) -> bool:
        logger.info("等待战斗结束 (restart 出现，最长 %ds)...", config.BATTLE_END_TIMEOUT)
        result = self.recognizer.wait_for(
            self.device, "restart", config.BATTLE_END_TIMEOUT
        )
        if not result.found:
            logger.error(
                "战斗未正常结束，未检测到 restart (最高置信度 %.2f)",
                result.confidence,
            )
            return False
        logger.info("战斗结束 (restart 置信度 %.2f)", result.confidence)
        return True

    def _should_use_multiply(self, round_no: int) -> bool:
        return (
            self.multiply_book is not None
            and self.multiply_rounds > 0
            and round_no <= self.multiply_rounds
        )

    def _click_multiply_and_begin(self, round_no: int) -> bool:
        if self._should_use_multiply(round_no):
            book_path = config.MULTIPLY_BOOKS.get(self.multiply_book)
            if not book_path:
                logger.error("未知倍率书: %s", self.multiply_book)
                return False
            label = config.MULTIPLY_BOOK_LABELS.get(self.multiply_book, self.multiply_book)
            logger.info(
                "选择倍率书 [%s]（第 %d/%d 轮）",
                label,
                round_no,
                self.multiply_rounds,
            )
            if not wait_and_click(
                self.device,
                self.recognizer,
                "multiply",
                template_path=book_path,
            ):
                return False
        elif self.multiply_book and round_no == self.multiply_rounds + 1:
            logger.info("倍率书已用满 %d 轮，后续不再选择", self.multiply_rounds)
        return wait_and_click(self.device, self.recognizer, "begin")

    def run_cycle(self, *, need_start: bool, round_no: int = 1) -> bool:
        if self._stopped():
            return False

        if need_start:
            if not wait_and_click(self.device, self.recognizer, "start"):
                return False

        if not self._click_multiply_and_begin(round_no):
            return False

        if not self.wait_fighting(repeat_round=not need_start):
            return False

        if not self.wait_loading_complete(repeat_round=not need_start):
            return False

        try:
            self.setup_afk()
        except RuntimeError as e:
            logger.error("%s", e)
            return False

        if not self.wait_battle_end():
            return False

        if not wait_and_click(self.device, self.recognizer, "restart"):
            return False

        return True

    def run_loop(self) -> None:
        logger.info(
            "=== 黎瑟挂机 | %s | %d 级副本 | 前往 #%d | 倍率书 %s | %dx%d ===",
            config.MAIN_CHARACTER,
            self.profile.level,
            self.go_index,
            (
                f"{config.MULTIPLY_BOOK_LABELS.get(self.multiply_book, self.multiply_book)}×{self.multiply_rounds}轮"
                if self.multiply_book
                else "无"
            ),
            config.SCREEN_WIDTH,
            config.SCREEN_HEIGHT,
        )
        self.device.connect()

        first = True
        round_no = 0
        while not self._stopped():
            round_no += 1
            logger.info("--- 第 %d 轮 ---", round_no)
            if not self.run_cycle(need_start=first, round_no=round_no):
                break
            first = False
            time.sleep(0.5)

        if self._stopped():
            logger.info("挂机循环已停止")
        else:
            logger.info("脚本结束")
