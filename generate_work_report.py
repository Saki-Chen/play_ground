#!/usr/bin/env python3
"""Generate a PDF summary of the completed work."""

from __future__ import annotations

import subprocess
from io import BytesIO
from pathlib import Path

import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

DEFAULT_IMAGE_URL = (
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330"
    "?auto=format&fit=crop&w=640&q=80"
)
OUTPUT_FILE = Path("work_results_report.pdf")


def run_ascii_preview() -> str:
    result = subprocess.run(
        ["python3", "ascii_beauty.py", "--width", "60"],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = result.stdout.splitlines()
    preview_lines = lines[:30]
    return "\n".join(preview_lines)


def download_default_image() -> bytes:
    response = requests.get(
        DEFAULT_IMAGE_URL,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    return response.content


def draw_wrapped_text(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    font_name: str,
    font_size: int,
    max_width: float,
    line_height: float,
) -> float:
    pdf.setFont(font_name, font_size)
    words = text.split(" ")
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if pdf.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
            continue
        pdf.drawString(x, y, current)
        y -= line_height
        current = word
    if current:
        pdf.drawString(x, y, current)
        y -= line_height
    return y


def main() -> None:
    ascii_preview = run_ascii_preview()
    image_data = download_default_image()

    pdf = canvas.Canvas(str(OUTPUT_FILE), pagesize=A4)
    page_width, page_height = A4
    margin = 40
    y = page_height - margin

    pdf.setTitle("Work Results Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margin, y, "Work Results Report")
    y -= 28

    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin, y, "Repository: play_ground")
    y -= 14
    pdf.drawString(
        margin,
        y,
        "Topic: Environment setup + image-to-ASCII + face detection crop",
    )
    y -= 22

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, y, "Implemented items")
    y -= 16
    pdf.setFont("Helvetica", 10)
    bullet_items = [
        "Initialized Python virtual environment (.venv).",
        "Built URL-based image to ASCII converter in ascii_beauty.py.",
        "Added automatic face detection and face-centered cropping (OpenCV Haar cascade).",
        "Kept optional no-crop mode (--disable-face-crop).",
        f"Default image URL: {DEFAULT_IMAGE_URL}",
    ]
    for item in bullet_items:
        y = draw_wrapped_text(
            pdf,
            f"- {item}",
            margin,
            y,
            "Helvetica",
            10,
            page_width - 2 * margin,
            13,
        )

    y -= 6
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, y, "How to run")
    y -= 16
    run_cmds = [
        "source .venv/bin/activate",
        "pip install -r requirements.txt",
        "python ascii_beauty.py --width 70",
        "python ascii_beauty.py --width 70 --disable-face-crop",
    ]
    pdf.setFont("Courier", 9)
    for cmd in run_cmds:
        pdf.drawString(margin, y, f"$ {cmd}")
        y -= 12

    y -= 6
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, y, "Default source image preview")
    y -= 12

    image = ImageReader(BytesIO(image_data))
    image_width = page_width - 2 * margin
    image_height = 180
    pdf.drawImage(
        image,
        margin,
        y - image_height,
        width=image_width,
        height=image_height,
        preserveAspectRatio=True,
        mask="auto",
        anchor="n",
    )
    y -= image_height + 14

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, y, "ASCII preview (first lines)")
    y -= 16
    pdf.setFont("Courier", 7)
    for line in ascii_preview.splitlines():
        if y < margin + 10:
            break
        pdf.drawString(margin, y, line[:130])
        y -= 8

    pdf.save()
    print(f"Generated {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
