from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import asyncio
from datetime import datetime

app = FastAPI(title="Viral Video Generator API")

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carpeta para videos temporales
TEMP_DIR = Path(tempfile.gettempdir()) / "viral_videos"
TEMP_DIR.mkdir(exist_ok=True)

# Limpieza de videos viejos
@app.on_event("startup")
async def cleanup_old_videos():
    """Limpia videos generados hace más de 1 hora"""
    import time
    current_time = time.time()
    for file in TEMP_DIR.glob("*.mp4"):
        if current_time - file.stat().st_mtime > 3600:
            try:
                file.unlink()
            except:
                pass


def create_image_with_text(image_bytes: bytes, title: str, subtitle: str) -> bytes:
    """Crea imagen con texto overlay"""
    try:
        # Cargar imagen
        img = Image.open(io.BytesIO(image_bytes))

        # Redimensionar a 1080x1920 (TikTok)
        img.thumbnail((1080, 1920), Image.Resampling.LANCZOS)

        # Crear canvas 1080x1920
        canvas = Image.new('RGB', (1080, 1920), color='black')

        # Centrar imagen
        offset = ((1080 - img.width) // 2, (1920 - img.height) // 2)
        canvas.paste(img, offset)

        # Añadir overlay oscuro
        overlay = Image.new('RGBA', (1080, 1920), (0, 0, 0, 100))
        canvas = Image.alpha_composite(canvas.convert('RGBA'), overlay).convert('RGB')

        # Dibujar texto
        draw = ImageDraw.Draw(canvas)

        try:
            # Intentar usar fuente del sistema
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            font_subtitle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
        except:
            # Fallback a fuente default
            font_title = ImageFont.load_default()
            font_subtitle = ImageFont.load_default()

        # Dibujar título
        if title:
            bbox = draw.textbbox((0, 0), title, font=font_title)
            text_width = bbox[2] - bbox[0]
            text_x = (1080 - text_width) // 2
            draw.text((text_x, 300), title, fill='white', font=font_title, stroke_width=3, stroke_fill='black')

        # Dibujar subtítulo
        if subtitle:
            bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
            text_width = bbox[2] - bbox[0]
            text_x = (1080 - text_width) // 2
            draw.text((text_x, 450), subtitle, fill='white', font=font_subtitle, stroke_width=2, stroke_fill='black')

        # Convertir a bytes
        output = io.BytesIO()
        canvas.save(output, format='PNG')
        return output.getvalue()
    except Exception as e:
        print(f"Error creating image with text: {e}")
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")


async def generate_video_ffmpeg(image_bytes: bytes, title: str, subtitle: str, duration: int, video_id: str) -> Path:
    """Genera MP4 real usando FFmpeg"""
    try:
        # Crear imagen con texto
        image_with_text = create_image_with_text(image_bytes, title, subtitle)

        # Guardar imagen temporal
        input_image = TEMP_DIR / f"{video_id}_input.png"
        with open(input_image, 'wb') as f:
            f.write(image_with_text)

        # Ruta de salida
        output_video = TEMP_DIR / f"{video_id}.mp4"

        # Comando FFmpeg
        # -loop 1: repite imagen
        # -i: archivo input
        # -c:v libx264: codec H.264
        # -t: duración en segundos
        # -pix_fmt: formato de píxeles (yuv420p para máxima compatibilidad)
        # -vf: video filter (scale para asegurar resolución)
        # -preset: fast = más rápido
        # -crf: 23 = calidad buena

        cmd = [
            'ffmpeg',
            '-loop', '1',
            '-i', str(input_image),
            '-c:v', 'libx264',
            '-preset', 'ultrafast',  # ⚡ Máxima velocidad, mínimo CPU
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            '-vf', f'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black',
            '-r', '24',  # ⚡ 24 fps en lugar de 30 (imperceptible, 20% menos CPU)
            '-crf', '28',  # ⚡ Más compresión (archivos 50% más pequeños)
            '-threads', '1',  # ⚡ Usar solo 1 thread para no sobrecargar
            '-y',  # Sobrescribir sin preguntar
            str(output_video)
        ]

        # Ejecutar FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # ⚡ 30 segundos es más que suficiente con ultrafast
        )

        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")

        if not output_video.exists():
            raise Exception("Output file was not created")

        # Eliminar imagen temporal
        input_image.unlink(missing_ok=True)

        return output_video

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Video generation timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "temp_dir": str(TEMP_DIR),
        "videos_count": len(list(TEMP_DIR.glob("*.mp4")))
    }


@app.post("/api/v1/videos/generate")
async def generate_video(
    image: UploadFile = File(...),
    title: str = Form(""),
    subtitle: str = Form(""),
    duration: int = Form(30)
):
    """
    Genera video MP4 desde imagen + texto

    Parámetros:
    - image: Archivo de imagen (JPG, PNG)
    - title: Título del video (max 50 chars)
    - subtitle: Subtítulo (max 50 chars)
    - duration: Duración en segundos (15, 30, 60)

    Respuesta:
    - video_id: ID único del video
    - url: URL para descargar el MP4
    - duration: Duración del video
    - size: Tamaño del archivo en bytes
    - generated_at: Timestamp
    """
    try:
        # Validar duración
        if duration not in [15, 30, 60]:
            raise HTTPException(status_code=400, detail="Duration must be 15, 30, or 60 seconds")

        # Validar título/subtítulo
        title = title[:50] if title else ""
        subtitle = subtitle[:50] if subtitle else ""

        # Leer imagen
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="No image provided")

        # Generar ID único
        video_id = str(uuid.uuid4())

        # Generar video
        video_path = await generate_video_ffmpeg(image_bytes, title, subtitle, duration, video_id)

        # Información del archivo
        file_size = video_path.stat().st_size

        return {
            "status": "success",
            "video_id": video_id,
            "url": f"/api/v1/videos/{video_id}/download",
            "duration": duration,
            "size": file_size,
            "generated_at": datetime.now().isoformat(),
            "message": "Video generated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


@app.get("/api/v1/videos/{video_id}/download")
async def download_video(video_id: str):
    """
    Descarga video MP4 generado
    """
    video_path = TEMP_DIR / f"{video_id}.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=f"viral-video-{video_id[:8]}.mp4"
    )


@app.get("/api/v1/videos/{video_id}/preview")
async def preview_video(video_id: str):
    """
    Obtiene información del video para preview
    """
    video_path = TEMP_DIR / f"{video_id}.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    return {
        "status": "ready",
        "video_id": video_id,
        "size": video_path.stat().st_size,
        "download_url": f"/api/v1/videos/{video_id}/download",
        "created_at": datetime.fromtimestamp(video_path.stat().st_mtime).isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
