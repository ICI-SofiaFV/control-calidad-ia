# Fuente de los datos

- **Archivo:** `datos.csv`, exportado desde Google Sheets.
- **Origen:** planilla *Producción planta*, material de referencia del curso
  IA Generativa para la Gestión Industrial (Módulo IV), citada en el enunciado
  del proyecto final como fuente de datos.
- **Contenido:** 516 filas (5-ene-2026 a 4-may-2026), una por día, línea y turno.
- **Filas sucias:** 8 (sin línea o sin unidades producidas); se descartan en
  `codigo/analisis.py`.
