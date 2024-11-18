from music21 import converter, stream

# Lista de los archivos MusicXML que quieres combinar
archivos_xml = [
    'XAC_ACAN_SMIAu04_005.01.musicxml',
    'XAC_ACAN_SMIAu04_005.02.musicxml',
    'XAC_ACAN_SMIAu04_005.03.musicxml',
    'XAC_ACAN_SMIAu04_005.04.musicxml',
    'XAC_ACAN_SMIAu04_005.05.musicxml',
    'XAC_ACAN_SMIAu04_005.06.musicxml',
    'XAC_ACAN_SMIAu04_005.07.musicxml',
    'XAC_ACAN_SMIAu04_005.08.musicxml',
    'XAC_ACAN_SMIAu04_005.09.musicxml'
]

# Crear un flujo vacío donde se añadirán las partituras
partitura_unida = stream.Score()

# Iterar sobre cada archivo y agregar su contenido al flujo
for archivo in archivos_xml:
    # Cargar el archivo MusicXML
    partitura = converter.parse(archivo)
    
    # Añadir la partitura cargada al flujo de la partitura unida
    partitura_unida.append(partitura)

# Guardar el archivo combinado
partitura_unida.write('musicxml', fp='partitura_unida.musicxml')
print("Los archivos han sido unidos y guardados como 'partitura_unida.musicxml'")
