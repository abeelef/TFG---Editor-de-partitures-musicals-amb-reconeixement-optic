# Cal fer pip install opencv-python-headless
import cv2
import numpy as np
from tkinter import Tk, filedialog
from matplotlib import pyplot as plt

def seleccionar_arxiu():
    """Obre un quadre de diàleg per seleccionar un arxiu d'imatge."""
    Tk().withdraw()  # Amaga la finestra principal de Tkinter
    arxiu_seleccionat = filedialog.askopenfilename(
        title="Seleccionar imatge de partitura",
        filetypes=[("Arxius d'imatge", "*.jpg *.jpeg *.png *.bmp")]
    )
    if not arxiu_seleccionat:
        raise FileNotFoundError("No s'ha seleccionat cap arxiu.")
    return arxiu_seleccionat

def detectar_pentagrames(imatge_path):
    """Detecta els pentagrames a una imatge de partitura i marca un únic punt davant de cadascun."""
    # Carregar l'imatge en escala de grisos
    imatge = cv2.imread(imatge_path, cv2.IMREAD_GRAYSCALE)
    if imatge is None:
        raise FileNotFoundError(f"No s'ha pogut carregar l'imatge: {imatge_path}")
    
    # Millorar el contrast i eliminar soroll amb un suavitzat
    imatge_suavitzada = cv2.GaussianBlur(imatge, (5, 5), 0)
    
    # Fer un llindar per millorar la detecció de vores (transformar l'imatge en blanc i negre)
    _, imatge_llindar = cv2.threshold(imatge_suavitzada, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Detectar línies horitzontals utilitzant la transformada de Hough
    linies = cv2.HoughLinesP(imatge_llindar, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)
    
    # Filtrar línies basant-se en l'alçada (proximitat a línies del pentagrama)
    imatge_color = cv2.cvtColor(imatge, cv2.COLOR_GRAY2BGR)
    altures_detectades = []
    if linies is not None:
        for linia in linies:
            x1, y1, x2, y2 = linia[0]
            if abs(y1 - y2) < 10:  # Assegurar-se que la línia és horitzontal
                altures_detectades.append(y1)
    
    # Ordenar i filtrar les línies properes (el rang pot ajustar-se segons l'imatge)
    altures_detectades = sorted(altures_detectades)
    linies_filtrades = []
    llindar_distancia = 28  # Ajusta aquest valor per decidir com de prop poden estar les línies
    for altura in altures_detectades:
        if not linies_filtrades or abs(altura - linies_filtrades[-1]) > llindar_distancia:
            linies_filtrades.append(altura)
    
    # Filtrar les línies de text (evitar les línies que estan massa a prop de la part inferior)
    altura_maxima = imatge.shape[0] - 100  # Evitar línies prop de la part inferior (ajustar valor si cal)
    linies_filtrades = [y for y in linies_filtrades if y < altura_maxima]
    
    # Mostrar quants pentagrames s'han detectat
    num_pentagrames = len(linies_filtrades) // 5  # Suposant que cada pentagrama té 5 línies
    print(f"S'han detectat {num_pentagrames} pentagrames.")
    
    # Dibuixar les línies del pentagrama
    for centre_y in linies_filtrades:
        cv2.line(imatge_color, (0, centre_y), (imatge.shape[1], centre_y), (0, 0, 255), 2)
    
    # Mostrar l'imatge amb les línies del pentagrama detectades
    plt.figure(figsize=(10, 10))
    plt.imshow(cv2.cvtColor(imatge_color, cv2.COLOR_BGR2RGB))
    plt.title("Pentagrames detectats")
    plt.axis("off")
    plt.show()

# Exemple d'ús
try:
    # Pots substituir aquesta línia per ruta_imatge = seleccionar_arxiu() per provar amb l'explorador
    ruta_imatge = "C:/Users/abel/Desktop/UNI/TFG/ProvaPartitura.jpg"  # Canvia a la ruta correcta si no fas servir l'explorador
    detectar_pentagrames(ruta_imatge)
except Exception as e:
    print(f"Error: {e}")
