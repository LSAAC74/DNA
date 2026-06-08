"""测试当前屏幕与各模板的匹配分数，并生成标注图"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import cv2

import config
from core.device import Device
from core.dungeon_profile import get_dungeon_profile
from core.map_detect import match_map_template
from core.recognizer import Recognizer


def main() -> None:
    device = Device()
    device.connect()
    screen = device.screenshot_bgr()
    out_dir = ROOT / "assets"
    cv2.imwrite(str(out_dir / "_debug_screen.png"), screen)
    print(f"屏幕尺寸: {screen.shape[1]}x{screen.shape[0]}")

    recognizer = Recognizer()
    overlay = screen.copy()

    for key, path in config.TEMPLATES.items():
        usable = recognizer.is_template_usable(key)
        result = recognizer.match(screen, path, template_key=key)
        th = config.TEMPLATE_THRESHOLDS.get(key, config.MATCH_THRESHOLD)
        status = "OK" if result.found else "FAIL"
        usable_tag = "" if usable else " [模板过小/无效]"
        print(
            f"{status} {key:8} max={result.confidence:.3f} "
            f"scale={result.scale:.2f} threshold={th:.2f}{usable_tag}"
        )
        if result.center and result.confidence > 0.3:
            template = cv2.imread(path)
            if template is not None:
                tw = max(1, int(template.shape[1] * result.scale))
                th_ = max(1, int(template.shape[0] * result.scale))
                x = result.center[0] - tw // 2
                y = result.center[1] - th_ // 2
                color = (0, 255, 0) if result.found else (0, 0, 255)
                cv2.rectangle(overlay, (x, y), (x + tw, y + th_), color, 2)
                cv2.putText(
                    overlay,
                    f"{key} {result.confidence:.2f}",
                    (x, max(0, y - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                )

    out_path = out_dir / "_debug_all_matches.png"
    cv2.imwrite(str(out_path), overlay)
    print(f"标注图已保存: {out_path}")

    profile = get_dungeon_profile(40)
    if profile.map_variants:
        print("\n--- 40 级地图 ---")
        for v in profile.map_variants:
            r = match_map_template(screen, v.template, config.MAP_MATCH_THRESHOLD)
            fb = match_map_template(screen, v.template, config.MAP_MATCH_THRESHOLD_FALLBACK)
            print(
                f"{'OK' if r.found else 'FAIL'} {v.name:6} "
                f"max={r.confidence:.3f} fallback={fb.confidence:.3f} "
                f"({v.template})"
            )


if __name__ == "__main__":
    main()
