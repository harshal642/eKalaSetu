from pathlib import Path

from PIL import (
    Image,
    ImageEnhance,
    ImageFilter,
    ImageOps,
)


# ============================================================================
# KALASETU IMAGE ENHANCEMENT
# ============================================================================
#
# Lightweight Pillow-based marketplace image enhancement.
#
# Pipeline:
#
# Original
#    ↓
# EXIF orientation correction
#    ↓
# Resize
#    ↓
# Lighting correction
#    ↓
# Colour correction
#    ↓
# Sharpness
#    ↓
# Studio-style presentation
#    ↓
# Save
#
# IMPORTANT:
# This pipeline does NOT generate or invent a new product.
# It only improves the submitted photograph.
# ============================================================================


MAX_IMAGE_SIZE = 1600

CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 1200

# Warm neutral studio background
BACKGROUND_COLOR = (250, 247, 242)


def prepare_image(image: Image.Image) -> Image.Image:
    """
    Prepare and enhance the original photograph.

    No AI-generated product content is added.
    """

    # ------------------------------------------------------------
    # Fix phone-camera orientation
    # ------------------------------------------------------------

    image = ImageOps.exif_transpose(image)

    # ------------------------------------------------------------
    # Convert to RGB
    # ------------------------------------------------------------

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    # ------------------------------------------------------------
    # Resize large images
    # ------------------------------------------------------------

    if max(image.size) > MAX_IMAGE_SIZE:

        image.thumbnail(
            (MAX_IMAGE_SIZE, MAX_IMAGE_SIZE),
            Image.Resampling.LANCZOS
        )

    # ------------------------------------------------------------
    # Convert to RGB for consistent processing
    # ------------------------------------------------------------

    image = image.convert("RGB")

    # ------------------------------------------------------------
    # Automatic contrast
    # ------------------------------------------------------------

    image = ImageOps.autocontrast(
        image,
        cutoff=1
    )

    # ------------------------------------------------------------
    # Lighting
    # ------------------------------------------------------------

    image = ImageEnhance.Brightness(
        image
    ).enhance(1.06)

    # ------------------------------------------------------------
    # Contrast
    # ------------------------------------------------------------

    image = ImageEnhance.Contrast(
        image
    ).enhance(1.10)

    # ------------------------------------------------------------
    # Colour
    # ------------------------------------------------------------

    image = ImageEnhance.Color(
        image
    ).enhance(1.08)

    # ------------------------------------------------------------
    # Sharpness
    # ------------------------------------------------------------

    image = ImageEnhance.Sharpness(
        image
    ).enhance(1.18)

    # ------------------------------------------------------------
    # Subtle edge sharpening
    # ------------------------------------------------------------

    image = image.filter(
        ImageFilter.UnsharpMask(
            radius=1.0,
            percent=80,
            threshold=3
        )
    )

    return image


def fit_product_on_canvas(
    image: Image.Image,
    canvas_width: int,
    canvas_height: int
):
    """
    Fit the product photograph inside a clean marketplace canvas.

    The image keeps its original aspect ratio.
    """

    image = image.copy()

    # Leave comfortable margins around the product
    max_width = int(canvas_width * 0.78)
    max_height = int(canvas_height * 0.78)

    ratio = min(
        max_width / image.width,
        max_height / image.height
    )

    new_width = max(
        1,
        int(image.width * ratio)
    )

    new_height = max(
        1,
        int(image.height * ratio)
    )

    image = image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS
    )

    x = (
        canvas_width - new_width
    ) // 2

    y = (
        canvas_height - new_height
    ) // 2

    return image, x, y


def create_studio_image(
    image: Image.Image
) -> Image.Image:
    """
    Create a clean studio-style marketplace presentation.

    The original image is placed on a warm neutral background.

    A subtle shadow is added to improve visual depth.
    """

    canvas = Image.new(
        "RGBA",
        (
            CANVAS_WIDTH,
            CANVAS_HEIGHT
        ),
        BACKGROUND_COLOR + (255,)
    )

    image = image.convert("RGB")

    fitted, x, y = fit_product_on_canvas(
        image,
        CANVAS_WIDTH,
        CANVAS_HEIGHT
    )

    # ------------------------------------------------------------
    # Create subtle soft shadow
    # ------------------------------------------------------------

    shadow_alpha = Image.new(
        "L",
        fitted.size,
        55
    )

    shadow_alpha = shadow_alpha.filter(
        ImageFilter.GaussianBlur(22)
    )

    shadow_layer = Image.new(
        "RGBA",
        (
            CANVAS_WIDTH,
            CANVAS_HEIGHT
        ),
        (60, 45, 30, 0)
    )

    full_shadow_alpha = Image.new(
        "L",
        (
            CANVAS_WIDTH,
            CANVAS_HEIGHT
        ),
        0
    )

    shadow_y = (
        y + int(fitted.height * 0.06)
    )

    full_shadow_alpha.paste(
        shadow_alpha,
        (
            x,
            shadow_y
        )
    )

    shadow_layer.putalpha(
        full_shadow_alpha
    )

    canvas = Image.alpha_composite(
        canvas,
        shadow_layer
    )

    # ------------------------------------------------------------
    # Place enhanced product
    # ------------------------------------------------------------

    canvas.alpha_composite(
        fitted.convert("RGBA"),
        (
            x,
            y
        )
    )

    return canvas.convert("RGB")


def enhance_image(
    input_path: str,
    output_path: str
) -> str:
    """
    Main KalaSetu image enhancement function.

    Parameters
    ----------
    input_path:
        Original uploaded image.

    output_path:
        Path where enhanced image should be saved.

    Returns
    -------
    str
        Enhanced image path.
    """

    input_path = str(
        Path(input_path)
    )

    output_path = str(
        Path(output_path)
    )

    # ------------------------------------------------------------
    # Open original
    # ------------------------------------------------------------

    with Image.open(input_path) as original:

        # --------------------------------------------------------
        # Prepare + enhance
        # --------------------------------------------------------

        enhanced = prepare_image(
            original
        )

        # --------------------------------------------------------
        # Studio-style presentation
        # --------------------------------------------------------

        final_image = create_studio_image(
            enhanced
        )

        # --------------------------------------------------------
        # Save
        # --------------------------------------------------------

        Path(output_path).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        final_image.save(
            output_path,
            "JPEG",
            quality=90,
            optimize=True
        )

    return output_path


# ============================================================================
# COMMAND-LINE TEST
# ============================================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) != 3:

        print(
            "Usage:"
        )

        print(
            "python ai/image_enhancement.py "
            "input.jpg output.jpg"
        )

        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    print(
        f"[KalaSetu] Enhancing: {input_file}"
    )

    enhance_image(
        input_file,
        output_file
    )

    print(
        f"[KalaSetu] Enhanced image saved: {output_file}"
    )