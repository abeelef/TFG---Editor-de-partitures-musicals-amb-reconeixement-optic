import subprocess
import tkinter as tk
from PIL import ImageTk, Image
import pyautogui
import pygetwindow as gw
import time

def executar_musescore(archivo_musicxml):
    musescore_path = "C:/Program Files/MuseScore 4/bin/MuseScore4.exe"  # Assegura't que aquesta és la ruta correcta
    subprocess.Popen([musescore_path, archivo_musicxml])  # Popen en lloc de run

def mostrar_imagen(ruta_imagen):
    ventana = tk.Tk()
    ventana.title("Partitura manuscrita")
    ventana.attributes('-topmost', True)  # Assegura que la finestra estigui sempre al davant
    
    img = Image.open(ruta_imagen)
    img.thumbnail((600, 600))  # Ajustar la mida de la imatge (ample, alçada)
    img = ImageTk.PhotoImage(img)
    
    panel = tk.Label(ventana, image=img)
    panel.image = img  # Mantenir una referència a la imatge per evitar la recollida d'escombraries
    panel.pack(side="bottom", fill="both", expand="yes")

    # Afegir un botó per guardar
    boto_guardar = tk.Button(ventana, text="Guardar", command=guardar_fitxer)
    boto_guardar.pack(side="bottom", pady=10)

    ventana.mainloop()

def guardar_fitxer():
    # Assegurar que MuseScore tingui el focus abans de guardar
    musescore_window = gw.getWindowsWithTitle("prova.musicxml")  # Utilitza el títol correcte
    if musescore_window:
        musescore_window[0].activate()
        time.sleep(0.5)  # Esperar un moment per assegurar-se que el focus s'ha establert
        pyautogui.hotkey('ctrl', 's')  # Simular les tecles per guardar (Ctrl + S)
    else:
        print("No s'ha trobat la finestra de MuseScore")

def sincronitzar():
    # Obtenir la posició del cursor
    cursor_pos = pyautogui.position()
    print(f"Posició del cursor: {cursor_pos}")
    
    # Simular la selecció a MuseScore
    musescore_window = gw.getWindowsWithTitle("prova.musicxml")
    if musescore_window:
        musescore_window[0].activate()
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'a')  # Ex: seleccionar tota la partitura
    else:
        print("No s'ha trobat la finestra de MuseScore")

        
if __name__ == "__main__":
    archivo_musicxml = "C:/Users/abel/Desktop/UNI/TFG/editor_partituras/prova.musicxml"
    ruta_imagen = "C:/Users/abel/Desktop/UNI/TFG/exemplesMusicXML/exemplesMusicXML/CVCDOL.S01P01/CVCDOL.S01P01/XAC_ACAN_SMIAu04_005.jpg"

    # Executar MuseScore amb el fitxer MusicXML
    executar_musescore(archivo_musicxml)

    # Iniciar la finestra amb la imatge de la partitura manuscrita i el botó per guardarf
    mostrar_imagen(ruta_imagen)
