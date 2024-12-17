import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageEnhance
import subprocess, os, re, time, pyautogui
import pygetwindow as gw
from music21 import converter, stream

# VARIABLES GLOBALS
# Variables per emmagatzemar l'estat de la imatge i retalls
nom_imatge = None  # Nom de l'arxiu d'imatge seleccionat
original_image = None  # Imatge original carregada
current_image = None  # Imatge actual mostrada
retall_lines = []  # Llista per guardar línies retallades
current_rectangle = None  # Coordenades del rectangle de retall
rectangle_y = 100  # Posició vertical inicial del rectangle
rectangle_height = 50  # Alçada inicial del rectangle
current_line_index = 0  # Índex de la línia actual per navegar
viewing_retall = False  # Estat: True si s'està visualitzant un retall

# Variables per al zoom i el drag (arrossegar)
zoom_level = 1.0  # Nivell inicial de zoom
drag_data = {"x": 0, "y": 0, "image_offset": (0, 0)}  # Informació de l'estat del drag


def obrir_imatge():
    """
    Obre una finestra de diàleg per seleccionar una imatge.
    Carrega la imatge seleccionada i obre els fitxers de MuseScore corresponents.
    """
    global nom_imatge
    # Obre un diàleg per seleccionar arxius d'imatge
    file_path = filedialog.askopenfilename(filetypes=[("Arxius d'imatge", "*.png;*.jpg;*.jpeg")])
    nom_imatge = os.path.splitext(os.path.basename(file_path))[0]  # Guarda el nom de la imatge sense extensió

    if file_path:
        carregar_imatge(file_path)  # Carrega la imatge seleccionada
        obrir_musescore(file_path)  # Obre MuseScore amb els fitxers relacionats


def carregar_imatge(path):
    """
    Carrega la imatge seleccionada i inicialitza l'estat de la interfície.
    """
    global original_image, current_image, retall_lines, rectangle_y, viewing_retall, rectangle_height
    try:
        # Carregar la imatge i generar-ne una còpia
        original_image = Image.open(path)
        original_image.thumbnail((700, 450))  # Redueix la mida de la imatge
        current_image = original_image.copy()
        
        # Restablir variables globals
        retall_lines = []
        rectangle_y = 100
        rectangle_height = 50
        viewing_retall = False
        
        mostrar_imatge(current_image)  # Mostra la imatge carregada en la interfície
    except Exception as e:
        print(f"Error carregant la imatge: {e}")


def mostrar_imatge(image):
    """
    Mostra la imatge proporcionada en l'etiqueta d'imatge (Tkinter).
    """
    img = ImageTk.PhotoImage(image)
    image_label.config(image=img)
    image_label.image = img


def obrir_musescore(path):
    """
    Busca fitxers .musicxml a la carpeta MUSICXML i obre'ls amb MuseScore.
    """
    # Obtenir el directori base de l'arxiu seleccionat
    base_folder = os.path.dirname(path)
    musescore_folder = os.path.join(base_folder, "MUSICXML")
    base_name = os.path.splitext(os.path.basename(path))[0]  # Nom base sense extensió

    # Verifica si la carpeta MUSICXML existeix
    if not os.path.exists(musescore_folder):
        messagebox.showinfo("Información", f"No se encontró la carpeta en {base_folder}.")
        return

    # Genera un patró regex per trobar els fitxers que coincideixin
    pattern = re.compile(rf"^{re.escape(base_name)}\.\d{{2}}\.musicxml$")
    partituras = [
        os.path.join(musescore_folder, file)
        for file in os.listdir(musescore_folder)
        if pattern.match(file)  # Coincideix amb el patró de fitxers
    ]

    if not partituras:
        messagebox.showinfo("Información", "No se encontraron archivos de partituras asociados.")
        return

    # Obre MuseScore amb les partitures trobades
    executar_musescore(partituras)


def executar_musescore(lista_archivos):
    """
    Obre els arxius MusicXML en MuseScore.
    """
    musescore_path = "C:/Program Files/MuseScore 4/bin/MuseScore4.exe"  # Ruta fixa de MuseScore
    for archivo in lista_archivos:
        subprocess.Popen([musescore_path, archivo])  # Executa MuseScore amb l'arxiu seleccionat


def guardar_musescore():
    """
    Guarda els arxius MusicXML oberts a MuseScore simulant la combinació de tecles 'Ctrl + S'.
    """
    nombre_imagen_sin_extension = os.path.splitext(os.path.basename(nom_imatge))[0]
    patron = re.compile(rf".*{re.escape(nombre_imagen_sin_extension)}.*\.musicxml")

    # Busca finestres de MuseScore amb el patró indicat
    ventanas_musescore = [
        ventana for ventana in gw.getWindowsWithTitle("")
        if patron.match(ventana.title)
    ]
    if ventanas_musescore:
        for ventana in ventanas_musescore:
            ventana.activate()  # Activa la finestra
            time.sleep(1)  # Espera un segon per assegurar la finestra activa
            pyautogui.hotkey('ctrl', 's')  # Simula 'Ctrl + S'
            time.sleep(1)
            print(f"Archivo '{ventana.title}' guardado correctamente.")
    else:
        print(f"No se encontraron ventanas de MuseScore con el archivo que contiene '{nombre_imagen_sin_extension}.musicxml'.")


def draw_rectangle():
    """
    Dibuixa un rectangle a la imatge actual basat en les coordenades globals.
    """
    global current_image, current_rectangle
    if current_image and current_rectangle:
        image_with_rectangle = current_image.copy()
        draw = ImageDraw.Draw(image_with_rectangle)
        draw.rectangle(current_rectangle, outline="red", width=2)  # Dibuixa el rectangle
        mostrar_imatge(image_with_rectangle)


def ajustar_rectangle(delta_y):
    """
    Ajusta la posició vertical del rectangle segons l'increment donat (delta_y).
    """
    global rectangle_y, rectangle_height, current_rectangle
    if current_image:
        rectangle_y = max(0, min(current_image.height - rectangle_height, rectangle_y + delta_y))
        current_rectangle = (0, rectangle_y, current_image.width, rectangle_y + rectangle_height)
        draw_rectangle()  # Actualitza el rectangle a la imatge


def ajustar_rectangle_personalitzat(event=None):
    '''
    Ajusta les dimensions del rectangle de retall segons el valor especificat per l'usuari.

    Paràmetres:
        event: Opcional. Esdeveniment que pot activar la funció (per exemple, prement Enter).

    Funcionament:
    - Llegeix el valor introduït pel camp de text "size_entry".
    - Comprova si el valor és un número vàlid. Si no, mostra un missatge d'error.
    - Ajusta l'alçada del rectangle de retall dins dels límits de la imatge actual.
    - Redibuixa el rectangle a la posició actualitzada.
    '''
    global rectangle_y, rectangle_height, current_rectangle  # Variables globals per gestionar el rectangle

    if current_image:  # Comprovar que existeixi una imatge carregada
        try:
            # Obtenir el valor introduït a size_entry i convertir-lo a enter
            new_height = int(size_entry.get())
        except ValueError:
            # Si el valor no és numèric, mostrar un missatge d'error
            messagebox.showerror("Error", "Si us plau, introdueix un valor numèric.")
            return  # Aturar l'execució de la funció

        # Ajustar l'alçada del rectangle, assegurant que es manté dins dels límits de la imatge
        rectangle_height = max(1, min(current_image.height, new_height))
        # Ajustar la posició Y del rectangle dins de la imatge
        rectangle_y = max(0, min(current_image.height - rectangle_height, rectangle_y))
        # Actualitzar les coordenades del rectangle (X inicial, Y inicial, amplada, Y final)
        current_rectangle = (0, rectangle_y, current_image.width, rectangle_y + rectangle_height)
        # Redibuixar el rectangle amb les noves dimensions
        draw_rectangle()

def retallar():
    """
    Retalla la part de la imatge dins del rectangle actual i l'afegeix a la llista de línies retallades.
    """
    global current_rectangle, retall_lines
    if current_rectangle and original_image:
        x1, y1, x2, y2 = current_rectangle

        # Ajusta les coordenades segons l'escala original
        displayed_width, displayed_height = current_image.size
        original_width, original_height = original_image.size
        scale_x = original_width / displayed_width
        scale_y = original_height / displayed_height
        x1 = int(x1 * scale_x)
        y1 = int(y1 * scale_y)
        x2 = int(x2 * scale_x)
        y2 = int(y2 * scale_y)

        # Retalla la imatge i l'afegeix a la llista
        cropped = original_image.crop((x1, y1, x2, y2))
        retall_lines.append(cropped)
        messagebox.showinfo("Retall", f"L\u00ednia retallada i afegida. Total l\u00ednies: {len(retall_lines)}")


def activar_desactivar_marca():
    return None       


def eliminar_ultim_retall():
    '''
    Elimina l'últim retall de la llista de retalls (retall_lines).
    Si no queden retalls després d'eliminar-lo, es torna a mostrar la imatge original.
    Mostra missatges informatius segons l'estat de la llista de retalls.
    '''
    global retall_lines, current_image  # Variables globals per gestionar les línies retallades i la imatge actual
    if retall_lines:  # Comprovar si hi ha línies retallades disponibles
        # Eliminar l'últim retall de la llista
        retall_lines.pop()
        if retall_lines:  # Si encara queden retalls després d'eliminar l'últim
            # Actualitzar la imatge actual amb el penúltim retall
            current_image = retall_lines[-1].copy()
            mostrar_imatge(current_image)  # Mostrar la imatge actualitzada
            messagebox.showinfo("Retall eliminat", f"S'ha eliminat l'últim retall. Queden {len(retall_lines)} línies.")
        else:
            # Si no queden més retalls, tornar a la imatge original
            current_image = original_image.copy()
            mostrar_imatge(current_image)
            messagebox.showinfo("Retalls eliminats", "No queden línies retallades.")
    else:
        # Si no hi ha línies per eliminar, mostrar un avís
        messagebox.showwarning("Error", "No hi ha cap línia retallada per eliminar.")


def navegar(direccio):
    '''
    Permet navegar entre les línies retallades (anterior i següent).
    Actualitza la imatge actual segons la direcció i actualitza la interfície.
    '''
    global current_line_index, viewing_retall, current_image  # Variables globals per gestionar la navegació de línies
    if not retall_lines:  # Comprovar si la llista de retalls està buida
        messagebox.showwarning("Navegació", "No hi ha línies retallades.")
        return

    # Actualitzar l'índex de la línia segons la direcció (prev o next)
    if direccio == "prev":
        current_line_index = (current_line_index - 1) % len(retall_lines)  # Retrocedir circularment
    elif direccio == "next":
        current_line_index = (current_line_index + 1) % len(retall_lines)  # Avançar circularment

    viewing_retall = True  # Indicar que s'està visualitzant un retall
    current_image = retall_lines[current_line_index].copy()  # Actualitzar la imatge amb el retall actual
    mostrar_imatge(current_image)  # Mostrar la imatge actualitzada

    # Actualitzar la interfície amb l'índex actual de la línia
    line_counter_label.config(text=f"Línia: {current_line_index + 1} / {len(retall_lines)}")
    activar_linea_actual_musescore(current_line_index)  # Activar la finestra de MuseScore per la línia actual


def activar_linea_actual_musescore(linea_actual):
    '''
    Activa la finestra de MuseScore que conté el fitxer .musicxml corresponent
    a la línia retallada actual, basant-se en el nom de la imatge i l'índex.
    '''
    # Generar el nom del fitxer segons la línia actual (afegint zeros davant si cal)
    ventana_buscar = f"{nom_imatge}.{str(linea_actual+1).zfill(2)}.musicxml"  # nom_imatge és la foto actual
    
    # Filtrar les finestres obertes que coincideixin amb el títol generat
    ventanas_musescore = [
        ventana for ventana in gw.getWindowsWithTitle("") if ventana.title == ventana_buscar
    ]
    
    # Comprovar si s'ha trobat la finestra corresponent
    if ventanas_musescore:
        ventana = ventanas_musescore[0]  # Només hauria d'haver-hi una finestra exacta
        ventana.activate()  # Activar la finestra trobada
        print(f"Ventana '{ventana.title}' activada correctament.")
    else:
        # Si no es troba la finestra, mostrar un missatge per consola
        print(f"No s'ha trobat la finestra per {ventana_buscar}. Revisa manualment.")
    
    # Per depuració: mostrar totes les finestres detectades per `gw`
    # print("Ventanas detectadas:", [ventana.title for ventana in gw.getWindowsWithTitle("")])


def tornar_a_imatge_completa():
    '''
    Torna a mostrar la imatge original completa, deixant de visualitzar retalls.
    Reinicia l'etiqueta de la línia a "Línia: 0".
    '''
    global viewing_retall, current_image  # Variables globals per gestionar l'estat de la imatge
    if original_image:  # Comprovar si la imatge original està disponible
        viewing_retall = False  # Indicar que no s'està visualitzant cap retall
        current_image = original_image.copy()  # Tornar a la imatge original
        mostrar_imatge(current_image)  # Mostrar la imatge original
        line_counter_label.config(text="Línia: 0")  # Reiniciar el comptador de línies a 0


def ajustar_brillo(value):
    '''
    Ajusta la brillantor de la imatge actual.
    Si s'està visualitzant un retall, ajusta només aquest retall.
    Si no, ajusta la imatge original completa.
    El valor de brillantor és un factor entre 0 i 2.
    '''
    global original_image, current_image, viewing_retall, retall_lines, current_line_index
    if original_image:  # Comprovar si la imatge original existeix
        brightness_factor = float(value) / 50  # Ajustar el factor de brillantor (escala de 0 a 2)

        if viewing_retall and retall_lines:  # Si s'està visualitzant un retall
            # Treballar amb una còpia del retall actual per no modificar l'original
            original_cropped = retall_lines[current_line_index].copy()
            enhancer = ImageEnhance.Brightness(original_cropped)  # Inicialitzar l'eina de brillantor
            adjusted_cropped = enhancer.enhance(brightness_factor)  # Aplicar l'ajust de brillantor
            mostrar_imatge(adjusted_cropped)  # Mostrar el retall ajustat
        else:
            # Ajustar la brillantor de la imatge completa
            enhancer = ImageEnhance.Brightness(original_image)
            current_image = enhancer.enhance(brightness_factor)
            mostrar_imatge(current_image)  # Mostrar la imatge ajustada


# FUNCIONS PER FER FUNCIONAR EL ZOOM AND DRAG
def aplicar_zoom(event):
    '''
    Gestiona el nivell de zoom sobre la imatge quan es visualitza un retall.
    Utilitza l'entrada de la roda del ratolí per augmentar o reduir el zoom.
    
    Paràmetres:
        - event: Conté informació sobre l'entrada (roda del ratolí).
    
    Nota:
        El zoom només funciona quan s'està visualitzant un retall.
    '''
    global zoom_level, viewing_retall
    if viewing_retall:  # Només permet fer zoom si s'està visualitzant un retall
        if event.delta > 0:
            # Augmentar el zoom fins a un màxim de 3.0x
            zoom_level = min(zoom_level + 0.1, 3.0)
        elif event.delta < 0:
            # Reduir el zoom fins a un mínim de 0.6x
            zoom_level = max(zoom_level - 0.1, 0.6)
        actualizar_zoom_drag()  # Actualitzar la visualització amb el nou nivell de zoom
    else:
        # Mostrar un missatge si s'intenta fer zoom fora del mode de retall
        messagebox.showinfo("Zoom", "De moment el zoom només està disponible en mode de retall!")


def iniciar_drag(event):
    '''
    Inicia l'operació de "drag" per moure la imatge en el canvas.
    Guarda la posició inicial del cursor quan es comença a arrossegar.

    Paràmetres:
        - event: Conté la posició actual del cursor dins del canvas.
    '''
    drag_data["x"] = event.x  # Coordenada X inicial
    drag_data["y"] = event.y  # Coordenada Y inicial


def mover_imagen(event):
    '''
    Gestiona el desplaçament de la imatge (drag) dins del canvas.
    Calcula el desplaçament des de la posició anterior del cursor fins a la nova.

    Paràmetres:
        - event: Conté la nova posició del cursor dins del canvas.
    '''
    # Calcular el desplaçament en X i Y
    dx = event.x - drag_data["x"]
    dy = event.y - drag_data["y"]
    
    # Actualitzar les coordenades del cursor
    drag_data["x"] = event.x
    drag_data["y"] = event.y
    
    # Actualitzar les coordenades de desplaçament de la imatge
    offset_x, offset_y = drag_data["image_offset"]
    drag_data["image_offset"] = (offset_x + dx, offset_y + dy)
    actualizar_zoom_drag()  # Aplicar el desplaçament actualitzat a la imatge


def actualizar_zoom_drag():
    '''
    Aplica el nivell de zoom i el desplaçament actuals a la imatge retallada.
    Redimensiona la imatge segons el nivell de zoom i la centra al canvas.

    Nota:
        Només s'aplica si s'està visualitzant un retall.
    '''
    global zoom_level, drag_data, retall_lines, current_line_index
    if retall_lines:  # Comprovar que hi hagi línies retallades
        cropped = retall_lines[current_line_index]  # Obtenir el retall actual
        
        # Redimensionar la imatge segons el nivell de zoom
        width, height = cropped.size
        zoomed_image = cropped.resize(
            (int(width * zoom_level), int(height * zoom_level)), 
            Image.Resampling.LANCZOS
        )
        
        # Obtenir les dimensions del canvas i el desplaçament actual
        canvas_width, canvas_height = image_label.winfo_width(), image_label.winfo_height()
        offset_x, offset_y = drag_data["image_offset"]
        
        # Crear una imatge centrada dins del canvas amb el color de fons
        centered_image = Image.new("RGBA", (canvas_width, canvas_height), (44, 44, 60, 255))
        centered_image.paste(zoomed_image, (offset_x, offset_y))  # Aplicar la imatge redimensionada
        
        mostrar_imatge(centered_image)  # Mostrar la imatge final al canvas



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
#######################################        CREACIÓ INTERFÍCIE PRINCIPAL      #########################################################
##########################################################################################################################################

# Importació de llibreries necessàries
import tkinter as tk  # Llibreria per crear interfícies gràfiques
from tkinter import ttk, messagebox  # ttk per estils avançats, messagebox per mostrar missatges emergents

# Creació de la finestra principal
root = tk.Tk()
root.title("Gestor de Partitures - TFG")  # Títol de la finestra
root.geometry("900x900")  # Mida inicial de la finestra
root.configure(bg="#1f1f2e")  # Configuració del color de fons de la finestra

# Mantenir la finestra en primer pla
root.attributes("-topmost", True)

# Funció per alternar el primer pla de la finestra
def toggle_on_top():
    current_state = root.attributes("-topmost")  # Estat actual del primer pla
    new_state = not current_state  # Alternar l'estat
    root.attributes("-topmost", new_state)  # Aplicar el nou estat
    if new_state:
        messagebox.showinfo("Estado de ventana", "La ventana está ahora en primer plano.")  # Missatge en primer pla
    else:
        messagebox.showinfo("Estado de ventana", "La ventana ya no está en primer plano.")  # Missatge fora del primer pla

# Configuració d'estils per a botons i marcs
style = ttk.Style()
style.theme_use("clam")  # Ús del tema 'clam'
style.configure("TButton", font=("Arial", 12), background="#6c63ff", foreground="white", padding=6)
style.map("TButton", background=[("active", "#5548c8")])
style.configure("TFrame", background="#1f1f2e")  # Color de fons per marcs

# Configuració de distribució de la graella principal
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# Creació d'un títol per a la interfície
title_label = tk.Label(root, text="🎵 Gestor de Partitures 🎵", font=("Arial", 32, "bold"), bg="#1f1f2e", fg="#f4a261")
title_label.grid(row=0, column=0, pady=20, sticky="ew")

# Creació del marc principal
main_frame = ttk.Frame(root, style="TFrame")
main_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=1)

# Secció de control de brillantor
brightness_frame = ttk.Frame(main_frame, style="TFrame")
brightness_frame.grid(row=0, column=0, sticky="ns")
brightness_label = tk.Label(brightness_frame, text="Brillantor", bg="#1f1f2e", fg="white", font=("Arial", 12))
brightness_label.pack()
brightness_scale = ttk.Scale(brightness_frame, from_=0, to=100, orient=tk.VERTICAL, command=ajustar_brillo, length=240)
brightness_scale.set(50)
brightness_scale.pack(pady=50)

# Marc per visualitzar imatges
image_frame = ttk.Frame(main_frame, style="TFrame")
image_frame.grid(row=0, column=1, sticky="nsew")
image_frame.grid_rowconfigure(0, weight=1)
image_frame.grid_columnconfigure(0, weight=1)
image_label = tk.Label(image_frame, bg="#2c2c3c", relief=tk.RIDGE, borderwidth=5, width=900, height=700)
image_label.grid(row=0, column=0, sticky="nsew")

# Creació de la barra de menú
menu_bar = tk.Menu(root)

# Menú Arxiu
file_menu = tk.Menu(menu_bar, tearoff=0, bg="#2c2c3c", fg="white", activebackground="#6c63ff")
file_menu.add_command(label="Obrir", command=obrir_imatge)  # Funció per obrir imatges
file_menu.add_command(label="Guardar", command=guardar_musescore)  # Funció per guardar
file_menu.add_separator()
file_menu.add_command(label="Sortir", command=root.quit)
menu_bar.add_cascade(label="Arxiu", menu=file_menu)

# Menú Editar
edit_menu = tk.Menu(menu_bar, tearoff=0, bg="#2c2c3c", fg="white", activebackground="#6c63ff")
edit_menu.add_command(label="Retallar", command=retallar)  # Funció per retallar
menu_bar.add_cascade(label="Editar", menu=edit_menu)

# Menú Ajuda
help_menu = tk.Menu(menu_bar, tearoff=0, bg="#2c2c3c", fg="white", activebackground="#6c63ff")
help_menu.add_command(label="Sobre", command=lambda: print("Gestor de Partitures v1.0"))
menu_bar.add_cascade(label="Ajuda", menu=help_menu)

# Afegir menú a la finestra principal
root.config(menu=menu_bar)

# Creació de seccions de controls addicionals
menu_frame = ttk.Frame(root, style="TFrame")
menu_frame.grid(row=2, column=0, pady=10, sticky="nsew")

# Secció de Recorte
crop_section = ttk.Frame(menu_frame, style="TFrame")
crop_section.pack(fill="x", pady=10)
crop_label = tk.Label(crop_section, text="Retalls", bg="#1f1f2e", fg="white", font=("Arial", 14, "bold"))
crop_label.pack(anchor="w", pady=5)

# Botons de retall
adjust_up_button = ttk.Button(crop_section, text="▲", command=lambda: ajustar_rectangle(-5))
adjust_up_button.pack(side=tk.LEFT, padx=5)
adjust_down_button = ttk.Button(crop_section, text="▼", command=lambda: ajustar_rectangle(5))
adjust_down_button.pack(side=tk.LEFT, padx=5)

# Controls per la mida del retall
size_label = tk.Label(crop_section, text="Mida Retall:", bg="#1f1f2e", fg="white", font=("Arial", 12, "bold"))
size_label.pack(side=tk.LEFT, padx=5)
size_entry = ttk.Entry(crop_section, width=5)
size_entry.insert(0, "50")
size_entry.pack(side=tk.LEFT, padx=5)
size_entry.bind("<Return>", ajustar_rectangle_personalitzat)

adjust_custom_button = ttk.Button(crop_section, text="Aplica mida", command=ajustar_rectangle_personalitzat)
adjust_custom_button.pack(side=tk.LEFT, padx=5)

# Botó per eliminar retalls
retallar_button = ttk.Button(crop_section, text="Retallar", command=retallar)
retallar_button.pack(side=tk.LEFT, padx=5)
retallar_button = ttk.Button(crop_section, text="Eliminar retall", command=eliminar_ultim_retall)
retallar_button.pack(side=tk.LEFT, padx=5)

# Secció de Navegació
nav_section = ttk.Frame(menu_frame, style="TFrame")
nav_section.pack(fill="x", pady=10)
nav_label = tk.Label(nav_section, text="Navegació", bg="#1f1f2e", fg="white", font=("Arial", 14, "bold"))
nav_label.pack(anchor="w", pady=5)

# Botons de navegació
reset_button = ttk.Button(nav_section, text="Imatge Completa", command=tornar_a_imatge_completa)
reset_button.pack(side=tk.LEFT, padx=5)
prev_button = ttk.Button(nav_section, text="←", command=lambda: navegar("prev"))
prev_button.pack(side=tk.LEFT, padx=2)

# Indicador de línia
line_counter_label = tk.Label(nav_section, text="Línia: 0", bg="#1f1f2e", fg="white", font=("Arial", 12, "bold"))
line_counter_label.pack(side=tk.LEFT, padx=10)

next_button = ttk.Button(nav_section, text="→", command=lambda: navegar("next"))
next_button.pack(side=tk.LEFT, padx=2)

# Funcionalitat Zoom
image_label.bind("<MouseWheel>", aplicar_zoom)
image_label.bind("<ButtonPress-1>", iniciar_drag)
image_label.bind("<B1-Motion>", mover_imagen)
image_label.bind("<Button-4>", lambda e: aplicar_zoom(type("Event", (object,), {"delta": 120})()))  # Roda amunt (per si s'executa en Linux)
image_label.bind("<Button-5>", lambda e: aplicar_zoom(type("Event", (object,), {"delta": -120})()))  # Roda avall (per si s'executa en Linux)

# Iniciar el bucle principal de l'aplicació
root.mainloop()





'''
Tant convertir_mscz_a_musicxml() com unificar_partitures() han sigut implementacions fallides de cara a unificar directament arxius mscz. De totes maneres, 
la utilitat i funció d'aquestes 2 funcions base si funcionen així que es deixen aquí per a possibles implementacions a futur que involucressin aquests processos
'''
def convertir_mscz_a_musicxml(musescore_path, input_mscz, output_folder):
    """
    Converteix un fitxer MSCZ a MusicXML utilitzant MuseScore des de la línia de comandes.
    """
    output_musicxml = os.path.join(output_folder, os.path.splitext(os.path.basename(input_mscz))[0] + ".musicxml")
    try:
        subprocess.run([musescore_path, "-o", output_musicxml, input_mscz], check=True)
        return output_musicxml
    except subprocess.CalledProcessError as e:
        print(f"Error en convertir {input_mscz}: {e}")
        return None

def unificar_partitures(arxius_musicxml):
    """
    Uneix múltiples partitures MusicXML en una sola partitura.
    """
    partitura_unida = stream.Score()
    temps_actual = 0  # Manté el temps on afegir la següent partitura

    for index, arxiu in enumerate(arxius_musicxml):
        try:
            print(f"Processant {arxiu}...")
            partitura = converter.parse(arxiu)

            # Ajustar el temps d'inici de cada nota/resta
            for part in partitura.parts:
                for element in part.flat.notesAndRests:
                    element.offset += temps_actual

                # Afegir la part ajustada a la partitura unida
                partitura_unida.append(part)

            # Actualitzar el temps actual per la següent partitura
            temps_actual += partitura.duration.quarterLength
        except Exception as e:
            print(f"No s'ha pogut processar {arxiu}: {e}")
    return partitura_unida


