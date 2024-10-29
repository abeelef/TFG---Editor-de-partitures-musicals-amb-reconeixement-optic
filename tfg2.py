import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import ImageTk, Image, ImageDraw
import pymongo
from datetime import datetime
import pyautogui
import pygetwindow as gw
import time

class PartituraApp:
    def __init__(self, ruta_musicxml):
        self.ruta_musicxml = ruta_musicxml
        self.recortes = []
        self.compas_actual = 0
        self.seleccionando = False
        self.start_x = self.start_y = 0
        self.end_x = self.end_y = 0
        self.factor_escala = 1.0
        self.zoom_step = 0.1
        self.max_width = 800
        self.max_height = 600
        self.imagen_original = None  # Inicializa la imagen original como None

    # Conectar a MongoDB
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["partituras_tfg"]
        self.partituras_collection = self.db["partituras"]


        self.cargar_imagen()
        self.crear_interfaz()

    def cargar_imagen(self):
        ruta_imagen = filedialog.askopenfilename(title="Seleccionar imagen", filetypes=[("Archivos de imagen", "*.jpg;*.jpeg;*.png")])
        if not ruta_imagen:
            messagebox.showwarning("Advertencia", "No se ha seleccionado ninguna imagen.")
            return
        if hasattr(self, 'imagen_actual') and self.imagen_actual == ruta_imagen:
            messagebox.showinfo("Aviso", "Ya estás analizando esta imagen.")
            return
        self.imagen_actual = ruta_imagen
        self.recortes = []
        self.compas_actual = 0
        self.imagen_original = Image.open(self.imagen_actual)

        # Guardar la imagen y el archivo MusicXML en MongoDB
        self.guardar_partitura_mongodb()
        print(self.ruta_musicxml)
        executar_musescore(self.ruta_musicxml)


    def guardar_partitura_mongodb(self):
        # Crear documento para MongoDB
        partitura_data = {
            "titulo": "Sinfonía No. 9",  # Cambia este título según la partitura
            "archivo_xml": self.ruta_musicxml,
            "imagen_partitura": self.imagen_actual,
            "fecha_creacion": datetime.now()
        }
        # Insertar en la base de datos
        self.partituras_collection.insert_one(partitura_data)
        print("Partitura guardada en MongoDB:", partitura_data)    

    def crear_interfaz(self):
        self.ventana = tk.Tk()
        self.ventana.title("Partitura manuscrita")
        self.ventana.attributes('-topmost', True)

        self.mostrar_imagen()

        self.ventana.bind("<MouseWheel>", self.ajustar_zoom)

        button_frame = tk.Frame(self.ventana)
        button_frame.pack(side="bottom", fill="x", pady=10)

        tk.Button(button_frame, text="Cargar Imagen", command=self.cargar_imagen).pack(side="left", padx=5)
        tk.Button(button_frame, text="Confirmar Recorte", command=self.confirmar_recorte).pack(side="left", padx=5)
        tk.Button(button_frame, text="Mostrar compases recortados", command=self.mostrar_compases).pack(side="left", padx=5)
        tk.Button(button_frame, text="Volver a imagen completa", command=self.ver_imagen_completa).pack(side="left", padx=5)
        tk.Button(button_frame, text="Siguiente compás", command=self.siguiente_compas).pack(side="right", padx=5)
        tk.Button(button_frame, text="Compás anterior", command=self.compas_anterior).pack(side="right", padx=5)

        self.label_numero_compas = tk.Label(self.ventana, text="Compás: 0")
        self.label_numero_compas.pack(side="bottom", pady=5)

        self.ventana.mainloop()

    def mostrar_imagen(self):
        if self.imagen_original is None:
            return  # Asegúrate de que la imagen original esté cargada

        width_ratio = self.max_width / self.imagen_original.width
        height_ratio = self.max_height / self.imagen_original.height
        self.factor_escala = min(width_ratio, height_ratio, self.factor_escala)
        
        img_resized = self.imagen_original.resize(
            (int(self.imagen_original.width * self.factor_escala), int(self.imagen_original.height * self.factor_escala))
        )
        self.img_tk = ImageTk.PhotoImage(img_resized)

        if hasattr(self, 'panel'):
            self.panel.config(image=self.img_tk)
        else:
            self.panel = tk.Label(self.ventana, image=self.img_tk)
            self.panel.pack(side="top", fill="both", expand="yes")

        self.panel.bind("<ButtonPress-1>", self.iniciar_seleccion)
        self.panel.bind("<B1-Motion>", self.arrastrar_seleccion)
        self.panel.bind("<ButtonRelease-1>", self.finalizar_seleccion)

    def ajustar_zoom(self, event):
        if event.delta > 0:
            self.factor_escala += self.zoom_step
        elif event.delta < 0 and self.factor_escala > self.zoom_step:
            self.factor_escala -= self.zoom_step
        self.mostrar_imagen()

    def iniciar_seleccion(self, event):
        self.seleccionando = True
        self.start_x = event.x
        self.start_y = event.y
        self.end_x = event.x
        self.end_y = event.y

    def arrastrar_seleccion(self, event):
        if self.seleccionando:
            self.end_x = event.x
            self.end_y = event.y
            self.actualizar_seleccion()

    def finalizar_seleccion(self, event):
        if self.seleccionando:
            self.end_x = event.x
            self.end_y = event.y
            self.seleccionando = False

    def actualizar_seleccion(self):
        img_resized = self.imagen_original.resize(
            (int(self.imagen_original.width * self.factor_escala), int(self.imagen_original.height * self.factor_escala))
        )
        draw = ImageDraw.Draw(img_resized)
        draw.rectangle([self.start_x, self.start_y, self.end_x, self.end_y], outline="red", width=2)
        self.img_tk = ImageTk.PhotoImage(img_resized)
        self.panel.config(image=self.img_tk)

    def confirmar_recorte(self):
        x1 = int(self.start_x / self.factor_escala)
        y1 = int(self.start_y / self.factor_escala)
        x2 = int(self.end_x / self.factor_escala)
        y2 = int(self.end_y / self.factor_escala)

        recorte = self.imagen_original.crop((x1, y1, x2, y2))
        self.recortes.append(recorte)
        self.compas_actual = len(self.recortes) - 1
        self.label_numero_compas.config(text=f"Compás: {self.compas_actual + 1}")
        self.ver_imagen_completa()

    def mostrar_compases(self):
        if not self.recortes:
            messagebox.showinfo("Aviso", "No hay compases recortados.")
            return
        self.compas_actual = 0
        self.mostrar_compas_actual()

    def mostrar_compas_actual(self):
        recorte_resized = self.recortes[self.compas_actual].resize((500, 500))
        recorte_tk = ImageTk.PhotoImage(recorte_resized)
        self.panel.config(image=recorte_tk)
        self.panel.image = recorte_tk
        self.label_numero_compas.config(text=f"Compás: {self.compas_actual + 1}")

    def siguiente_compas(self):
        if self.compas_actual < len(self.recortes) - 1:
            self.compas_actual += 1
            self.mostrar_compas_actual()
        else:
            messagebox.showinfo("Aviso", "Este es el último compás.")

    def compas_anterior(self):
        if self.compas_actual > 0:
            self.compas_actual -= 1
            self.mostrar_compas_actual()
        else:
            messagebox.showinfo("Aviso", "Este es el primer compás.")

    def ver_imagen_completa(self):
        self.factor_escala = min(self.max_width / self.imagen_original.width, self.max_height / self.imagen_original.height)
        self.mostrar_imagen()
        self.label_numero_compas.config(text="Imagen completa")

def executar_musescore(archivo_musicxml):
    musescore_path = "C:/Program Files/MuseScore 4/bin/MuseScore4.exe"
    subprocess.Popen([musescore_path, archivo_musicxml])

if __name__ == "__main__":
    archivo_musicxml = "C:/Users/abel/Desktop/UNI/TFG/editor_partituras/TFG/prova.musicxml"
    app = PartituraApp(archivo_musicxml)
