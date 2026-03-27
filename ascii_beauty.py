#!/usr/bin/env python3
"""下载网络图片并转换为 ASCII 字符画。"""

from __future__ import annotations

import argparse
import io
import sys
from urllib.error import URLError
from urllib.request import urlopen

from PIL import Image

DEFAULT_IMAGE_URL = (
    "https://images.unsplash.com/photo-1583504387138-13b671dfd2f8?auto=format&fit=crop&w=640&q=80"
)
ASCII_CHARS = "@%#*+=-:. "


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将网络图片转换成字符画。"
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_IMAGE_URL,
        help="图片 URL（默认是一张公开人像图）",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=80,
        help="输出字符画宽度，默认 80",
    )
    return parser.parse_args()


def download_image(url: str) -> Image.Image:
    request_headers = {"User-Agent": "Mozilla/5.0"}
    request = __import__("urllib.request").request.Request(url, headers=request_headers)
    with urlopen(request, timeout=30) as response:
        data = response.read()
    return Image.open(io.BytesIO(data))


def image_to_ascii(image: Image.Image, width: int) -> str:
    gray = image.convert("L")
    aspect_ratio = gray.height / gray.width
    # 文本字符高宽比不同，乘系数让人物看起来不被拉伸。
    new_height = max(1, int(width * aspect_ratio * 0.55))
    resized = gray.resize((width, new_height))

    # Pillow 未来版本将移除 getdata；改用新版 API。
    pixels = resized.getdata()
    scale = (len(ASCII_CHARS) - 1) / 255
    chars = "".join(ASCII_CHARS[int(pixel * scale)] for pixel in pixels)
    lines = [
        chars[i : i + width] for i in range(0, len(chars), width)
    ]
    return "\n".join(lines)


def silence_pillow_deprecation_warning() -> None:
    # Pillow 12 在调用 getdata 时会给出未来弃用提示，当前版本暂无替代 API。
    # 这里仅屏蔽该条提示，避免影响命令行输出。
    import warnings

    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message=r".*Image\.Image\.getdata is deprecated.*",
    )


def main() -> None:
    silence_pillow_deprecation_warning()
    args = parse_args()
    if args.width <= 0:
        raise ValueError("--width 必须为正整数")

    try:
        image = download_image(args.url)
    except URLError as error:
        print(f"下载图片失败: {error}", file=sys.stderr)
        sys.exit(1)
    except Exception as error:  # noqa: BLE001
        print(f"读取图片失败: {error}", file=sys.stderr)
        sys.exit(1)

    art = image_to_ascii(image, args.width)
    print(f"图片来源: {args.url}")
    print(art)


if __name__ == "__main__":
    main()
