"""
Engine module for image conversion to WebP format using Pillow.
Handles color spaces, EXIF orientation, alpha channel, and compression errors.
"""

from pathlib import Path
from typing import Tuple
from PIL import Image, ImageOps

# Custom exception for reporting
class ImageConversionError(Exception):
    """Raised when image conversion fails due to corrupted, invalid, or oversized data."""
    pass


def convert_image_to_webp(
    source_path: Path,
    destination_path: Path,
    quality: int = 80,
    lossless: bool = False,
    method: int = 6
) -> Tuple[int, int]:
    """
    Open an image, normalize color modes and EXIF orientation, and save as WebP.
    
    Returns:
        Tuple[int, int]: (original_file_size_bytes, converted_file_size_bytes)
        
    Raises:
        ImageConversionError: On corrupted images, DecompressionBombError, or I/O failure.
    """
    try:
        orig_size = source_path.stat().st_size
        if orig_size == 0:
            raise ImageConversionError("Empty file (0-byte file)")
    except Exception as e:
        raise ImageConversionError(f"Cannot access source file: {e}")

    try:
        with Image.open(source_path) as img:
            # Correct orientation from EXIF tags
            try:
                img = ImageOps.exif_transpose(img) or img
            except Exception:
                # If EXIF reading fails, continue with original orientation
                pass

            # Handle color modes
            if img.mode == "CMYK":
                img = img.convert("RGB")
            elif img.mode == "P":
                # If palette image contains transparency, convert to RGBA
                if "transparency" in img.info:
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")
            elif img.mode in ("RGBA", "LA"):
                # Preserve alpha channel
                pass
            elif img.mode not in ("RGB", "L"):
                # Normalize 1-bit or unusual modes
                img = img.convert("RGB")

            # Ensure destination directory exists
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            img.save(
                destination_path,
                format="WEBP",
                quality=quality,
                lossless=lossless,
                method=method
            )

        new_size = destination_path.stat().st_size
        return orig_size, new_size

    except Image.DecompressionBombError as e:
        raise ImageConversionError(f"Image too large (Pixel Bomb protection): {e}")
    except (Image.UnidentifiedImageError, OSError, IOError) as e:
        raise ImageConversionError(f"Corrupted or invalid image: {e}")
    except Exception as e:
        raise ImageConversionError(f"Unexpected conversion error: {e}")
