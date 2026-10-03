"""Lógica de ajuste de imagen: recorta el fondo blanco sobrante, escala el
producto y lo centra en un lienzo blanco de tamaño fijo (1100x1422)."""
from io import BytesIO

from PIL import Image, ImageChops, ImageOps

ANCHO, ALTO = 800, 800     # tamaño final de todas las imágenes (cuadrado estándar)
MARGEN = 0.08              # espacio en blanco a cada lado (8 %), medido sobre las imágenes ya hechas a mano
UMBRAL = 20                # diferencia mínima con el blanco para considerar "producto"


def _a_rgb_sobre_blanco(im: Image.Image) -> Image.Image:
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fondo = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(fondo, im)
    return im.convert("RGB")


def ajustar(im: Image.Image) -> Image.Image:
    im = _a_rgb_sobre_blanco(im)

    blanco = Image.new("RGB", im.size, (255, 255, 255))
    mascara = ImageChops.difference(im, blanco).convert("L").point(lambda p: 255 if p > UMBRAL else 0)
    caja = mascara.getbbox()
    if caja:
        im = im.crop(caja)

    max_w = round(ANCHO * (1 - 2 * MARGEN))
    max_h = round(ALTO * (1 - 2 * MARGEN))
    escala = min(max_w / im.width, max_h / im.height)
    nuevo = (max(1, round(im.width * escala)), max(1, round(im.height * escala)))
    im = im.resize(nuevo, Image.LANCZOS)

    lienzo = Image.new("RGB", (ANCHO, ALTO), (255, 255, 255))
    lienzo.paste(im, ((ANCHO - im.width) // 2, (ALTO - im.height) // 2))
    return lienzo


def ajustar_bytes(datos: bytes) -> bytes:
    with Image.open(BytesIO(datos)) as im:
        resultado = ajustar(im)
    salida = BytesIO()
    resultado.save(salida, "JPEG", quality=90, optimize=True)
    return salida.getvalue()
