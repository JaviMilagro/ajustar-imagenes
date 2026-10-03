# Ajustar imágenes

Aplicación de escritorio muy simple para preparar fotos de producto: recorta el fondo blanco sobrante,
escala el producto y lo centra sobre un lienzo blanco de **800×800 px** (margen del 8 %).
Se elige una imagen, se ve el resultado y se guarda como JPG.

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
