"""OpenCV 模板匹配（支持多尺度）"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

import config


@dataclass
class MatchResult:
    found: bool
    confidence: float
    center: Optional[Tuple[int, int]] = None
    scale: float = 1.0


class Recognizer:
    def __init__(self, threshold: float = config.MATCH_THRESHOLD):
        self.threshold = threshold
        self._cache: dict[str, np.ndarray] = {}

    def _load_template(self, path: str) -> Optional[np.ndarray]:
        if path in self._cache:
            return self._cache[path]
        p = Path(path)
        if not p.is_file():
            return None
        img = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if img is not None:
            self._cache[path] = img
        return img

    def _threshold_for(self, template_key: str) -> float:
        return config.TEMPLATE_THRESHOLDS.get(template_key, self.threshold)

    def _scales_for(self, template_key: str) -> list[float]:
        return config.TEMPLATE_SCALES.get(template_key, config.MATCH_SCALES)

    def is_template_usable(self, template_key: str) -> bool:
        path = config.TEMPLATES.get(template_key, "")
        template = self._load_template(path)
        if template is None:
            return False
        h, w = template.shape[:2]
        return w >= config.MIN_TEMPLATE_SIZE and h >= config.MIN_TEMPLATE_SIZE

    def _prepare_template(self, template: np.ndarray, template_key: str) -> np.ndarray:
        ratio = config.TEMPLATE_CROP_LEFT_RATIO.get(template_key)
        if ratio is None or ratio >= 1.0:
            return template
        cut = max(1, int(template.shape[1] * ratio))
        return template[:, :cut]

    def _click_point(
        self,
        top_left: Tuple[int, int],
        width: int,
        height: int,
        template_key: str,
    ) -> Tuple[int, int]:
        rx, ry = config.TEMPLATE_CLICK_POINT_RATIO.get(template_key, (0.5, 0.5))
        x = top_left[0] + int(width * rx)
        y = top_left[1] + int(height * ry)
        return x, y

    def match(
        self,
        screen: np.ndarray,
        template_path: str,
        threshold: Optional[float] = None,
        template_key: str = "",
    ) -> MatchResult:
        template = self._load_template(template_path)
        if template is None:
            return MatchResult(found=False, confidence=0.0)

        template = self._prepare_template(template, template_key)

        th = threshold if threshold is not None else self._threshold_for(template_key)
        scales = self._scales_for(template_key) if template_key else config.MATCH_SCALES

        best = MatchResult(found=False, confidence=0.0)
        sh, sw = screen.shape[:2]

        for scale in scales:
            tw = max(1, int(template.shape[1] * scale))
            th_ = max(1, int(template.shape[0] * scale))
            if tw > sw or th_ > sh:
                continue

            scaled = template if scale == 1.0 else cv2.resize(template, (tw, th_))
            result = cv2.matchTemplate(screen, scaled, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > best.confidence:
                center = self._click_point(max_loc, tw, th_, template_key)
                best = MatchResult(
                    found=False,
                    confidence=float(max_val),
                    center=center,
                    scale=scale,
                )

        best.found = best.confidence >= th
        return best

    def match_all(
        self,
        screen: np.ndarray,
        template_path: str,
        threshold: Optional[float] = None,
        template_key: str = "",
        min_distance: int = 40,
    ) -> list[MatchResult]:
        """找出屏幕上所有匹配项（按置信度贪心 + 距离去重）"""
        template = self._load_template(template_path)
        if template is None:
            return []

        template = self._prepare_template(template, template_key)
        th = threshold if threshold is not None else self._threshold_for(template_key)
        scales = self._scales_for(template_key) if template_key else config.MATCH_SCALES

        candidates: list[MatchResult] = []
        sh, sw = screen.shape[:2]

        for scale in scales:
            tw = max(1, int(template.shape[1] * scale))
            th_ = max(1, int(template.shape[0] * scale))
            if tw > sw or th_ > sh:
                continue

            scaled = template if scale == 1.0 else cv2.resize(template, (tw, th_))
            result_map = cv2.matchTemplate(screen, scaled, cv2.TM_CCOEFF_NORMED)
            ys, xs = np.where(result_map >= th)
            for y, x in zip(ys, xs):
                conf = float(result_map[y, x])
                center = (x + tw // 2, y + th_ // 2)
                candidates.append(
                    MatchResult(found=True, confidence=conf, center=center, scale=scale)
                )

        candidates.sort(key=lambda r: r.confidence, reverse=True)
        picked: list[MatchResult] = []
        for c in candidates:
            if c.center is None:
                continue
            if all(
                abs(c.center[0] - p.center[0]) ** 2 + abs(c.center[1] - p.center[1]) ** 2
                >= min_distance**2
                for p in picked
                if p.center
            ):
                picked.append(c)

        picked.sort(key=lambda r: r.center[1] if r.center else 0)
        return picked

    def wait_for(
        self,
        device,
        template_key: str,
        timeout: float,
        interval: float = config.POLL_INTERVAL,
        template_path: str | None = None,
    ) -> MatchResult:
        import time

        path = template_path or config.TEMPLATES.get(template_key, "")
        th = self._threshold_for(template_key)
        deadline = time.time() + timeout
        best = MatchResult(found=False, confidence=0.0)

        while time.time() < deadline:
            screen = device.screenshot_bgr()
            result = self.match(screen, path, threshold=th, template_key=template_key)
            if result.found:
                return result
            if result.confidence > best.confidence:
                best = result
            time.sleep(interval)

        best.found = False
        return best
