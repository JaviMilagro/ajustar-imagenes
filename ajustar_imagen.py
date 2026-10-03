"""Lógica de ajuste de imagen: recorta el fondo blanco sobrante, escala el
producto y lo centra en un lienzo blanco de tamaño fijo (800x800).

Mejoras opcionales cuando la foto original es pequeña o de poca calidad:
  - "clasica": suaviza el ruido de compresión, amplía con Lanczos y afina.
  - "ia":      amplía con Real-ESRGAN (modelo ONNX incluido en assets/models).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageOps

ANCHO, ALTO = 800, 800     # tamaño final de todas las imágenes (cuadrado estándar)
MARGEN = 0.08              # espacio en blanco a cada lado (8 %)
UMBRAL = 20                # diferencia mínima con el blanco para considerar "producto"

MODELO_IA = os.path.join("assets", "models", "realesr-general-x4v3.onnx")
_sesion_ia = None


def ruta_recurso(relativa: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relativa)


def _a_rgb_sobre_blanco(im: Image.Image) -> Image.Image:
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fondo = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(fondo, im)
    return im.convert("RGB")


def _recortar_producto(im: Image.Image) -> Image.Image:
    blanco = Image.new("RGB", im.size, (255, 255, 255))
    mascara = ImageChops.difference(im, blanco).convert("L").point(lambda p: 255 if p > UMBRAL else 0)
    caja = mascara.getbbox()
    return im.crop(caja) if caja else im


def _tamano_destino(im: Image.Image):
    max_w = round(ANCHO * (1 - 2 * MARGEN))
    max_h = round(ALTO * (1 - 2 * MARGEN))
    escala = min(max_w / im.width, max_h / im.height)
    return escala, (max(1, round(im.width * escala)), max(1, round(im.height * escala)))


def info_producto(im: Image.Image):
    """Devuelve (ancho, alto, escala) del producto una vez recortado el fondo blanco.
    escala > 1 significa que habrá que ampliarlo para llenar el lienzo."""
    producto = _recortar_producto(_a_rgb_sobre_blanco(im))
    return producto.width, producto.height, _tamano_destino(producto)[0]


def _mejora_clasica(im: Image.Image, escala: float, nuevo) -> Image.Image:
    if escala > 1:
        if max(im.size) < 450:   # fotos pequeñas suelen traer cuadritos de compresión JPEG
            im = im.filter(ImageFilter.GaussianBlur(0.6))
        im = im.resize(nuevo, Image.LANCZOS)
        return im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=190, threshold=1))
    im = im.resize(nuevo, Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=40, threshold=2))


def _sesion():
    global _sesion_ia
    if _sesion_ia is None:
        import onnxruntime as ort
        _sesion_ia = ort.InferenceSession(ruta_recurso(MODELO_IA), providers=["CPUExecutionProvider"])
    return _sesion_ia


def _mejora_ia(im: Image.Image, progreso=None) -> Image.Image:
    """Amplía x4 con Real-ESRGAN procesando por trozos para no gastar mucha memoria."""
    sesion = _sesion()
    entrada = sesion.get_inputs()[0].name
    arr = np.asarray(im, dtype=np.float32) / 255.0
    h, w, _ = arr.shape
    trozo, borde = 160, 12
    relleno = np.pad(arr, ((borde, borde), (borde, borde), (0, 0)), mode="edge")
    salida = np.zeros((h * 4, w * 4, 3), dtype=np.float32)
    ys, xs = list(range(0, h, trozo)), list(range(0, w, trozo))
    total, hecho = len(ys) * len(xs), 0
    for y0 in ys:
        for x0 in xs:
            y1, x1 = min(y0 + trozo, h), min(x0 + trozo, w)
            parte = relleno[y0:y1 + 2 * borde, x0:x1 + 2 * borde]
            tensor = np.ascontiguousarray(parte.transpose(2, 0, 1)[None])
            res = sesion.run(None, {entrada: tensor})[0][0].transpose(1, 2, 0)
            b = borde * 4
            salida[y0 * 4:y1 * 4, x0 * 4:x1 * 4] = res[b:b + (y1 - y0) * 4, b:b + (x1 - x0) * 4]
            hecho += 1
            if progreso:
                progreso(hecho / total)
    return Image.fromarray((np.clip(salida, 0, 1) * 255 + 0.5).astype(np.uint8))


def ajustar(im: Image.Image, mejora: str = "ninguna", progreso=None) -> Image.Image:
    """mejora: "ninguna", "clasica" o "ia"."""
    im = _recortar_producto(_a_rgb_sobre_blanco(im))
    escala, nuevo = _tamano_destino(im)

    if mejora == "ia" and escala > 1:
        im = _mejora_ia(im, progreso).resize(nuevo, Image.LANCZOS)
    elif mejora in ("clasica", "ia"):   # la IA no hace falta si la foto ya es grande
        im = _mejora_clasica(im, escala, nuevo)
    else:
        im = im.resize(nuevo, Image.LANCZOS)

    lienzo = Image.new("RGB", (ANCHO, ALTO), (255, 255, 255))
    lienzo.paste(im, ((ANCHO - im.width) // 2, (ALTO - im.height) // 2))
    return lienzo
