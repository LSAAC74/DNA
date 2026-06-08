"""手动输入走位路径（无需 keyboard 库）

示例输入：
  w 3
  d 1.5
  w 2
  done
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "move_path.py"


def main() -> None:
    path: list[dict[str, object]] = []
    print("输入 方向 秒数，如: w 2.5  或  wd 1.0")
    print("输入 done 结束\n")

    while True:
        line = input("> ").strip().lower()
        if line in ("done", "q", ""):
            break
        parts = line.split()
        if len(parts) != 2:
            print("  格式: w 2.5")
            continue
        key, sec = parts[0], float(parts[1])
        if not all(c in "wasd" for c in key):
            print("  方向只能是 w/a/s/d 组合")
            continue
        path.append({"key": key, "sec": sec})
        print(f"  已添加: {key} {sec}s")

    content = (
        '"""手动录入的走位路径 — 复制 MOVE_PATH 到 config.py"""\n\n'
        f"MOVE_PATH = {path!r}\n"
    )
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"\n已保存到 {OUTPUT}")
    print(path)


if __name__ == "__main__":
    main()
