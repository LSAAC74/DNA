"""《二重螺旋》黎瑟挂机脚本入口

流程（循环）：
  首次: start → begin → 走位按E → 等结束 → restart
  之后: begin → 走位按E → 等结束 → restart → ...
"""

from __future__ import annotations

import argparse
import logging
import sys

from flows.lyser_afk import LyserAfkFlow


def main() -> int:
    parser = argparse.ArgumentParser(description="二重螺旋 - 黎瑟挂机")
    parser.add_argument(
        "--once",
        action="store_true",
        help="只跑一轮（默认不含 start，加 --with-start 则含首次 start）",
    )
    parser.add_argument(
        "--with-start",
        action="store_true",
        help="与 --once 合用：本轮包含点击 start",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="调试日志")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    flow = LyserAfkFlow()
    if args.once:
        ok = flow.run_cycle(need_start=args.with_start)
        return 0 if ok else 1

    flow.run_loop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
