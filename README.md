# Ajustar imágenes

Aplicación de escritorio muy simple para preparar fotos de producto: recorta el fondo blanco sobrante,
escala el producto y lo centra sobre un lienzo blanco de **800×800 px** (margen del 8 %).
Se elige o se arrastra una imagen, se ve el antes y el después y se guarda como JPG.

Para fotos pequeñas o de poca calidad hay tres modos:

- **Sin mejorar**: solo ajusta el tamaño.
- **Mejorar calidad**: suaviza el ruido de compresión, amplía con Lanczos y afina (rápido y seguro).
- **Mejorar con IA**: amplía x4 con Real-ESRGAN (`realesr-general-x4v3`, ONNX, licencia BSD-3, en `assets/models`).
  Más lento y puede deformar texto muy pequeño, por lo que conviene revisar el resultado.

- `ajustar_imagen.py`: lógica de ajuste (Pillow). Constantes `ANCHO`, `ALTO`, `MARGEN`.
- `main.py`: interfaz con Tkinter.
- `.github/workflows/build.yml`: tests + compilación con PyInstaller en GitHub Actions
  (`.exe` para Windows y `.app` para Mac). Los resultados se descargan en la pestaña **Actions → Artifacts**.

## Desarrollo

```bash
pip install -r requirements-dev.txt
pytest
python main.py
```
