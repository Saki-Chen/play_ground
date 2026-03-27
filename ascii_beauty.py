#!/usr/bin/env python3
"""下载网络图片并转换为 ASCII 字符画，支持自动人脸裁剪。"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import cv2
import numpy as np
from PIL import Image

DEFAULT_IMAGE_URL = (
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=640&q=80"
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
        "--image",
        help="本地图片路径（设置后优先于 --url）",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=80,
        help="输出字符画宽度，默认 80",
    )
    parser.add_argument(
        "--disable-face-crop",
        action="store_true",
        help="禁用自动人脸检测和裁剪",
    )
    return parser.parse_args()


def download_image(url: str) -> Image.Image:
    request_headers = {"User-Agent": "Mozilla/5.0"}
    request = __import__("urllib.request").request.Request(url, headers=request_headers)
    with urlopen(request, timeout=30) as response:
        data = response.read()
    return Image.open(io.BytesIO(data))


def load_local_image(image_path: str) -> Image.Image:
    return Image.open(image_path)


def detect_and_crop_face(image: Image.Image) -> Image.Image:
    rgb_image = image.convert("RGB")
    np_image = np.array(rgb_image)
    gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)

    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(str(cascade_path))
    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40),
    )

    if len(faces) == 0:
        return rgb_image

    x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
    margin_x = int(w * 0.6)
    margin_top = int(h * 0.9)
    margin_bottom = int(h * 1.2)

    left = max(0, x - margin_x)
    top = max(0, y - margin_top)
    right = min(np_image.shape[1], x + w + margin_x)
    bottom = min(np_image.shape[0], y + h + margin_bottom)

    cropped = np_image[top:bottom, left:right]
    return Image.fromarray(cropped)


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
        if args.image:
            image = load_local_image(args.image)
            image_source = args.image
        else:
            image = download_image(args.url)
            image_source = args.url
    except URLError as error:
        print(f"下载图片失败: {error}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as error:
        print(f"本地图片不存在: {error}", file=sys.stderr)
        sys.exit(1)
    except Exception as error:  # noqa: BLE001
        print(f"读取图片失败: {error}", file=sys.stderr)
        sys.exit(1)

    processed_image = image
    if not args.disable_face_crop:
        processed_image = detect_and_crop_face(image)

    art = image_to_ascii(processed_image, args.width)
    print(f"图片来源: {image_source}")
    if args.disable_face_crop:
        print("模式: 原图转字符画（未启用人脸裁剪）")
    else:
        print("模式: 自动人脸裁剪后转字符画")
    print(art)


if __name__ == "__main__":
    main()
