"""
Image Processing Service
Resize, crop, validate images for video generation
"""

from PIL import Image, ImageEnhance
from pathlib import Path
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class ImageService:
    """Service for image processing and validation"""

    # TikTok vertical format
    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    MAX_SIZE_MB = 50

    @staticmethod
    def validate_image(image_path: str) -> Tuple[bool, str]:
        """
        Validate image file

        Returns:
            (is_valid: bool, message: str)
        """
        try:
            path = Path(image_path)

            # Check file exists
            if not path.exists():
                return False, "Image file not found"

            # Check file size
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > ImageService.MAX_SIZE_MB:
                return False, f"Image too large ({file_size_mb:.1f}MB, max {ImageService.MAX_SIZE_MB}MB)"

            # Try to open
            img = Image.open(path)
            img.verify()

            return True, "Image valid"

        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False, f"Invalid image: {str(e)}"

    @staticmethod
    def process_image(
        input_path: str,
        output_path: str = None,
    ) -> Tuple[bool, str, str]:
        """
        Process image: resize to 1080x1920, enhance quality

        Returns:
            (success: bool, message: str, output_path: str)
        """
        try:
            # Validate first
            valid, msg = ImageService.validate_image(input_path)
            if not valid:
                return False, msg, ""

            # Open and convert to RGB
            img = Image.open(input_path)
            if img.mode != "RGB":
                img = img.convert("RGB")

            logger.info(f"Original size: {img.size}")

            # Resize with smart crop (center crop to maintain aspect)
            img_resized = ImageService._smart_crop_and_resize(
                img,
                ImageService.TARGET_WIDTH,
                ImageService.TARGET_HEIGHT,
            )

            # Enhance: increase contrast and saturation
            enhancer = ImageEnhance.Contrast(img_resized)
            img_enhanced = enhancer.enhance(1.15)  # +15% contrast

            enhancer = ImageEnhance.Color(img_enhanced)
            img_enhanced = enhancer.enhance(1.20)  # +20% saturation

            # Determine output path
            if output_path is None:
                output_path = str(Path(input_path).parent / f"processed_{Path(input_path).name}")

            # Save
            img_enhanced.save(output_path, quality=95)

            logger.info(f"Image processed: {img_resized.size} -> {output_path}")
            return True, "Image processed successfully", output_path

        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return False, f"Processing error: {str(e)}", ""

    @staticmethod
    def _smart_crop_and_resize(
        img: Image.Image,
        target_width: int,
        target_height: int,
    ) -> Image.Image:
        """
        Resize image to target dimensions with smart center crop

        Maintains aspect ratio and centers content
        """
        img_width, img_height = img.size
        target_ratio = target_width / target_height
        img_ratio = img_width / img_height

        if img_ratio > target_ratio:
            # Image is too wide, crop width
            new_width = int(img_height * target_ratio)
            left = (img_width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img_height))
        else:
            # Image is too tall, crop height
            new_height = int(img_width / target_ratio)
            top = (img_height - new_height) // 2
            img = img.crop((0, top, img_width, top + new_height))

        # Resize to exact target dimensions
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        return img

    @staticmethod
    def get_image_info(image_path: str) -> dict:
        """Get image metadata"""
        try:
            img = Image.open(image_path)
            return {
                "width": img.width,
                "height": img.height,
                "size_mb": Path(image_path).stat().st_size / (1024 * 1024),
                "format": img.format,
                "mode": img.mode,
            }
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return {}
