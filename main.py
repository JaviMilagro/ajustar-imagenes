"""Ventana sencilla: elegir una imagen, ver el resultado y guardarla ajustada."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk

from ajustar_imagen import ajustar

TIPOS = [("Imágenes", "*.jpg *.jpeg *.png *.webp"), ("Todos los archivos", "*.*")]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ajustar imágenes")
        self.geometry("560x720")
        self.minsize(480, 600)
        self.configure(bg="white")
        self.resultado = None
        self.nombre = "imagen.jpg"
        self._miniatura = None

        fuente = ("Helvetica", 18, "bold")
        tk.Label(self, text="Ajustar imágenes", font=("Helvetica", 26, "bold"), bg="white").pack(pady=(20, 6))
        tk.Label(self, text="1. Elige la foto    2. Guárdala", font=("Helvetica", 16), bg="white").pack()

        self.btn_elegir = tk.Button(self, text="1. ELEGIR IMAGEN", font=fuente, height=2,
                                    bg="#2d6cdf", fg="white", activebackground="#1f4fa8",
                                    command=self.elegir)
        self.btn_elegir.pack(fill="x", padx=40, pady=(20, 10))

        self.vista = tk.Label(self, bg="#f2f2f2", text="Aquí aparecerá el resultado",
                              font=("Helvetica", 14), fg="#777")
        self.vista.pack(expand=True, fill="both", padx=40, pady=10)

        self.estado = tk.Label(self, text="", font=("Helvetica", 14), bg="white", fg="#1b8a3a")
        self.estado.pack()

        self.btn_guardar = tk.Button(self, text="2. GUARDAR IMAGEN", font=fuente, height=2,
                                     bg="#1b8a3a", fg="white", activebackground="#146b2d",
                                     disabledforeground="#dddddd", state="disabled",
                                     command=self.guardar)
        self.btn_guardar.pack(fill="x", padx=40, pady=(10, 25))

    def elegir(self):
        ruta = filedialog.askopenfilename(title="Elige la imagen", filetypes=TIPOS)
        if not ruta:
            return
        try:
            with Image.open(ruta) as im:
                self.resultado = ajustar(im)
        except Exception:
            self.resultado = None
            self.btn_guardar.config(state="disabled")
            messagebox.showerror("No se pudo abrir", "No he podido leer esta imagen.\nPrueba con otra (JPG o PNG).")
            return
        self.nombre = os.path.splitext(os.path.basename(ruta))[0] + ".jpg"
        self._mostrar()
        self.estado.config(text="¡Lista! Ahora pulsa GUARDAR IMAGEN")
        self.btn_guardar.config(state="normal")

    def _mostrar(self):
        miniatura = self.resultado.copy()
        miniatura.thumbnail((360, 440))
        self._miniatura = ImageTk.PhotoImage(miniatura)
        self.vista.config(image=self._miniatura, text="")

    def guardar(self):
        if self.resultado is None:
            return
        inicio = os.path.join(os.path.expanduser("~"), "Downloads")
        ruta = filedialog.asksaveasfilename(
            title="Guardar imagen", initialdir=inicio if os.path.isdir(inicio) else None,
            initialfile=self.nombre, defaultextension=".jpg", filetypes=[("JPG", "*.jpg")])
        if not ruta:
            return
        self.resultado.save(ruta, "JPEG", quality=90, optimize=True)
        self.estado.config(text="¡Guardada!")
        messagebox.showinfo("Guardada", "La imagen se ha guardado correctamente.")


if __name__ == "__main__":
    App().mainloop()
