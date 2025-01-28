import tkinter as tk
from tkinter import ttk, filedialog, messagebox,simpledialog
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk, ImageDraw, ImageEnhance
import subprocess, os, re, time, pyautogui
import pygetwindow as gw
from music21 import converter, stream
import psutil
import sqlite3
import os
import json
from datetime import datetime

CONFIG_FILE = "config.json"

# VARIABLES GLOBALS
# Variables per emmagatzemar l'estat de la imatge i retalls
nom_imatge = None  # Nom de l'arxiu d'imatge seleccionat
original_image = None  # Imatge original carregada
current_image = None  # Imatge actual mostrada
retall_lines = {}  # Llista per guardar línies retallades
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
    Carrega la imatge seleccionada, obre els fitxers de MuseScore corresponents,
    i tanca les instàncies de MuseScore de la partitura anterior amb confirmació.
    """
    global nom_imatge,current_image

    # Obre un diàleg per seleccionar arxius d'imatge
    file_path = filedialog.askopenfilename(filetypes=[("Arxius d'imatge", "*.png;*.jpg;*.jpeg")])
    nom_imatge = os.path.splitext(os.path.basename(file_path))[0]  # Guarda el nom de la imatge sense extensió

    if current_image:
        # Mostrar un missatge per confirmar el tancament de MuseScore
        resposta = messagebox.askyesno(
            "Confirmació de tancament",
            "S'estan carregant noves partitures. Has guardat tots els canvis a de l'anterior?\n"
            "Si continues, es tancaran les instàncies actuals i s'obriran les noves."
        )
        if resposta:  # Si l'usuari confirma
            tancar_musescore()  # Tanca MuseScore de la partitura anterior
            messagebox.showinfo(
                "Carregant nova partitura",
                f"S'han tancat les instàncies de MuseScore de la partitura anterior. Carregant la nova partitura: {nom_imatge}."
            )

            # Carrega la nova imatge i obre els fitxers de MuseScore associats
            carregar_imatge(file_path)  # Carrega la imatge seleccionada
            obrir_musescore(file_path)  # Obre MuseScore amb els fitxers relacionats
            activar_bd()
            insertar_o_actualizar(file_path, nom_imatge)
        else:
            # Si l'usuari cancel·la, no es tanca res i es manté la imatge anterior
            messagebox.showinfo("Operació cancel·lada", "No s'ha carregat cap nova imatge ni s'han tancat les instàncies de MuseScore.")
    else:
        # Carrega la nova imatge i obre els fitxers de MuseScore associats
        carregar_imatge(file_path)  # Carrega la imatge seleccionada
        obrir_musescore(file_path)  # Obre MuseScore amb els fitxers relacionats
        activar_bd()
        insertar_o_actualizar(file_path, nom_imatge)



def carregar_imatge(path):
    global original_image, current_image, retall_lines, rectangle_y, viewing_retall, rectangle_height, marca_coords
    try:
        original_image = Image.open(path)
        original_image.thumbnail((820, 950))  # MIDA DE LA FOTO
        current_image = original_image.copy()

        retall_lines = {}
        rectangle_y = 100
        rectangle_height = 50
        viewing_retall = False

        # Recuperar les coordenades de la marca i els retalls des de la base de dades
        db_path = 'gestor_partitures.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT marca_coords, retalls FROM imagenes WHERE nombre_imagen = ?
        """, (nom_imatge,))
        result = cursor.fetchone()
        conn.close()

        if result:
            if result[0]:  # Si hi ha coordenades guardades, les recuperem
                marca_coords = json.loads(result[0])
                actualitzar_marca()

            if result[1]:  # Si hi ha retalls guardats, els recuperem
                retalls_guardats = json.loads(result[1])
                for linia, coordenades in retalls_guardats.items():
                    x1, y1, x2, y2 = coordenades
                    retall = original_image.crop((x1, y1, x2, y2))
                    retall_lines[int(linia)] = retall

        mostrar_imatge(current_image)  # Mostra la imatge si no hi ha marca
    except Exception as e:
        print(f"Error carregant la imatge: {e}")
        mostrar_imatge(current_image)  # Assegura que la imatge es mostra encara que hi hagi un error



def mostrar_imatge(image):
    """
    Mostra la imatge proporcionada en l'etiqueta d'imatge (Tkinter).
    """
    # Converteix la imatge proporcionada (de PIL) al format compatible amb Tkinter
    img = ImageTk.PhotoImage(image)
    
    # Actualitza la configuració de l'etiqueta d'imatge (image_label) per mostrar la nova imatge
    image_label.config(image=img)
    
    # Assigna la imatge a una propietat de l'etiqueta per evitar que es perdi la referència
    # (Això és necessari per evitar que Python elimini l'objecte img de la memòria)
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
    executar_musescore(partituras)  #ACTIVAR O DESACTIVAR PER FER PROVES MÉS RÀPID



# Función para cargar la ruta guardada
def load_musescore_path():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("musescore_path")
    return None



# Función para guardar la ruta en un archivo de configuración
def save_musescore_path(path):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"musescore_path": path}, f)



# Función para seleccionar el ejecutable de MuseScore con un cuadro de diálogo
def select_musescore():
    print("Selecciona el archivo ejecutable de MuseScore...")
    tk.Tk().withdraw()  # Correcto: Usa tk.Tk() para crear la ventana principal y ocultarla
    file_path = askopenfilename(
        title="Seleccionar ejecutable de MuseScore",
        filetypes=[("Archivos ejecutables", "*.exe")],
        initialdir="C:/Program Files"  # Ruta inicial sugerida
    )
    return file_path if file_path else None        



# Función para ejecutar MuseScore con los archivos seleccionados
def executar_musescore(lista_archivos):
    """
    Abre los archivos MusicXML en MuseScore.
    Si la ruta no está configurada, permite seleccionarla con un cuadro de diálogo.
    Jo la tinc en: "C:/Program Files/MuseScore 4/bin/MuseScore4.exe" 
    """
    musescore_path = load_musescore_path()  # Intentar cargar la ruta desde configuración
    if not musescore_path or not os.path.exists(musescore_path):  # Si no existe, pedirla
        musescore_path = select_musescore()
        if musescore_path:
            save_musescore_path(musescore_path)  # Guardar la ruta para el futuro
        else:
            print("No se seleccionó un ejecutable de MuseScore. Abortando.")
            return  # Salir si no se selecciona una ruta válida

    # Ejecutar MuseScore con los archivos proporcionados
    for archivo in lista_archivos:
        subprocess.Popen([musescore_path, archivo])  # Abre MuseScore con el archivo
        print(f"Abriendo {archivo} con MuseScore...")



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
            actualitzar_data_edicio(nombre_imagen_sin_extension)
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
    Retalla la part de la imatge dins del rectangle actual i la guarda associada a un número de línia.
    """
    global current_rectangle, retall_lines
    if current_rectangle and original_image:
        # Demana a l'usuari el número de línia
        numero_linia = simpledialog.askinteger(
            "Número de línia",
            "Introdueix el número de línia al qual correspon aquest retall:",
            parent=root
        )
        if numero_linia is None:
            messagebox.showinfo("Operació cancel·lada", "No s'ha introduït cap número de línia.")
            return

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

        # Retalla la imatge
        cropped = original_image.crop((x1, y1, x2, y2))

        # Actualitza o afegeix el retall associat a la línia
        retall_lines[numero_linia] = cropped

        # Guarda el retall a la base de dades
        coordenades = [x1, y1, x2, y2]
        guardar_retall_db(nom_imatge, numero_linia, coordenades)

        messagebox.showinfo("Retall", f"Retall afegit o actualitzat per la línia {numero_linia}.")



def activar_desactivar_marca():
    """
    Activa o desactiva la funcionalitat de la marca.
    La marca es col·loca a la darrera posició guardada o al centre de la imatge si no n'hi ha.
    """
    global marca_activa, marca_coords, current_image

    # Alternar l'estat de la funcionalitat de la marca
    marca_activa = not globals().get('marca_activa', False)

    if marca_activa:
        if not current_image:
            messagebox.showwarning("Advertència", "No hi ha cap imatge carregada per activar la marca.")
            return

        # Recuperar coordenades guardades des de la base de dades
        db_path = 'gestor_partitures.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT marca_coords FROM imagenes WHERE nombre_imagen = ?
        """, (nom_imatge,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:  # Si hi ha coordenades guardades
            marca_coords = json.loads(result[0])
        else:
            # Col·locar la marca al centre si no hi ha coordenades
            marca_coords = (current_image.width // 2, current_image.height // 2)

        actualitzar_marca()  # Mostrar la marca a la posició adequada

        # Informar l'usuari que pot moure la marca amb les fletxes
        messagebox.showinfo("Marca Activa", "La marca està activa. Pots moure-la amb les fletxes del teclat.")

        # Vincular les tecles per moure la marca
        root.bind("<Up>", moure_marca)
        root.bind("<Down>", moure_marca)
        root.bind("<Left>", moure_marca)
        root.bind("<Right>", moure_marca)
    else:
        # Desvincular els esdeveniments i restaurar la imatge original
        root.unbind("<Up>")
        root.unbind("<Down>")
        root.unbind("<Left>")
        root.unbind("<Right>")
        mostrar_imatge(current_image)
        marca_coords = None  # Reiniciar les coordenades de la marca
        messagebox.showinfo("Marca Desactivada", "La marca s'ha desactivat correctament.")



def moure_marca(event):
    """
    Mou la marca en la direcció indicada per les fletxes del teclat.
    """
    global marca_coords

    if not marca_coords:
        messagebox.showwarning("Advertència", "No hi ha cap marca per moure.")
        return

    # Actualitzar les coordenades de la marca segons la tecla pressionada
    x, y = marca_coords
    if event.keysym == "Up":
        y = max(0, y - 10)
    elif event.keysym == "Down":
        y = min(current_image.height, y + 10)
    elif event.keysym == "Left":
        x = max(0, x - 10)
    elif event.keysym == "Right":
        x = min(current_image.width, x + 10)
    marca_coords = (x, y)


    # Actualitzar les coordenades de la marca a la base de dades
    db_path = 'gestor_partitures.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE imagenes
        SET marca_coords = ?
        WHERE nombre_imagen = ?
    """, (json.dumps(marca_coords), nom_imatge))  # Convertim les coordenades a format JSON
    conn.commit()
    conn.close()

    # Actualitzar la imatge amb la marca movent-se
    actualitzar_marca()



def actualitzar_marca():
    """
    Redibuixa la imatge amb la marca a les coordenades actuals.
    """
    global marca_coords, current_image

    if not current_image or not marca_coords:
        return

    # Crear una còpia de la imatge actual
    image_with_mark = current_image.copy()
    draw = ImageDraw.Draw(image_with_mark)

    # Coordenades de la marca
    x, y = marca_coords
    size = 10  # Mida de la creu

    # Dibuixar una creu com a marca centrada
    draw.line((x - size, y - size, x + size, y + size), fill="red", width=2)  # Diagonal 1
    draw.line((x - size, y + size, x + size, y - size), fill="red", width=2)  # Diagonal 2

    # Mostrar la imatge amb la marca
    mostrar_imatge(image_with_mark)



def eliminar_retall():
    """
    Elimina el retall associat al número de línia especificat per l'usuari.
    """
    global retall_lines
    if not retall_lines:
        messagebox.showwarning("Error", "No hi ha retalls disponibles per eliminar.")
        return

    # Demana a l'usuari el número de línia
    numero_linia = simpledialog.askinteger(
        "Eliminar retall",
        "Introdueix el número de línia del retall que vols eliminar:",
        parent=root
    )
    if numero_linia is None:
        messagebox.showinfo("Operació cancel·lada", "No s'ha introduït cap número de línia.")
        return

    # Elimina el retall si existeix
    if numero_linia in retall_lines:
        del retall_lines[numero_linia]

        # Actualitza la base de dades
        db_path = 'gestor_partitures.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Recuperem els retalls existents
        cursor.execute("""
            SELECT retalls FROM imagenes WHERE nombre_imagen = ?
        """, (nom_imatge,))
        resultat = cursor.fetchone()

        retalls = json.loads(resultat[0]) if resultat and resultat[0] else {}

        # Eliminar el retall de la línia especificada
        if str(numero_linia) in retalls:
            del retalls[str(numero_linia)]

        # Guardar els retalls actualitzats a la base de dades
        cursor.execute("""
            UPDATE imagenes
            SET retalls = ?
            WHERE nombre_imagen = ?
        """, (json.dumps(retalls), nom_imatge))

        conn.commit()
        conn.close()

        messagebox.showinfo("Retall eliminat", f"S'ha eliminat el retall de la línia {numero_linia}.")
    else:
        messagebox.showwarning("Error", f"No hi ha cap retall associat a la línia {numero_linia}.")



def navegar(direccio):
    '''
    Permet navegar entre les línies retallades (anterior i següent).
    Actualitza la imatge actual segons la direcció i actualitza la interfície.
    '''
    global current_line_index, viewing_retall, current_image  # Variables globals per gestionar la navegació de línies
    if not retall_lines:  # Comprovar si el diccionari de retalls està buit
        messagebox.showwarning("Navegació", "No hi ha línies retallades.")
        return

    # Obtenim els números de línia disponibles de forma ordenada
    linies_disponibles = sorted(retall_lines.keys())

    # Actualitzar l'índex de la línia segons la direcció (prev o next)
    if direccio == "prev":
        current_line_index = (current_line_index - 1) % len(linies_disponibles)  # Retrocedir circularment
    elif direccio == "next":
        current_line_index = (current_line_index + 1) % len(linies_disponibles)  # Avançar circularment

    # Obtenim el número de línia actual segons l'índex
    linia_actual = linies_disponibles[current_line_index]

    viewing_retall = True  # Indicar que s'està visualitzant un retall
    current_image = retall_lines[linia_actual].copy()  # Actualitzar la imatge amb el retall actual
    mostrar_imatge(current_image)  # Mostrar la imatge actualitzada

    # Actualitzar la interfície amb el número de línia actual
    line_counter_label.config(text=f"Línia: {linia_actual}")
    activar_linea_actual_musescore(linia_actual)  # Activar la finestra de MuseScore per la línia actual




def activar_linea_actual_musescore(linea_actual):
    '''
    Activa la finestra de MuseScore que conté el fitxer .musicxml corresponent
    a la línia retallada actual, basant-se en el nom de la imatge i l'índex.
    '''
    # Generar el nom del fitxer segons la línia actual (afegint zeros davant si cal)
    ventana_buscar = f"{nom_imatge}.{str(linea_actual).zfill(2)}.musicxml"  # nom_imatge és la foto actual
    
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
        messagebox.showwarning("Finestra no trobada", f"No s'ha trobat la finestra per {ventana_buscar}. Revisa manualment.")
    
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



def tancar_musescore():
    """
    Tanca tots els processos de MuseScore oberts.
    """
    for proc in psutil.process_iter(['name']):
        try:
            if "MuseScore" in proc.info['name']:
                proc.terminate()  # Intenta finalitzar el procés
                proc.wait(timeout=5)  # Espera que el procés es tanqui
                print(f"Procés {proc.info['name']} tancat.")
        except Exception as e:
            print(f"No s'ha pogut tancar el procés: {e}")



def sortir():
    """
    Mostra un missatge de confirmació abans de tancar MuseScore i l'aplicació.
    """
    resposta = messagebox.askyesno(
        "Confirmació de tancament",
        "T'has assegura't que has guardat tots els canvis de la partitura treballada?"
    )
    if resposta:  
        tancar_musescore()  # Tanca MuseScore
        root.quit()  # Tanca l'aplicació principal

##########################################################################################################################################
################################################   PART DE LA BASE DE DADES      #########################################################
##########################################################################################################################################


def guardar_retall_db(nom_imatge, numero_linia, coordenades):
    db_path = 'gestor_partitures.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Recuperem els retalls existents
    cursor.execute("""
        SELECT retalls FROM imagenes WHERE nombre_imagen = ?
    """, (nom_imatge,))
    resultat = cursor.fetchone()

    retalls = json.loads(resultat[0]) if resultat and resultat[0] else {}

    # Afegim o actualitzem el retall
    retalls[numero_linia] = coordenades

    # Guardem els retalls actualitzats a la base de dades
    cursor.execute("""
        UPDATE imagenes
        SET retalls = ?
        WHERE nombre_imagen = ?
    """, (json.dumps(retalls), nom_imatge))

    conn.commit()
    conn.close()


def activar_bd():
    """
    Crea la base de dades i la taula necessària si no existeixen.
    Si la taula ja existeix, comprova que tingui totes les columnes necessàries.
    """
    db_path = 'gestor_partitures.db'

    # Estableix connexió amb la base de dades
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Elimina la taula si és necessari (només en desenvolupament)
    try:
        cursor.execute("SELECT marca_coords FROM imagenes LIMIT 1")
    except sqlite3.OperationalError:
        # Si la columna no existeix, recreem la taula
        cursor.execute("DROP TABLE IF EXISTS imagenes")
        print("Taula eliminada per assegurar que es recrea amb les noves columnes.")

    # Crea la taula amb totes les columnes requerides
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS imagenes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ruta_imagen TEXT UNIQUE,
        nombre_imagen TEXT UNIQUE,
        fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
        fecha_edicion TEXT DEFAULT CURRENT_TIMESTAMP,
        marca_coords TEXT DEFAULT NULL,
        retalls TEXT DEFAULT NULL
    )
    """)
    print("BD i taula creada o actualitzada correctament.")

    # Tanca la connexió
    conn.commit()
    conn.close()



def insertar_o_actualizar(ruta_imagen, nombre_imagen):
    """
    Inserta un nou registre a la base de dades amb la ruta i el nom de la imatge,
    o bé actualitza la data d'edició si el registre ja existeix.
    """
    db_path = 'gestor_partitures.db'  # Ruta de la base de dades
    conn = sqlite3.connect(db_path)  # Estableix la connexió amb la base de dades
    cursor = conn.cursor()  # Crea un cursor per executar consultes SQL

    # Verifica si ja existeix un registre amb la mateixa ruta o nom de la imatge
    cursor.execute("""
    SELECT id FROM imagenes WHERE ruta_imagen = ? OR nombre_imagen = ?
    """, (ruta_imagen, nombre_imagen))
    resultado = cursor.fetchone()  # Obté el primer resultat si existeix

    if resultado:
        # Si el registre ja existeix, només s'actualitza la data d'edició
        id_existente = resultado[0]
        cursor.execute("""
        UPDATE imagenes
        SET fecha_edicion = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (id_existente,))
        print(f"Registro existente actualizado (ID: {id_existente}).")
    else:
        # Si no existeix, inserta un nou registre amb la ruta i el nom
        cursor.execute("""
        INSERT INTO imagenes (ruta_imagen, nombre_imagen)
        VALUES (?, ?)
        """, (ruta_imagen, nombre_imagen))
        print("Nuevo registro insertado.")

    conn.commit()  # Guarda els canvis a la base de dades
    conn.close()  # Tanca la connexió amb la base de dades



def actualitzar_data_edicio(nombre_imagen):
    """
    Actualitza la data d'edició del registre que coincideix amb el nom de la imatge.
    Si no es troba cap registre, mostra un missatge indicant-ho.
    """
    db_path = 'gestor_partitures.db'  # Ruta de la base de dades
    conn = sqlite3.connect(db_path)  # Estableix la connexió amb la base de dades
    cursor = conn.cursor()  # Crea un cursor per executar consultes SQL

    # Obté la data actual en format 'YYYY-MM-DD HH:MM:SS'
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Actualitza el camp `fecha_edicion` del registre que coincideix amb `nombre_imagen`
    cursor.execute("""
    UPDATE imagenes
    SET fecha_edicion = ?
    WHERE nombre_imagen = ?
    """, (fecha_actual, nombre_imagen))

    # Confirma si l'actualització s'ha realitzat amb èxit
    if cursor.rowcount > 0:
        print(f"Fecha de edición actualizada para '{nombre_imagen}' a {fecha_actual}.")
    else:
        print(f"No se encontró ningún registro con el nombre de imagen '{nombre_imagen}'.")

    conn.commit()  # Guarda els canvis a la base de dades
    conn.close()  # Tanca la connexió amb la base de dades



def mostrar_bd():
    """
    Crea una finestra per mostrar el contingut de la base de dades.
    La finestra permet cercar registres pel nom de la imatge, refrescar el contingut 
    i tancar la vista de manera fàcil.
    """
    # Crear una nova finestra per mostrar la base de dades
    ventana = tk.Toplevel(root)
    ventana.title("Contingut de la Base de Dades")  # Títol de la finestra
    ventana.geometry("800x400")  # Mida inicial de la finestra
    ventana.configure(bg="#1f1f2e")  # Configuració del color de fons

    # Etiqueta i camp d'entrada per a la cerca
    label_busqueda = tk.Label(ventana, text="Cerca pel Nom:", bg="#1f1f2e", fg="white", font=("Arial", 12))
    label_busqueda.pack(pady=5)

    entry_busqueda = ttk.Entry(ventana, width=30)  # Camp d'entrada de text
    entry_busqueda.pack(pady=5)

    def buscar():
        """Filtra els resultats segons el nom de la imatge introduït."""
        nombre_buscar = entry_busqueda.get().strip()  # Obté el text del camp d'entrada
        for row in tree.get_children():  # Esborra les dades actuals del Treeview
            tree.delete(row)

        conn = sqlite3.connect(db_path)  # Conexió a la base de dades
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM imagenes WHERE nombre_imagen LIKE ?", ('%' + nombre_buscar + '%',))  # Cerca parcial
        registros = cursor.fetchall()
        conn.close()

        for registro in registros:  # Inserta els resultats filtrats al Treeview
            retalls_present = "Sí" if registro[5] else "No"  # Comprovar si té retalls
            tree.insert("", tk.END, values=registro + (retalls_present,))

    def refrescar():
        """Recupera tots els registres de la base de dades i actualitza el Treeview."""
        entry_busqueda.delete(0, tk.END)  # Neteja el camp de cerca
        for row in tree.get_children():  # Esborra les dades actuals del Treeview
            tree.delete(row)

        conn = sqlite3.connect(db_path)  # Conexió a la base de dades
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM imagenes")  # Recupera tots els registres
        registros = cursor.fetchall()
        conn.close()

        for registro in registros:  # Inserta tots els registres al Treeview
            retalls_present = "Sí" if registro[5] else "No"  # Comprovar si té retalls
            tree.insert("", tk.END, values=registro + (retalls_present,))

    def obrir_imatge_des_de_base(event):
        """
        Obre la imatge seleccionada al fer doble clic en una fila del Treeview.
        """
        item = tree.selection()  # Obté l'ítem seleccionat
        if item:
            ruta_seleccionada = tree.item(item, 'values')[1]  # La segona columna conté la ruta de la imatge
            if os.path.exists(ruta_seleccionada):  # Comprova si la ruta és vàlida
                carregar_imatge(ruta_seleccionada)  # Crida a la funció per carregar la imatge
            else:
                messagebox.showerror("Error", f"No s'ha trobat la ruta: {ruta_seleccionada}")        

    # Crear el Treeview per mostrar els registres
    tree = ttk.Treeview(ventana, columns=("ID", "Ruta Imatge", "Nom Imatge", "Data Creació", "Data Edició", "Té Retalls"), show="headings")
    tree.heading("ID", text="ID")  # Capçalera de columna
    tree.heading("Ruta Imatge", text="Ruta Imatge")
    tree.heading("Nom Imatge", text="Nom Imatge")
    tree.heading("Data Creació", text="Data Creació")
    tree.heading("Data Edició", text="Data Edició")
    tree.heading("Té Retalls", text="Té Retalls")

    # Configuració d'amplades de columnes
    tree.column("ID", width=50, anchor="center")
    tree.column("Ruta Imatge", width=250)
    tree.column("Nom Imatge", width=150)
    tree.column("Data Creació", width=150)
    tree.column("Data Edició", width=150)
    tree.column("Té Retalls", width=100, anchor="center")

    # Inserció del Treeview al disseny
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # Connectar l'esdeveniment de doble clic al Treeview
    tree.bind("<Double-1>", obrir_imatge_des_de_base)

    # Recupera tots els registres inicials de la base de dades
    db_path = 'gestor_partitures.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM imagenes")
    registros = cursor.fetchall()
    conn.close()

    # Inserta els registres inicials al Treeview
    for registro in registros:
        retalls_present = "Sí" if registro[5] else "No"  # Comprovar si té retalls
        tree.insert("", tk.END, values=registro + (retalls_present,))

    # Botó per executar la cerca
    btn_buscar = ttk.Button(ventana, text="Cercar", command=buscar)
    btn_buscar.pack(pady=5)

    # Botó per refrescar els resultats
    btn_refrescar = ttk.Button(ventana, text="Refrescar", command=refrescar)
    btn_refrescar.pack(pady=5)

    # Botó per tancar la finestra
    btn_cerrar = ttk.Button(ventana, text="Tancar", command=ventana.destroy)
    btn_cerrar.pack(pady=10)

##########################################################################################################################################
#######################################        CREACIÓ INTERFÍCIE PRINCIPAL      #########################################################
##########################################################################################################################################

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
image_label = tk.Label(image_frame, bg="#2c2c3c", relief=tk.RIDGE, borderwidth=5, width=1200, height=900) #TAMANY FOTO PRINCIPAL
image_label.grid(row=0, column=0, sticky="nsew")

# Creació de la barra de menú
menu_bar = tk.Menu(root)

# Menú Arxiu
file_menu = tk.Menu(menu_bar, tearoff=0, bg="#2c2c3c", fg="white", activebackground="#6c63ff")
file_menu.add_command(label="Obrir", command=obrir_imatge)  # Funció per obrir imatges
file_menu.add_command(label="Guardar", command=guardar_musescore)  # Funció per guardar
file_menu.add_command(label="Veure BaseDades", command=mostrar_bd)  # Funció per veure els registres de la BD
file_menu.add_command(label="Primer pla", command=toggle_on_top)  # Desactivar o activar el primer pla de la meva app  
file_menu.add_separator()
file_menu.add_command(label="Sortir", command=lambda: sortir())
menu_bar.add_cascade(label="Arxiu", menu=file_menu)

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

adjust_custom_button = ttk.Button(crop_section, text="Preparar Retall", command=ajustar_rectangle_personalitzat)
adjust_custom_button.pack(side=tk.LEFT, padx=5)

# Botó per eliminar retalls
retallar_button = ttk.Button(crop_section, text="Retallar", command=retallar)
retallar_button.pack(side=tk.LEFT, padx=5)
retallar_button = ttk.Button(crop_section, text="Eliminar retall", command=eliminar_retall)
retallar_button.pack(side=tk.LEFT, padx=5)

# Secció de Navegació
nav_section = ttk.Frame(menu_frame, style="TFrame")
nav_section.pack(fill="x", pady=10)
nav_label = tk.Label(nav_section, text="Navegació", bg="#1f1f2e", fg="white", font=("Arial", 14, "bold"))
nav_label.pack(anchor="w", pady=5)

# Botons de navegació
reset_button = ttk.Button(nav_section, text="Imatge Completa", command=tornar_a_imatge_completa)
reset_button.pack(side=tk.LEFT, padx=5)
reset_button = ttk.Button(nav_section, text="Activar/Desactivar Marca", command=activar_desactivar_marca)
reset_button.pack(side=tk.LEFT, padx=5)
prev_button = ttk.Button(nav_section, text="←", command=lambda: navegar("prev"))
prev_button.pack(side=tk.LEFT, padx=2)
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

##################################################################################################################
#######################    FUNCIONS FINALMENT NO USADES PERQUÈ AL FINAL NO HAN SIGUT NECESSÀRIES #################
##################################################################################################################

'''
convertir_mscz_a_musicxml() ha sigut part d'una implementacio que s'anava a usar de cara a unificar directament arxius mscz. De totes maneres, 
la utilitat i funció del pas a xml si va.
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




