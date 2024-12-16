import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageEnhance
import subprocess
import os,re
import pygetwindow as gw
import time
import pyautogui
from music21 import converter, stream


# VARIABLES GLOBALS
nom_imatge = None
original_image = None
current_image = None
retall_lines = []
current_rectangle = None
rectangle_y = 100
rectangle_height = 50  # Altura inicial del rectangle
current_line_index = 0  # Índex inicial per a la navegació
viewing_retall = False  # Indica si s'està visualitzant una línia retallada

# Variables per al zoom i el drag
zoom_level = 1.0  # Nivell inicial de zoom
drag_data = {"x": 0, "y": 0, "image_offset": (0, 0)}

def obrir_imatge():
    global nom_imatge
    file_path = filedialog.askopenfilename(filetypes=[("Arxius d'imatge", "*.png;*.jpg;*.jpeg")])
    nom_imatge = os.path.splitext(os.path.basename(file_path))[0]  #Agafem el nom de la imatge oberta per tractaments en altres funcions

    if file_path:
        carregar_imatge(file_path)
        obrir_musescore(file_path)

 
def carregar_imatge(path):
    global original_image, current_image, retall_lines, rectangle_y, viewing_retall, rectangle_height
    try:
        original_image = Image.open(path)
        original_image.thumbnail((700, 450))
        current_image = original_image.copy()
        retall_lines = []
        rectangle_y = 100
        rectangle_height = 50
        viewing_retall = False
        mostrar_imatge(current_image)
    except Exception as e:
        print(f"Error carregant la imatge: {e}")

def mostrar_imatge(image):
    img = ImageTk.PhotoImage(image)
    image_label.config(image=img)
    image_label.image = img


def obrir_musescore(path):
    # Extraer la carpeta base y el nombre del archivo
    base_folder = os.path.dirname(path)
    musescore_folder = os.path.join(base_folder, "MUSICXML")
    base_name = os.path.splitext(os.path.basename(path))[0]

    # Validar que exista la carpeta MUSESCORE
    if not os.path.exists(musescore_folder):
        messagebox.showinfo("Información", f"No se encontró la carpeta en {base_folder}.")
        return

    # Crear un patrón para buscar las partituras en la carpeta MUSESCORE
    pattern = re.compile(rf"^{re.escape(base_name)}\.\d{{2}}\.musicxml$")
    partituras = [
        os.path.join(musescore_folder, file)
        for file in os.listdir(musescore_folder)
        if pattern.match(file)
    ]

    if not partituras:
        messagebox.showinfo("Información", "No se encontraron archivos de partituras asociados.")
        return

    # Ejecutar MuseScore con las partituras encontradas, DESACTIVAT PER DEBUGAR!
    executar_musescore(partituras) #IMPORTANT

def executar_musescore(lista_archivos):
    # Ruta al ejecutable de MuseScore
    musescore_path = "C:/Program Files/MuseScore 4/bin/MuseScore4.exe"
    for archivo in lista_archivos:
        subprocess.Popen([musescore_path, archivo]) 



def guardar_musescore():
    """
    Busca todas las ventanas de MuseScore que contienen el nombre de la imagen seguido de .musicxml
    en cualquier parte del título y simula un 'Ctrl + S' en cada una para guardar el archivo.
    """
    # Obtener el nombre de la imagen sin la extensión
    nombre_imagen_sin_extension = os.path.splitext(os.path.basename(nom_imatge))[0]
    
    # Expresión regular para buscar el nombre base de la imagen seguido de .musicxml
    patron = re.compile(rf".*{re.escape(nombre_imagen_sin_extension)}.*\.musicxml")
    
    # Filtrar las ventanas que contienen el patrón en el título
    ventanas_musescore = [
        ventana for ventana in gw.getWindowsWithTitle("") 
        if patron.match(ventana.title)
    ]
    
    # Comprobar si se han encontrado ventanas que coinciden
    if ventanas_musescore:
        for ventana in ventanas_musescore:
            # Activar la ventana
            ventana.activate()
            time.sleep(1)  # Esperar un segundo para asegurar que la ventana está activa
            
            # Simular 'Ctrl + S' para guardar el archivo
            pyautogui.hotkey('ctrl', 's')
            time.sleep(1)  # Esperar un poco para asegurar que el comando se haya ejecutado
            print(f"Archivo '{ventana.title}' guardado correctamente.")
    else:
        print(f"No se encontraron ventanas de MuseScore con el archivo que contiene '{nombre_imagen_sin_extension}.musicxml'.")




def draw_rectangle():
    global current_image, current_rectangle
    if current_image and current_rectangle:
        image_with_rectangle = current_image.copy()
        draw = ImageDraw.Draw(image_with_rectangle)
        draw.rectangle(current_rectangle, outline="red", width=2)
        mostrar_imatge(image_with_rectangle)

def activar_desactivar_marca():
    return None       

def ajustar_rectangle(delta_y):
    global rectangle_y, rectangle_height, current_rectangle
    if current_image:
        rectangle_y = max(0, min(current_image.height - rectangle_height, rectangle_y + delta_y))
        current_rectangle = (0, rectangle_y, current_image.width, rectangle_y + rectangle_height)
        draw_rectangle()

def ajustar_rectangle_personalitzat(event=None):
    global rectangle_y, rectangle_height, current_rectangle
    if current_image:
        try:
            new_height = int(size_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Si us plau, introdueix un valor numèric.")
            return
        rectangle_height = max(1, min(current_image.height, new_height))
        rectangle_y = max(0, min(current_image.height - rectangle_height, rectangle_y))
        current_rectangle = (0, rectangle_y, current_image.width, rectangle_y + rectangle_height)
        draw_rectangle()     

def retallar():
    global current_rectangle, retall_lines
    if current_rectangle and original_image:
        x1, y1, x2, y2 = current_rectangle

        displayed_width, displayed_height = current_image.size
        original_width, original_height = original_image.size
        scale_x = original_width / displayed_width
        scale_y = original_height / displayed_height
        x1 = int(x1 * scale_x)
        y1 = int(y1 * scale_y)
        x2 = int(x2 * scale_x)
        y2 = int(y2 * scale_y)

        cropped = original_image.crop((x1, y1, x2, y2))
        retall_lines.append(cropped)
        messagebox.showinfo("Retall", f"L\u00ednia retallada i afegida. Total l\u00ednies: {len(retall_lines)}")

def eliminar_ultim_retall():
    global retall_lines, current_image
    if retall_lines:
        # Eliminar l'últim retall
        retall_lines.pop()
        if retall_lines:
            # Mostrar el penúltim retall
            current_image = retall_lines[-1].copy()
            mostrar_imatge(current_image)
            messagebox.showinfo("Retall eliminat", f"S'ha eliminat l'últim retall. Queden {len(retall_lines)} línies.")
        else:
            # Si no queden retalls, mostrar la imatge original
            current_image = original_image.copy()
            mostrar_imatge(current_image)
            messagebox.showinfo("Retalls eliminats", "No queden línies retallades.")
    else:
        messagebox.showwarning("Error", "No hi ha cap línia retallada per eliminar.")     

def navegar(direccio):
    global current_line_index, viewing_retall, current_image
    if not retall_lines:
        messagebox.showwarning("Navegaci\u00f3", "No hi ha l\u00ednies retallades.")
        return

    if direccio == "prev":
        current_line_index = (current_line_index - 1) % len(retall_lines)
    elif direccio == "next":
        current_line_index = (current_line_index + 1) % len(retall_lines)

    viewing_retall = True
    current_image = retall_lines[current_line_index].copy()
    mostrar_imatge(current_image)

    #Actualitzar la etiqueta con el índice de la línea actual.
    line_counter_label.config(text=f"Línia: {current_line_index + 1} / {len(retall_lines)}")
    activar_linea_actual_musescore(current_line_index)

def activar_linea_actual_musescore(linea_actual):
    """
    Activa la finestra de MuseScore que conte el nom del archiu .musicxml corresponent a la línea actual.
    """
    # Generar el título del archivo .musicxml con el índice correspondiente
    ventana_buscar = f"{nom_imatge}.{str(linea_actual+1).zfill(2)}.musicxml"   #EN nom_imatge esta EL NOM DE LA FOTO ACTUAL!
    
    # Filtrar las ventanas que contienen el título generado
    ventanas_musescore = [
        ventana for ventana in gw.getWindowsWithTitle("") if ventana.title == ventana_buscar
    ]
    
    # Comprobar si el índice linea_actual existe en la lista de ventanas
    if ventanas_musescore:
        ventana = ventanas_musescore[0]  # Solo debe haber una ventana con este título exacto
        ventana.activate()  # Activa la ventana
        print(f"Ventana '{ventana.title}' activada correctamente.")
    else:
        print(f"No se encontró la ventana para {ventana_buscar}. Revisa manualmente.")
    
    # Per debugar podem mirar totes les finestres que trobem amb el GW: print("Ventanas detectadas:", [ventana.title for ventana in gw.getWindowsWithTitle("")])


def tornar_a_imatge_completa():
    global viewing_retall, current_image
    if original_image:
        viewing_retall = False
        current_image = original_image.copy()
        mostrar_imatge(current_image)
        line_counter_label.config(text="Línia: 0")


def ajustar_brillo(value):
    global original_image, current_image, viewing_retall, retall_lines, current_line_index
    if original_image:
        brightness_factor = float(value) / 50

        if viewing_retall and retall_lines:
            # Sempre treballar amb una còpia de l'original del retall actual
            original_cropped = retall_lines[current_line_index].copy()
            enhancer = ImageEnhance.Brightness(original_cropped)
            adjusted_cropped = enhancer.enhance(brightness_factor)
            mostrar_imatge(adjusted_cropped)
        else:
            # Ajustar la imatge completa
            enhancer = ImageEnhance.Brightness(original_image)
            current_image = enhancer.enhance(brightness_factor)
            mostrar_imatge(current_image)

# FUNCIONS PER FER FUNCIONAR EL ZOOM AND DRAG

def aplicar_zoom(event):
    global zoom_level, viewing_retall
    if viewing_retall:  # Només permet fer zoom si estàs visualitzant un retall
        if event.delta > 0:
            zoom_level = min(zoom_level + 0.1, 3.0)
        elif event.delta < 0:
            zoom_level = max(zoom_level - 0.1, 0.6)
        actualizar_zoom_drag()
    else:
        messagebox.showinfo("Zoom", "De moment el zoom només està disponible en mode de retall!")

def iniciar_drag(event):
    drag_data["x"] = event.x
    drag_data["y"] = event.y

def mover_imagen(event):
    dx = event.x - drag_data["x"]
    dy = event.y - drag_data["y"]
    drag_data["x"] = event.x
    drag_data["y"] = event.y
    offset_x, offset_y = drag_data["image_offset"]
    drag_data["image_offset"] = (offset_x + dx, offset_y + dy)
    actualizar_zoom_drag()

def actualizar_zoom_drag():
    global zoom_level, drag_data, retall_lines, current_line_index
    if retall_lines:
        cropped = retall_lines[current_line_index]
        width, height = cropped.size
        zoomed_image = cropped.resize((int(width * zoom_level), int(height * zoom_level)), Image.Resampling.LANCZOS)
        canvas_width, canvas_height = image_label.winfo_width(), image_label.winfo_height()
        offset_x, offset_y = drag_data["image_offset"]
        centered_image = Image.new("RGBA", (canvas_width, canvas_height), (44, 44, 60, 255))
        centered_image.paste(zoomed_image, (offset_x, offset_y))
        mostrar_imatge(centered_image)


def unificar_musicxml(self):
    global imagen_actual_base  # Usar la variable global
    # Ruta fija de la carpeta donde están los archivos .musicxml
    musescore_folder = r"C:\Users\abel\Desktop\UNI\TFG\exemplesMusicXML\exemplesMusicXML\CVCDOL.S01P01\MUSICXML"

    # Verificar si la carpeta MUSESCORE existe
    if not os.path.exists(musescore_folder):
        messagebox.showinfo("Información", f"No se encontró la carpeta MUSICXML en {musescore_folder}.")
        return

    # Buscar archivos .musicxml en la carpeta MUSESCORE que coincidan con el nombre base
    archivos_xml = [
        os.path.join(musescore_folder, file)
        for file in os.listdir(musescore_folder)
        if file.endswith(".musicxml") and file.startswith(imagen_actual_base)
    ]

    # Si no se encontraron archivos MusicXML
    if not archivos_xml:
        messagebox.showinfo("Información", "No se encontraron archivos MusicXML para unificar.")
        return

    # Crear un flujo vacío donde se añadirán las partituras
    partitura_unida = stream.Score()

    # Iterar sobre cada archivo y agregar su contenido al flujo
    for archivo in archivos_xml:
        try:
            partitura = converter.parse(archivo)  # Cargar el archivo MusicXML
            partitura_unida.append(partitura)    # Añadir al flujo
        except Exception as e:
            messagebox.showwarning("Error", f"No se pudo procesar {archivo}: {str(e)}")

    # Guardar el archivo combinado
    output_path = os.path.join(musescore_folder, "partitura_unida.musicxml")
    output_path = os.path.normpath(output_path)  # Normalizar ruta de salida

    try:
        partitura_unida.write('musicxml', fp=output_path)
        messagebox.showinfo("Éxito", f"Archivos unidos y guardados como '{output_path}'")
    except Exception as e:
        messagebox.showwarning("Error", f"No se pudo guardar la partitura unificada: {str(e)}")




##########################################################################################################################################
##########################################################################################################################################
##################################        CREACIÓ INTERFÍCIE PRINCIPAL      ##############################################################
##########################################################################################################################################
##########################################################################################################################################

root = tk.Tk()
root.title("Gestor de Partitures - TFG")
root.geometry("900x900")
root.configure(bg="#1f1f2e")

# Mantenir la finestra en primer pla
root.attributes("-topmost", True)

# Afegir botó per alternar primer pla
def toggle_on_top():
    # Obtener el estado actual de la ventana (si está en primer plano o no)
    current_state = root.attributes("-topmost")
    # Cambiar el estado de la ventana
    new_state = not current_state
    root.attributes("-topmost", new_state)
    # Mostrar un mensaje al usuario con el nuevo estado
    if new_state:
        messagebox.showinfo("Estado de ventana", "La ventana está ahora en primer plano.")
    else:
        messagebox.showinfo("Estado de ventana", "La ventana ya no está en primer plano.")

style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Arial", 12), background="#6c63ff", foreground="white", padding=6)
style.map("TButton", background=[("active", "#5548c8")])
style.configure("TFrame", background="#1f1f2e")

root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

title_label = tk.Label(root, text="\ud83c\udfb5 Gestor de Partitures \ud83c\udfb5", font=("Arial", 32, "bold"), bg="#1f1f2e", fg="#f4a261")
title_label.grid(row=0, column=0, pady=20, sticky="ew")

main_frame = ttk.Frame(root, style="TFrame")
main_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=1)

brightness_frame = ttk.Frame(main_frame, style="TFrame")
brightness_frame.grid(row=0, column=0, sticky="ns")
brightness_label = tk.Label(brightness_frame, text="Brillantor", bg="#1f1f2e", fg="white", font=("Arial", 12))
brightness_label.pack()
brightness_scale = ttk.Scale(brightness_frame, from_=0, to=100, orient=tk.VERTICAL, command=ajustar_brillo, length=240)
brightness_scale.set(50)
brightness_scale.pack(pady=50)

image_frame = ttk.Frame(main_frame, style="TFrame")
image_frame.grid(row=0, column=1, sticky="nsew")
image_frame.grid_rowconfigure(0, weight=1)
image_frame.grid_columnconfigure(0, weight=1)
image_label = tk.Label(image_frame, bg="#2c2c3c", relief=tk.RIDGE, borderwidth=5, width=900, height=700)  # TAMANY DE LES IMATGES EDITABLE PER ALT I AMPLE
image_label.grid(row=0, column=0, sticky="nsew")

menu_bar = tk.Menu(root)
file_menu = tk.Menu(menu_bar, tearoff=0, bg="#2c2c3c", fg="white", activebackground="#6c63ff")
file_menu.add_command(label="Obrir", command=obrir_imatge)
file_menu.add_command(label="Guardar", command=guardar_musescore)
file_menu.add_separator()
file_menu.add_command(label="Sortir", command=root.quit)
menu_bar.add_cascade(label="Arxiu", menu=file_menu)

edit_menu = tk.Menu(menu_bar, tearoff=0, bg="#2c2c3c", fg="white", activebackground="#6c63ff")
edit_menu.add_command(label="Retallar", command=retallar)
menu_bar.add_cascade(label="Editar", menu=edit_menu)

help_menu = tk.Menu(menu_bar, tearoff=0, bg="#2c2c3c", fg="white", activebackground="#6c63ff")
help_menu.add_command(label="Sobre", command=lambda: print("Gestor de Partitures v1.0"))
menu_bar.add_cascade(label="Ajuda", menu=help_menu)

root.config(menu=menu_bar)

menu_frame = ttk.Frame(root, style="TFrame")
menu_frame.grid(row=2, column=0, pady=10, sticky="nsew")

# Sección: Recorte
crop_section = ttk.Frame(menu_frame, style="TFrame")
crop_section.pack(fill="x", pady=10)
crop_label = tk.Label(crop_section, text="Retalls", bg="#1f1f2e", fg="white", font=("Arial", 14, "bold"))
crop_label.pack(anchor="w", pady=5)
adjust_up_button = ttk.Button(crop_section, text="\u25b2", command=lambda: ajustar_rectangle(-5))
adjust_up_button.pack(side=tk.LEFT, padx=5)
adjust_down_button = ttk.Button(crop_section, text="\u25bc", command=lambda: ajustar_rectangle(5))
adjust_down_button.pack(side=tk.LEFT, padx=5)
size_label = tk.Label(crop_section, text="Mida Retall:", bg="#1f1f2e", fg="white", font=("Arial", 12,"bold"))
size_label.pack(side=tk.LEFT, padx=5)
size_entry = ttk.Entry(crop_section, width=5)
size_entry.insert(0, "50")  # Valor per defecte
size_entry.pack(side=tk.LEFT, padx=5)
size_entry.bind("<Return>", ajustar_rectangle_personalitzat)  # Activarse al fer enter de la mida per teclat.
adjust_custom_button = ttk.Button(crop_section, text="Aplica mida", command=ajustar_rectangle_personalitzat)
adjust_custom_button.pack(side=tk.LEFT, padx=5)
retallar_button = ttk.Button(crop_section, text="Retallar", command=retallar)
retallar_button.pack(side=tk.LEFT, padx=5)
retallar_button = ttk.Button(crop_section, text="Eliminar retall", command=eliminar_ultim_retall)
retallar_button.pack(side=tk.LEFT, padx=5)

# Sección: Acciones generales
general_section = ttk.Frame(menu_frame, style="TFrame")
general_section.pack(fill="x", pady=10)
general_label = tk.Label(general_section, text="General", bg="#1f1f2e", fg="white", font=("Arial", 14, "bold"))
general_label.pack(anchor="w", pady=5)
open_button = ttk.Button(general_section, text="Obrir", command=obrir_imatge)
open_button.pack(side=tk.LEFT, padx=5)
save_button = ttk.Button(general_section, text="Guardar", command=guardar_musescore)
save_button.pack(side=tk.LEFT, padx=5)
unite_button = ttk.Button(general_section, text="Unir", command=lambda: print("Funcionalitat d'unir no implementada"))
unite_button.pack(side=tk.LEFT, padx=5)

# Sección: Navegación
nav_section = ttk.Frame(menu_frame, style="TFrame")
nav_section.pack(fill="x", pady=10)
nav_label = tk.Label(nav_section, text="Navegació", bg="#1f1f2e", fg="white", font=("Arial", 14, "bold"))
nav_label.pack(anchor="w", pady=5)
reset_button = ttk.Button(nav_section, text="Imatge Completa", command=tornar_a_imatge_completa)
reset_button.pack(side=tk.LEFT, padx=5)
prev_button = ttk.Button(nav_section, text="\u2190", command=lambda: navegar("prev"))
prev_button.pack(side=tk.LEFT, padx=2)
line_counter_label = tk.Label(nav_section, text="Línia: 0", bg="#1f1f2e", fg="white", font=("Arial", 12,"bold"))
line_counter_label.pack(side=tk.LEFT, padx=10)
next_button = ttk.Button(nav_section, text="\u2192", command=lambda: navegar("next"))
next_button.pack(side=tk.LEFT, padx=2)
toggle = ttk.Button(nav_section, text="Primer pla", command=toggle_on_top)
toggle.pack(side=tk.LEFT, padx=5)


#  marca
mark_button = ttk.Button(nav_section, text="Posar Marca", command=activar_desactivar_marca)
mark_button.pack(side=tk.LEFT, padx=5)

# TEMA ZOOM
image_label.bind("<MouseWheel>", aplicar_zoom)
image_label.bind("<ButtonPress-1>", iniciar_drag)
image_label.bind("<B1-Motion>", mover_imagen)

image_label.bind("<Button-4>", lambda e: aplicar_zoom(type("Event", (object,), {"delta": 120})()))
image_label.bind("<Button-5>", lambda e: aplicar_zoom(type("Event", (object,), {"delta": -120})()))

root.mainloop()


