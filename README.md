# Control de calidad automatizado por línea de producción

Hito 1 – Certamen 2 · IA Generativa para la Gestión Industrial

Autora: Sofía Fariña

## 1. Problema (R7)

Una planta manufacturera tiene tres líneas de producción (Línea A, B y C) que trabajan
en dos turnos (mañana y tarde) y fabrican entre 1.800 y 3.000 piezas diarias cada una.
Hoy, detectar que una línea empezó a producir más piezas defectuosas exige revisar
planillas a mano, y un empeoramiento sostenido puede pasar semanas sin verse, lo que
genera merma.

| Elemento | Definición |
|---|---|
| Industria | Manufactura (3 líneas de producción, 2 turnos) |
| Usuario que decide | Responsable de calidad de la planta |
| Decisión recurrente | Cada mañana, para cada línea: seguir, ajustar, detener o pedir revisión humana |
| Indicador de negocio | Tasa de defectos = n° de piezas defectuosas ÷ n° de piezas producidas |
| Meta de calidad | Tasa de defectos ≤ 2,5 % |

El sistema revisa las tres líneas automáticamente cada mañana, detecta si hubo un
cambio real o solo un dato aislado, propone una decisión con un LLM y avisa al
responsable por Gmail y Telegram.

## 2. Datos (R8)

**Origen:** planilla *Producción planta*, material de referencia del curso (Módulo IV),
citada en el enunciado del proyecto como fuente de datos. Se cargó en Google Sheets.

| Característica | Detalle |
|---|---|
| Período | 5 de enero al 4 de mayo de 2026 (86 días hábiles, lunes a viernes) |
| Filas | 516 (una por día, línea y turno) |
| Columnas | fecha, mes, linea, turno, unidades_producidas, unidades_defectuosas, minutos_detencion |
| Hoja de salida | `Registro`: historial de cada decisión del sistema |

**Limpieza y validación (en Python):**
- Se descartan las filas sin línea o sin unidades producidas (8 filas en la planilla original).
- Se descartan las filas imposibles: unidades ≤ 0, defectos negativos o más defectos que unidades.
- Los dos turnos de cada día se suman para obtener una tasa diaria por línea.

**Limitaciones:**
- Se desconoce si la planilla proviene de una planta real o fue preparada para el curso.
- La serie termina el 4 de mayo de 2026: en operación real, los supervisores agregarían filas cada día.
- Solo hay días hábiles y un tipo de defecto, sin su causa.
- La meta de 2,5 % es un supuesto del proyecto, no un dato de la planta.
