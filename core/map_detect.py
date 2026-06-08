"""地图识别（40 级双地图）"""

from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np

import config
from core.dungeon_profile import DungeonProfile, MapVariant
from core.device import Device
from core.recognizer import MatchResult, Recognizer

logger = logging.getLogger(__name__)


def _match_at_scale(
    screen: np.ndarray,
    template: np.ndarray,
    scale: float,
    threshold: float,
) -> MatchResult:
    tw = max(1, int(template.shape[1] * scale))
    th = max(1, int(template.shape[0] * scale))
    sw, sh = screen.shape[1], screen.shape[0]
    if tw > sw or th > sh:
        return MatchResult(found=False, confidence=0.0)

    scaled_t = template if scale == 1.0 else cv2.resize(template, (tw, th))
    result = cv2.matchTemplate(screen, scaled_t, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    conf = float(max_val)
    center = (max_loc[0] + tw // 2, max_loc[1] + th // 2)
    return MatchResult(found=conf >= threshold, confidence=conf, center=center, scale=scale)


def match_map_template(
    screen: np.ndarray,
    template_path: str,
    threshold: float,
) -> MatchResult:
    """匹配地图模板；大图自动缩小匹配以提高容错"""
    template = cv2.imread(template_path)
    if template is None:
        return MatchResult(found=False, confidence=0.0)

    best = MatchResult(found=False, confidence=0.0)
    scales = list(config.TEMPLATE_SCALES.get("map", config.MATCH_SCALES))

    # 全屏级模板：额外用缩小版匹配（HUD 差异时更稳）
    if template.shape[1] > config.MAP_TEMPLATE_LARGE_WIDTH:
        scales = sorted(set(scales + [0.45, 0.50, 0.55, 0.60]))

    for scale in scales:
        result = _match_at_scale(screen, template, scale, threshold)
        if result.confidence > best.confidence:
            best = result

    best.found = best.confidence >= threshold
    return best


def detect_map_variant(
    device: Device,
    recognizer: Recognizer,
    profile: DungeonProfile,
) -> MapVariant | None:
    if not profile.map_variants:
        return None

    screen = device.screenshot_bgr()
    thresholds = [config.MAP_MATCH_THRESHOLD, config.MAP_MATCH_THRESHOLD_FALLBACK]

    for th in thresholds:
        best_variant: MapVariant | None = None
        best_conf = 0.0

        for variant in profile.map_variants:
            if not Path(variant.template).is_file():
                logger.warning("缺少地图模板: %s", variant.template)
                continue

            result = match_map_template(screen, variant.template, th)
            logger.info(
                "地图 %s 匹配 %.2f (阈值 %.2f)",
                variant.name,
                result.confidence,
                th,
            )

            if result.confidence > best_conf:
                best_conf = result.confidence
                if result.found:
                    best_variant = variant

        if best_variant:
            if th < config.MAP_MATCH_THRESHOLD:
                logger.warning(
                    "地图以较低阈值 %.2f 识别为 %s，建议缩小模板图仅保留特征区域",
                    th,
                    best_variant.name,
                )
            else:
                logger.info("识别地图: %s (置信度 %.2f)", best_variant.name, best_conf)
            return best_variant

    logger.error(
        "未识别到已知地图 (最高置信度 %.2f)。"
        "请检查 assets/maps/ 模板是否为「小区域特征图」而非整屏截图",
        best_conf,
    )
    return None
