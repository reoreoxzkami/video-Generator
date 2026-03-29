from __future__ import annotations

import base64
import os
import io
import textwrap
import uuid
from pathlib import Path
from typing import List

import numpy as np
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from moviepy import ImageClip, concatenate_videoclips
from openai import OpenAI
from PIL import Image, ImageDraw

app = FastAPI(title="AI Video Generator")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

OUTPUT_DIR = Path("generated")
OUTPUT_DIR.mkdir(exist_ok=True)


def _fallback_image(prompt: str, width: int, height: int, seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    arr = np.zeros((height, width, 3), dtype=np.uint8)

    c1 = rng.integers(20, 230, size=3)
    c2 = rng.integers(20, 230, size=3)

    for y in range(height):
        t = y / max(height - 1, 1)
        arr[y, :, :] = ((1 - t) * c1 + t * c2).astype(np.uint8)

    image = Image.fromarray(arr)
    draw = ImageDraw.Draw(image)
    wrapped = "\n".join(textwrap.wrap(prompt, width=28))
    draw.rectangle([(30, height - 240), (width - 30, height - 30)], fill=(0, 0, 0, 120))
    draw.text((50, height - 220), f"AI Prompt:\n{wrapped}", fill=(255, 255, 255))
    return image


def _openai_images(prompt: str, count: int, width: int, height: int) -> List[Image.Image]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return [_fallback_image(f"{prompt} (scene {i + 1})", width, height, i + 1) for i in range(count)]

    client = OpenAI(api_key=api_key)
    images: List[Image.Image] = []
    size = "1024x1024"

    for i in range(count):
        result = client.images.generate(
            model="gpt-image-1",
            prompt=f"Cinematic still frame, scene {i + 1}: {prompt}",
            size=size,
            quality="medium",
        )

        b64_data = result.data[0].b64_json
        if not b64_data:
            raise HTTPException(status_code=500, detail="画像生成に失敗しました。")

        binary = base64.b64decode(b64_data)
        image = Image.open(io.BytesIO(binary))
        image = image.convert("RGB").resize((width, height))
        images.append(image)

    return images


def _build_video(images: List[Image.Image], seconds_per_image: float, output_file: Path) -> None:
    clips = []
    for image in images:
        frame = np.array(image)
        clips.append(ImageClip(frame).with_duration(seconds_per_image))

    video = concatenate_videoclips(clips, method="compose")
    video.write_videofile(
        str(output_file),
        fps=24,
        codec="libx264",
        audio=False,
        logger=None,
    )
    video.close()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
def generate_video(
    prompt: str = Form(...),
    scene_count: int = Form(4),
    seconds_per_scene: float = Form(1.5),
):
    scene_count = max(2, min(scene_count, 8))
    seconds_per_scene = max(0.8, min(seconds_per_scene, 4.0))

    width, height = 768, 768
    images = _openai_images(prompt, scene_count, width, height)

    file_name = f"video_{uuid.uuid4().hex}.mp4"
    output_path = OUTPUT_DIR / file_name
    _build_video(images, seconds_per_scene, output_path)

    return {"file": f"/download/{file_name}", "message": "動画を生成しました。"}


@app.get("/download/{file_name}")
def download(file_name: str):
    file_path = OUTPUT_DIR / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="ファイルが見つかりません。")
    return FileResponse(file_path, media_type="video/mp4", filename=file_name)
