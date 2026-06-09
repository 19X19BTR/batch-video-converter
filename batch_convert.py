#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量选片转码器
作者：阿瑞
功能：交互式选取视频文件，批量转换为目标格式
依赖：ffmpeg（需在 PATH 中）
"""
import os
import sys
import json
import shutil
import subprocess
import signal
from pathlib import Path
from typing import List, Dict, Optional
import threading

# ---------- 常量 ----------
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "config.json"


# ---------- 打包兼容：自动把 ffmpeg 所在目录加入 PATH ----------
def _setup_bundled_ffmpeg():
    """PyInstaller 打包后，ffmpeg 在 _MEIPASS (即 _internal/) 目录下"""
    if getattr(sys, 'frozen', False):
        meipass = Path(sys._MEIPASS)
        # 优先找 _internal/，其次找 exe 同级目录
        for candidate in [meipass, meipass.parent]:
            if (candidate / 'ffmpeg.exe').exists():
                bin_str = str(candidate)
                if bin_str not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = bin_str + os.pathsep + os.environ.get("PATH", "")
                return

_setup_bundled_ffmpeg()
DEFAULT_CONFIG = {
    "input_dir": "./input",
    "output_dir": "./output",
    "page_size": 10,
    "presets": {
        "1": {"name": "mp4(H.264)", "ext": "mp4", "vcodec": "libx264", "acodec": "aac"},
        "2": {"name": "mp4(H.265)", "ext": "mp4", "vcodec": "libx265", "acodec": "aac"},
        "3": {"name": "mkv(H.264)", "ext": "mkv", "vcodec": "libx264", "acodec": "copy"},
        "4": {"name": "avi(Xvid)",  "ext": "avi", "vcodec": "libxvid", "acodec": "mp3"},
        "5": {"name": "mov(H.264)", "ext": "mov", "vcodec": "libx264", "acodec": "aac"},
        "6": {"name": "gif",        "ext": "gif", "vcodec": "gif",     "acodec": "none"},
    },
}

# 支持的视频扩展名
VIDEO_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".m4v", ".mpg", ".mpeg", ".3gp", ".ts", ".vob", ".mts", ".m2ts",
}

# ---------- 全局退出标志 ----------
STOP = threading.Event()


def _signal_handler(signum, frame):
    STOP.set()


signal.signal(signal.SIGINT, _signal_handler)


# ---------- 配置加载 ----------
def load_config() -> dict:
    """加载配置文件，不存在则使用默认值并创建"""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            config.update(user_cfg)
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠ 配置文件读取失败，使用默认配置: {e}")
    else:
        # 首次运行，生成默认配置
        save_config(config)
        print(f"已生成默认配置文件: {CONFIG_FILE}")
    return config


def save_config(config: dict):
    """保存配置到文件"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ---------- 选片语法解析 ----------
def parse_choice(raw: str, max_n: int) -> List[int]:
    """
    解析选片语法，支持：
      - 单号：3
      - 逗号分隔：1,3,5
      - 范围：3-7
      - 前缀区间：-5（即 1-5）
      - 后缀区间：8-（即 8 到最后）
      - 混合：1,3-5,8-
    返回 0-based 索引列表（已排序去重）
    """
    raw = raw.strip()
    if not raw:
        return []
    idx_set: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            # 前缀区间 -5 → 1~5
            if part.startswith("-") and part.count("-") == 1:
                end = int(part[1:])
                if end < 1 or end > max_n:
                    raise ValueError(f"前缀区间 {part} 超出范围 (1-{max_n})")
                idx_set.update(range(0, end))
                continue
            # 后缀区间 8- → 8~最后
            if part.endswith("-") and part.count("-") == 1:
                start = int(part[:-1])
                if start < 1 or start > max_n:
                    raise ValueError(f"后缀区间 {part} 超出范围 (1-{max_n})")
                idx_set.update(range(start - 1, max_n))
                continue
            # 普通范围 3-7
            start_str, end_str = part.split("-", 1)
            start, end = int(start_str), int(end_str)
            if start > end or start < 1 or end > max_n:
                raise ValueError(f"区间 {part} 超出范围 (1-{max_n})")
            idx_set.update(range(start - 1, end))
        else:
            idx = int(part)
            if idx < 1 or idx > max_n:
                raise ValueError(f"序号 {part} 超出范围 (1-{max_n})")
            idx_set.add(idx - 1)
    return sorted(idx_set)


# ---------- 分页浏览文件 ----------
def paginate(files: List[Path], page_size: int) -> List[Path]:
    """分页展示文件列表，返回用户选中的文件"""
    total = len(files)
    total_pages = (total + page_size - 1) // page_size
    page = 0

    while True:
        start = page * page_size
        end = min(start + page_size, total)
        print(f"\n{'='*50}")
        print(f"  第 {page + 1} 页 / 共 {total_pages} 页    (共 {total} 个文件)")
        print(f"{'='*50}")
        for i in range(start, end):
            size_mb = files[i].stat().st_size / (1024 * 1024)
            print(f"  {i + 1:>3}  {files[i].name}  ({size_mb:.1f} MB)")

        print(f"\n  [n] 下页  [p] 上页  [a] 全选  [q] 退出")
        print(f"  直接输入序号/范围，如: 1,3,5-8,-5,10-")
        choice = input(">>> ").strip().lower()

        if choice == "n":
            page = (page + 1) % total_pages
        elif choice == "p":
            page = (page - 1) % total_pages
        elif choice == "a":
            return list(files)
        elif choice == "q":
            return []
        else:
            try:
                idxs = parse_choice(choice, total)
                return [files[i] for i in idxs]
            except ValueError as e:
                print(f"❌ {e}")


# ---------- 选择目标格式 ----------
def choose_preset(presets: Dict[str, dict]) -> dict:
    """让用户选择转码预设"""
    print(f"\n{'='*50}")
    print("  目标格式")
    print(f"{'='*50}")
    for k, v in presets.items():
        print(f"  {k}  {v['name']}")

    while True:
        try:
            fmt = input(f"\n请选择格式 (1-{len(presets)})：").strip()
            if fmt in presets:
                return presets[fmt]
            print("❌ 无效选项，请重新选择")
        except ValueError:
            pass


# ---------- 单文件转码 ----------
def convert_one(src: Path, preset: dict, output_dir: Path) -> Optional[Path]:
    """转码单个文件，返回输出路径或 None"""
    dst = output_dir / f"{src.stem}.{preset['ext']}"
    cmd = ["ffmpeg", "-i", str(src), "-vcodec", preset["vcodec"]]
    if preset["acodec"] != "none":
        cmd += ["-acodec", preset["acodec"]]
    cmd += ["-y", str(dst)]

    print(f"\n🔄 转码中：{src.name}")
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        size_mb = dst.stat().st_size / (1024 * 1024)
        print(f"✅ 完成：{dst.name}  ({size_mb:.1f} MB)")
        return dst
    except subprocess.CalledProcessError as e:
        print(f"❌ 失败：{src.name}")
        if e.stderr:
            print(f"   错误信息：{e.stderr.decode('utf-8', errors='replace')[:200]}")
        return None


# ---------- 主流程 ----------
def main():
    # 检查 ffmpeg
    if not shutil.which("ffmpeg"):
        sys.exit("❌ ffmpeg 不在 PATH 中！请先安装 ffmpeg。")

    # 加载配置
    config = load_config()
    input_dir = (SCRIPT_DIR / config["input_dir"]).resolve()
    output_dir = (SCRIPT_DIR / config["output_dir"]).resolve()
    page_size = config.get("page_size", 10)
    presets = config.get("presets", DEFAULT_CONFIG["presets"])

    # 检查输入目录
    if not input_dir.exists():
        input_dir.mkdir(parents=True, exist_ok=True)
        print(f"已创建输入目录: {input_dir}")
        sys.exit("请将待转码的视频放入 input 文件夹后重新运行。")

    # 扫描视频文件
    files = sorted(
        [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS],
        key=lambda p: p.name,
    )
    if not files:
        sys.exit(f"❌ input 文件夹中没有找到视频文件！\n路径: {input_dir}")

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 输入目录: {input_dir}")
    print(f"📁 输出目录: {output_dir}")
    print(f"📹 发现 {len(files)} 个视频文件")

    # 选片
    chosen = paginate(files, page_size)
    if not chosen:
        print("未选择任何文件，拜拜！👋")
        return

    print(f"\n已选择 {len(chosen)} 个文件")

    # 选格式
    preset = choose_preset(presets)
    print(f"目标格式: {preset['name']}")

    # 确认
    confirm = input(f"\n确认将 {len(chosen)} 个文件转为 {preset['name']}？(y/n): ").strip().lower()
    if confirm != "y":
        print("已取消。")
        return

    # 开始转码
    print(f"\n{'='*50}")
    print("  开始批量转码  (Ctrl+C 可中断)")
    print(f"{'='*50}")

    done: List[Path] = []
    failed: List[str] = []
    total = len(chosen)

    for i, src in enumerate(chosen, 1):
        if STOP.is_set():
            break
        print(f"\n[{i}/{total}]", end="")
        dst = convert_one(src, preset, output_dir)
        if dst:
            done.append(dst)
        else:
            failed.append(src.name)

    # 中断处理
    if STOP.is_set():
        answer = input("\n\n⚠ 已中断，是否终止？(y/n): ").strip().lower()
        if answer == "y":
            print("用户终止转码。")
        else:
            STOP.clear()
            for i, src in enumerate(chosen[len(done) + len(failed) :], len(done) + len(failed) + 1):
                print(f"\n[{i}/{total}]", end="")
                dst = convert_one(src, preset, output_dir)
                if dst:
                    done.append(dst)
                else:
                    failed.append(src.name)

    # 汇总
    print(f"\n\n{'='*50}")
    print("  转码汇总")
    print(f"{'='*50}")
    print(f"  ✅ 成功: {len(done)} 个")
    print(f"  ❌ 失败: {len(failed)} 个")
    if STOP.is_set():
        print(f"  ⏹ 中断时剩余: {total - len(done) - len(failed)} 个")

    if done:
        print(f"\n  输出目录: {output_dir}")
        for d in done:
            size_mb = d.stat().st_size / (1024 * 1024)
            print(f"    ✅ {d.name}  ({size_mb:.1f} MB)")

    if failed:
        print(f"\n  失败文件:")
        for name in failed:
            print(f"    ❌ {name}")


if __name__ == "__main__":
    main()
