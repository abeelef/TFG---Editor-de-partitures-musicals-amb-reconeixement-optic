# Gestor de Partitures - Treball Final de Grau

## Descripció

Aquest projecte és un gestor de partitures creat com a treball final de grau dissenyat per a agilitzar el traspàs a digital de partitures musicals d'un arxiu del segle passat junt amb un OMR (reconeixement òptic musical). Permet obrir imatges de partitures, retallar línies d'elles, ajustar paràmetres com el brillantor, i guardar les partitures modificades utilitzant MuseScore. A més, facilita la navegació per les línies retallades i la seva integració amb arxius MusicXML associats.

## Característiques Principals

- **Obrir imatges de partitures**: Permet obrir arxius d'imatge en formats PNG, JPG i JPEG.
- **Retallar línies de la partitura**: Es poden retallar línies específiques de la partitura i visualitzar-les de manera independent.
- **Ajustar el brillantor**: Permet ajustar el brillantor de la imatge de la partitura.
- **Navegar entre línies retallades**: Navega per les línies retallades de la partitura anteriorment.
- **MuseScore Integrat**: El projecte utilitza MuseScore4 per obrir,editar i guardar partitures en format MusicXML associades a la imatge de la partitura.
- **Zoom i Drag**: Permet fer zoom sobre la partitura i desplaçar-la (drag) per veure'n millor les línies retallades.
- **Compatibilitat amb OMR**: Codi preparat de cara a la unió amb el moment de la finalització del OMR.
- etc...

## Requisits

Per executar aquest projecte, hauràs d'instal·lar les següents dependències:

- Python 3.x
- `Pillow` - Per al tractament d'imatges.
- `pygetwindow` - Per obtenir finestres actives de l'aplicació MuseScore.
- `pyautogui` - Per controlar el ratolí i el teclat (simulant la interacció amb MuseScore).
- `music21` - Per treballar amb arxius MusicXML.
- `tkinter` - Per la interfície gràfica d'usuari (GUI).
- `music21` - Caldrà tenir tot el repositori de music21 recent per a la funcionalitat correcte del notebook
- `psutil` - Per a tota la gestió de processos
-  `sqlite3` - Per a treballar amb la base de dades



