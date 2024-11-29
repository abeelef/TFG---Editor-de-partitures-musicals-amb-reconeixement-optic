#Cal fer pip install opencv-python-headless
import cv2
import numpy as np
from tkinter import Tk, filedialog
from matplotlib import pyplot as plt

def seleccionar_archivo():
    """Abre un cuadro de diálogo para seleccionar un archivo de imagen."""
    Tk().withdraw()  # Oculta la ventana principal de Tkinter
    archivo_seleccionado = filedialog.askopenfilename(
        title="Seleccionar imagen de partitura",
        filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png *.bmp")]
    )
    if not archivo_seleccionado:
        raise FileNotFoundError("No se seleccionó ningún archivo.")
    return archivo_seleccionado

def detectar_pentagramas(imagen_path):
    """Detecta los pentagramas en una imagen de partitura y marca un único punto delante de cada uno."""
    # Cargar la imagen en escala de grises
    imagen = cv2.imread(imagen_path, cv2.IMREAD_GRAYSCALE)
    if imagen is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {imagen_path}")

    # Mejorar el contraste y eliminar ruido con un suavizado
    imagen_suavizada = cv2.GaussianBlur(imagen, (5, 5), 0)
    
    # Realizar un umbral para mejorar la detección de bordes (transformar la imagen en blanco y negro)
    _, imagen_umbral = cv2.threshold(imagen_suavizada, 150, 255, cv2.THRESH_BINARY_INV)

    # Detectar líneas horizontales utilizando la transformada de Hough
    lineas = cv2.HoughLinesP(imagen_umbral, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)

    # Dibujar las líneas detectadas en la imagen
    imagen_color = cv2.cvtColor(imagen, cv2.COLOR_GRAY2BGR)
    if lineas is not None:
        for linea in lineas:
            x1, y1, x2, y2 = linea[0]
            cv2.line(imagen_color, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Dibujar línea roja

    # Mostrar la imagen con las líneas detectadas
    plt.figure(figsize=(10, 10))
    plt.imshow(cv2.cvtColor(imagen_color, cv2.COLOR_BGR2RGB))
    plt.title("Pentagramas detectados")
    plt.axis("off")
    plt.show()

# Ejemplo de uso
try:
    # Puedes reemplazar esta línea por ruta_imagen = seleccionar_archivo() para probar con el explorador
    ruta_imagen = "C:/Users/abel/Desktop/UNI/TFG/ProvaPartitura.png"  # Cambiar a la ruta correcta si no usas el explorador
    detectar_pentagramas(ruta_imagen)
except Exception as e:
    print(f"Error: {e}")




