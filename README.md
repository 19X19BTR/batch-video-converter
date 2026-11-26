# 批量选片转码器 (Batch Video Converter)

一款交互式批量视频转码工具，支持灵活的选取语法和多种输出格式。

## ✨ 功能特性

- 📁 **批量扫描** — 自动识别 input 目录中的视频文件
- 🔢 **灵活选取** — 支持单号、范围、区间、混合选取
- 📄 **分页浏览** — 文件多时自动分页，支持翻页和全选
- 🎬 **多格式输出** — 支持 H.264/H.265/Xvid 等编码的 mp4/mkv/avi/mov/gif
- ⏹ **中断恢复** — 转码中可随时 Ctrl+C 中断，选择继续或终止
- ⚙️ **可配置** — 通过 config.json 自定义输入输出路径、分页大小、预设格式

## 📋 前置条件

- Python 3.9+
- [FFmpeg](https://ffmpeg.org/)（需在系统 PATH 中）

安装 FFmpeg（Windows）：
```bash
# 使用 winget
winget install FFmpeg

# 或使用 scoop
scoop install ffmpeg

# 或使用 chocolatey
choco install ffmpeg
```

## 🚀 快速开始

```bash
# 1. 将待转码的视频放入 input/ 目录
# 2. 运行脚本
python batch_convert.py

# 3. 按提示选择文件和格式
# 4. 转码完成后查看 output/ 目录
```

## 📂 目录结构

```
convert/
├── batch_convert.py   # 主程序
├── config.json        # 配置文件（首次运行自动生成）
├── README.md          # 本文件
├── tests/             # 单元测试（选片语法）
├── input/             # 输入目录（放入待转码视频）
└── output/            # 输出目录（转码后的文件）
```

## ⚙️ 配置说明 (config.json)

```json
{
  "input_dir": "./input",
  "output_dir": "./output",
  "page_size": 10,
  "presets": {
    "1": {"name": "mp4(H.264)", "ext": "mp4", "vcodec": "libx264", "acodec": "aac"},
    "2": {"name": "mp4(H.265)", "ext": "mp4", "vcodec": "libx265", "acodec": "aac"},
    "3": {"name": "mkv(H.264)", "ext": "mkv", "vcodec": "libx264", "acodec": "copy"},
    "4": {"name": "avi(Xvid)",  "ext": "avi", "vcodec": "libxvid", "acodec": "mp3"},
    "5": {"name": "mov(H.264)", "ext": "mov", "vcodec": "libx264", "acodec": "aac"},
    "6": {"name": "gif",        "ext": "gif", "vcodec": "gif",     "acodec": "none"}
  }
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `input_dir` | 输入目录（相对于脚本目录） | `./input` |
| `output_dir` | 输出目录（相对于脚本目录） | `./output` |
| `page_size` | 分页显示的文件数量 | `10` |
| `presets` | 转码预设，key 为选项编号 | 见上方 |

### 自定义预设

每个预设包含以下字段：
- `name` — 显示名称
- `ext` — 输出文件扩展名
- `vcodec` — FFmpeg 视频编码器（如 `libx264`、`libx265`、`libxvid`、`gif`）
- `acodec` — FFmpeg 音频编码器（如 `aac`、`mp3`、`copy`，`none` 表示无音频）

## 🎮 选片语法

程序使用一套灵活的选取语法：

| 语法 | 示例 | 说明 |
|------|------|------|
| 单号 | `3` | 选择第 3 个文件 |
| 逗号分隔 | `1,3,5` | 选择第 1、3、5 个文件 |
| 范围 | `3-7` | 选择第 3 到第 7 个文件 |
| 前缀区间 | `-5` | 选择第 1 到第 5 个文件 |
| 后缀区间 | `8-` | 选择第 8 个到最后一个文件 |
| 混合 | `1,3-5,8-,12` | 以上语法任意组合 |
| 全选 | `a` | 选择所有文件 |

## 💡 使用示例

```
📁 输入目录: D:\videos\input
📁 输出目录: D:\videos\output
📹 发现 25 个视频文件

==================================================
  第 1 页 / 共 3 页    (共 25 个文件)
==================================================
    1  video01.mp4  (120.5 MB)
    2  video02.mp4  (85.3 MB)
    3  video03.avi  (200.1 MB)
  ...

  [n] 下页  [p] 上页  [a] 全选  [q] 退出
  直接输入序号/范围，如: 1,3,5-8,-5,10-
>>> 1,3-5

已选择 4 个文件

==================================================
  目标格式
==================================================
  1  mp4(H.264)
  2  mp4(H.265)
  3  mkv(H.264)
  4  avi(Xvid)
  5  mov(H.264)
  6  gif

请选择格式 (1-6)：1
目标格式: mp4(H.264)

确认将 4 个文件转为 mp4(H.264)？(y/n): y

🔄 转码中：video01.mp4
✅ 完成：video01.mp4  (95.2 MB)
...
```

## ❓ 常见问题

**Q: 提示 "ffmpeg 不在 PATH 中"**
A: 安装 FFmpeg 并确保其 bin 目录已添加到系统 PATH 环境变量。

**Q: 如何更改默认输入/输出路径？**
A: 运行一次程序后会自动生成 `config.json`，编辑其中的 `input_dir` 和 `output_dir` 字段即可。

**Q: 转码速度很慢？**
A: H.265 编码比 H.264 慢很多但压缩率更高。如需快速转码，优先选择 H.264 或使用 `copy` 音频编码。

## 🧪 测试

纯标准库 `unittest`，不依赖 ffmpeg：

```bash
python -m unittest discover -s tests -t .
```

18 个用例，专测选片语法 `parse_choice()`：

- 单号 / 逗号 / 范围 / 前缀 `-5` / 后缀 `8-` / 混合 `1,3-5,8-`
- 乱序输入排序去重、带空格、末尾多余逗号
- 越界（0、11、`5-11`）、范围反了（`7-3`）、非数字 → 都抛 `ValueError`
- 只有 1 个文件、`1-1`、`10-10` 这种边界

## 📄 License

MIT License
