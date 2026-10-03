import sys
from pathlib import Path

from PIL import Image, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ajustar_imagen import ALTO, ANCHO, ajustar


def caja_producto(im):
    blanco = Image.new("RGB", im.size, (255, 255, 255))
    return ImageChops.difference(im, blanco).convert("L").point(lambda p: 255 if p > 20 else 0).getbbox()


def test_tamano_fijo_y_centrado():
    origen = Image.new("RGB", (900, 400), (255, 255, 255))
    origen.paste(Image.new("RGB", (200, 300), (200, 0, 0)), (300, 50))
    salida = ajustar(origen)
    assert salida.size == (ANCHO, ALTO)
    x0, y0, x1, y1 = caja_producto(salida)
    assert abs(x0 - (ANCHO - x1)) <= 2 and abs(y0 - (ALTO - y1)) <= 2


def test_acepta_png_con_transparencia():
    origen = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    origen.paste(Image.new("RGBA", (100, 100), (0, 0, 255, 255)), (100, 100))
    assert ajustar(origen).size == (ANCHO, ALTO)


def test_imagen_toda_blanca_no_falla():
    assert ajustar(Image.new("RGB", (50, 50), (255, 255, 255))).size == (ANCHO, ALTO)
