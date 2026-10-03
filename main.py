"""Ajustar imágenes: elige o arrastra una foto, mira el antes y el después, y guárdala (800x800)."""
import os
import queue
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageOps

from ajustar_imagen import ALTO, ANCHO, ajustar, info_producto, ruta_recurso

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAY_DND = True
except Exception:
    HAY_DND = False

TIPOS = [("Imágenes", "*.jpg *.jpeg *.png *.webp"), ("Todos los archivos", "*.*")]

FONDO, TARJETA, PAPEL = "#F6F0EB", "#FFFFFF", "#EDE5DE"
MARRON, MARRON_SUAVE = "#5B3F37", "#8C7B75"
VERDE, VERDE_OSC = "#2E8B57", "#236B43"
AMBAR, ROSA = "#B8741A", "#C9A59A"

MODOS = {"Sin mejorar": "ninguna", "Mejorar calidad": "clasica", "Mejorar con IA": "ia"}
AYUDA_MODO = {
    "ninguna": "Solo ajusta el tamaño. Es lo más fiel a la foto original.",
    "clasica": "Suaviza los cuadritos de la foto y la afina. Rápido y seguro.",
    "ia": "Reconstruye detalle con inteligencia artificial. Es más lento "
          "y puede deformar letras muy pequeñas: revisa el resultado.",
}
LADO_VISTA = 350


class App(ctk.CTk, *([TkinterDnD.DnDWrapper] if HAY_DND else [])):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        self.title("Ajustar imágenes")
        self.geometry("920x760")
        self.minsize(860, 720)
        self.configure(fg_color=FONDO)

        self.original = None       # imagen original (PIL)
        self.resultado = None      # imagen ajustada (PIL)
        self.nombre = "imagen.jpg"
        self.ocupado = False
        self.token = 0
        self.cola = queue.Queue()
        self._refs = {}
        # Imagen transparente de relleno: customtkinter falla si se le quita la imagen a una etiqueta.
        self._vacio = ctk.CTkImage(light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 0)), size=(1, 1))

        self.dnd_ok = False
        if HAY_DND:
            try:
                self.TkdndVersion = TkinterDnD._require(self)
                self.drop_target_register(DND_FILES)
                self.dnd_bind("<<Drop>>", self._soltar)
                self.dnd_ok = True
            except Exception:
                self.dnd_ok = False

        self._construir()

    # ---------- interfaz ----------
    def _construir(self):
        self.grid_columnconfigure((0, 1), weight=1, uniform="tarjetas")
        self.grid_rowconfigure(1, weight=1)

        cabecera = ctk.CTkFrame(self, fg_color="transparent")
        cabecera.grid(row=0, column=0, columnspan=2, sticky="ew", padx=30, pady=(22, 8))
        try:
            logo = Image.open(ruta_recurso(os.path.join("assets", "logo.png"))).convert("RGBA")
            self._refs["logo"] = ctk.CTkImage(light_image=logo, size=(58, 58))
            ctk.CTkLabel(cabecera, image=self._refs["logo"], text="").pack(side="left", padx=(0, 14))
        except Exception:
            pass
        textos = ctk.CTkFrame(cabecera, fg_color="transparent")
        textos.pack(side="left")
        ctk.CTkLabel(textos, text="Ajustar imágenes", font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=MARRON).pack(anchor="w")
        ctk.CTkLabel(textos, text=f"Todas las fotos salen iguales: {ANCHO}×{ALTO} px",
                     font=ctk.CTkFont(size=15), text_color=MARRON_SUAVE).pack(anchor="w")

        # Tarjeta original
        self.tarjeta_orig = self._tarjeta(0, "ANTES")
        self.vista_orig = ctk.CTkLabel(
            self.tarjeta_orig, text=self._texto_vacio(), font=ctk.CTkFont(size=17), text_color=MARRON_SUAVE,
            fg_color=PAPEL, corner_radius=14, cursor="hand2", width=LADO_VISTA, height=LADO_VISTA)
        self.vista_orig.pack(padx=18, pady=(0, 18), expand=True)
        self.vista_orig.bind("<Button-1>", lambda e: self.elegir())

        # Tarjeta resultado
        self.tarjeta_res = self._tarjeta(1, f"DESPUÉS  ({ANCHO}×{ALTO})")
        self.vista_res = ctk.CTkLabel(
            self.tarjeta_res, text="Aquí aparecerá\nel resultado", font=ctk.CTkFont(size=17),
            text_color=MARRON_SUAVE, fg_color=PAPEL, corner_radius=14, width=LADO_VISTA, height=LADO_VISTA)
        self.vista_res.pack(padx=18, pady=(0, 18), expand=True)

        # Información y mejoras
        inferior = ctk.CTkFrame(self, fg_color="transparent")
        inferior.grid(row=2, column=0, columnspan=2, sticky="ew", padx=30, pady=(6, 0))
        inferior.grid_columnconfigure(0, weight=1)

        self.info = ctk.CTkLabel(inferior, text="", font=ctk.CTkFont(size=15, weight="bold"), text_color=MARRON_SUAVE)
        self.info.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(inferior, text="¿Quieres mejorar la calidad?", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=MARRON).grid(row=1, column=0, sticky="w", pady=(10, 4))
        self.segmento = ctk.CTkSegmentedButton(
            inferior, values=list(MODOS), command=self._cambiar_modo, height=44,
            font=ctk.CTkFont(size=16, weight="bold"), selected_color=MARRON, selected_hover_color="#452F29",
            unselected_color=PAPEL, unselected_hover_color="#E2D7CE", text_color=MARRON, fg_color=PAPEL)
        self.segmento.set("Sin mejorar")
        self.segmento.grid(row=2, column=0, sticky="ew")
        self.ayuda = ctk.CTkLabel(inferior, text=AYUDA_MODO["ninguna"], font=ctk.CTkFont(size=14),
                                  text_color=MARRON_SUAVE, wraplength=820, justify="left")
        self.ayuda.grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.progreso = ctk.CTkProgressBar(inferior, progress_color=VERDE, fg_color=PAPEL, height=10)
        self.progreso.set(0)
        self.progreso.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self.progreso.grid_remove()

        # Botones
        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.grid(row=3, column=0, columnspan=2, sticky="ew", padx=30, pady=(14, 24))
        botones.grid_columnconfigure(1, weight=1)
        self.btn_elegir = ctk.CTkButton(
            botones, text="Elegir otra foto", height=58, width=230, corner_radius=14,
            font=ctk.CTkFont(size=18, weight="bold"), fg_color=TARJETA, text_color=MARRON, hover_color=PAPEL,
            border_width=2, border_color=ROSA, command=self.elegir)
        self.btn_elegir.grid(row=0, column=0, padx=(0, 14))
        self.btn_guardar = ctk.CTkButton(
            botones, text="GUARDAR IMAGEN", height=58, corner_radius=14, font=ctk.CTkFont(size=21, weight="bold"),
            fg_color=VERDE, hover_color=VERDE_OSC, text_color_disabled="#E7E0DA", state="disabled",
            command=self.guardar)
        self.btn_guardar.grid(row=0, column=1, sticky="ew")

        self._set_controles(False)

    def _tarjeta(self, col, titulo):
        marco = ctk.CTkFrame(self, fg_color=TARJETA, corner_radius=20)
        marco.grid(row=1, column=col, sticky="nsew", padx=(30, 10) if col == 0 else (10, 30), pady=8)
        ctk.CTkLabel(marco, text=titulo, font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=MARRON_SUAVE).pack(anchor="w", padx=22, pady=(16, 8))
        return marco

    def _texto_vacio(self):
        cuerpo = "Arrastra aquí tu foto\n\no haz clic para elegirla" if self.dnd_ok else "Haz clic aquí\npara elegir tu foto"
        return cuerpo

    def _set_controles(self, activos: bool):
        estado = "normal" if activos else "disabled"
        self.segmento.configure(state=estado)
        self.btn_guardar.configure(state=estado)
        self.btn_elegir.configure(state="disabled" if self.ocupado else "normal")

    # ---------- cargar ----------
    def elegir(self):
        if self.ocupado:
            return
        ruta = filedialog.askopenfilename(title="Elige la foto", filetypes=TIPOS)
        if ruta:
            self._cargar(ruta)

    def _soltar(self, evento):
        if self.ocupado:
            return
        try:
            rutas = self.tk.splitlist(evento.data)
        except Exception:
            rutas = [evento.data]
        if rutas:
            self._cargar(rutas[0])

    def _cargar(self, ruta):
        try:
            with Image.open(ruta) as im:
                im.load()
                original = im.copy()
            pw, ph, escala = info_producto(original)
        except Exception:
            messagebox.showerror("No se pudo abrir", "No he podido leer esta foto.\nPrueba con otra (JPG o PNG).")
            return
        self.original = original
        self.nombre = os.path.splitext(os.path.basename(ruta))[0] + ".jpg"
        self.segmento.set("Sin mejorar")
        self.ayuda.configure(text=AYUDA_MODO["ninguna"])

        vista = ImageOps.exif_transpose(original).convert("RGB")
        vista.thumbnail((LADO_VISTA - 10, LADO_VISTA - 10))
        self._refs["orig"] = ctk.CTkImage(light_image=vista, size=vista.size)
        self.vista_orig.configure(image=self._refs["orig"], text="")

        if escala > 1.3:
            self.info.configure(
                text=f"El producto de tu foto mide {pw}×{ph} px: es pequeño y se verá borroso. "
                     "Prueba «Mejorar calidad».", text_color=AMBAR)
        else:
            self.info.configure(text=f"El producto de tu foto mide {pw}×{ph} px: tiene buen tamaño.",
                                text_color=VERDE)
        self._procesar()

    # ---------- procesar ----------
    def _cambiar_modo(self, valor):
        self.ayuda.configure(text=AYUDA_MODO[MODOS[valor]])
        self._procesar()

    def _procesar(self):
        if self.original is None:
            return
        modo = MODOS[self.segmento.get()]
        self.token += 1
        token = self.token
        self.ocupado = True
        self.progreso.set(0)
        if modo == "ia":
            self.progreso.grid()
        self.btn_guardar.configure(state="disabled")
        self.segmento.configure(state="disabled")
        self.btn_elegir.configure(state="disabled")
        if modo != "ninguna":
            self.vista_res.configure(text="Trabajando…", image=self._vacio)

        original = self.original

        def trabajo():
            try:
                res = ajustar(original, modo, progreso=lambda f: self.cola.put(("prog", token, f)))
                self.cola.put(("ok", token, res))
            except Exception as e:
                self.cola.put(("err", token, e))

        threading.Thread(target=trabajo, daemon=True).start()
        self.after(60, self._sondear)

    def _sondear(self):
        terminado = False
        try:
            while True:
                tipo, token, dato = self.cola.get_nowait()
                if token != self.token:
                    continue
                if tipo == "prog":
                    self.progreso.set(dato)
                elif tipo == "ok":
                    self._mostrar_resultado(dato)
                    terminado = True
                elif tipo == "err":
                    self._error(dato)
                    terminado = True
        except queue.Empty:
            pass
        if not terminado and self.ocupado:
            self.after(60, self._sondear)

    def _mostrar_resultado(self, res):
        self.resultado = res
        self.ocupado = False
        self.progreso.grid_remove()
        lado = LADO_VISTA - 10
        vista = res.resize((lado, lado), Image.LANCZOS)
        self._refs["res"] = ctk.CTkImage(light_image=vista, size=(lado, lado))
        self.vista_res.configure(image=self._refs["res"], text="")
        self._set_controles(True)

    def _error(self, e):
        self.ocupado = False
        self.progreso.grid_remove()
        self.vista_res.configure(text="No se pudo\nmejorar esta foto", image=self._vacio)
        self._set_controles(False)
        self.segmento.configure(state="normal")
        messagebox.showerror("Algo ha fallado", f"No he podido procesar la foto.\n\n{e}")

    # ---------- guardar ----------
    def guardar(self):
        if self.resultado is None or self.ocupado:
            return
        inicio = os.path.join(os.path.expanduser("~"), "Downloads")
        ruta = filedialog.asksaveasfilename(
            title="Guardar imagen", initialdir=inicio if os.path.isdir(inicio) else None,
            initialfile=self.nombre, defaultextension=".jpg", filetypes=[("JPG", "*.jpg")])
        if not ruta:
            return
        self.resultado.save(ruta, "JPEG", quality=92, optimize=True)
        messagebox.showinfo("Guardada", "La imagen se ha guardado correctamente.")


if __name__ == "__main__":
    App().mainloop()
