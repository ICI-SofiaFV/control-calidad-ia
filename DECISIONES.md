# Bitácora de decisiones

Cada decisión del proyecto, por qué se tomó y el dato que la respalda.

| # | Decisión | Justificación (enunciado · materia) | Evidencia |
|---|---|---|---|
| 1 | Mantener el Caso A (control de calidad) | Regla 6: "el caso se mantiene en ambos hitos" | — |
| 2 | Disparador programado (cada mañana) en vez de formulario | R6: el flujo "se dispara solo"; decisión recurrente | Mejora sobre la versión del grupo, que usaba formulario manual |
| 3 | Telegram en vez de WhatsApp | R11 acepta "WhatsApp o Telegram"; el número de prueba de WhatsApp exige un mensaje previo en las últimas 24 h | Práctica "Mi primer flujo", desafío 3 |
| 4 | Usar la planilla *Producción planta* en vez de datos generados | R8: "de preferencia datos reales o públicos"; el enunciado la cita como fuente | 516 filas, 3 líneas, 2 turnos, 5-ene a 4-may-2026 |
| 5 | Descartar filas vacías o imposibles (`num()` devuelve None, no 0) | R8: limpieza y validación. Una celda vacía no es "0 defectos" | 8 filas descartadas de 516 |
| 6 | Sumar los turnos y analizar por día | La decisión es diaria; una serie temporal necesita puntos frecuentes | 86 días por línea |
| 7 | Meta de 2,5 % | Supuesto del proyecto (declarado como limitación) | — |
| 8 | Gráfico de control con base de 60 días y límite = media + 3 desviaciones | R3: detección de anomalías; "gráfico de control" es ejemplo aceptado | Línea B: normal 3,29 %, límite 5,29 % |
| 9 | Mediana de 7 días (no promedio) para el cambio de nivel | La mediana no se deja engañar por un día extremo | Promedio de B en todo el período (3,88 %) esconde el salto de abril |
| 10 | z con error estándar de la mediana (1,25 × desv / √7) y corte z > 3 | Regla clásica de 3 sigmas (0,3 % de falsas alarmas) | Línea B: z = 6,73 → cambio de nivel |
| 11 | Nuevo estado "estable sobre meta" | La estadística (¿cambió?) y el negocio (¿cumple la meta?) son preguntas distintas | Línea B ya estaba sobre la meta (3,3 %) antes de abril |
| 12 | Comparar Holt vs promedio móvil 7 d vs ingenuo | Navaja de Occam: comparar con alternativa simple | Ingenuo pierde en las 3 líneas |
| 13 | Elegir α y β con los primeros 60 días y comparar en los 26 restantes | Separar entrenamiento y prueba (materia de series de tiempo) | B: α = 0,4, β = 0,1 |
| 14 | Holt solo se recomienda si mejora ≥ 5 % al mejor simple | Navaja de Occam: un modelo complejo debe ganar por margen claro | A: +0,1 % (empate) · B: +11,1 % (Holt) · C: −3,0 % |
| 15 | Python calcula la decisión esperada, pero no se la entrega al LLM | Control de alucinaciones; mismo patrón que Python (3) en el Ejercicio 5 | Se usará para verificar la respuesta del LLM |
| 16 | Umbral de 1,5 veces la meta para detener la línea | Supuesto heredado del grupo; debe calibrarse con el responsable de calidad | B: 2,16 veces la meta → detener |
| 17 | n8n Cloud (prueba de 14 días) con nodo Code en Python | Así lo usa el profesor en clase; el flujo corre sin depender del computador (R6) | Prueba: 14 días, 1.000 ejecuciones; vence el 23-nov, después del Hito 2 |
| 18 | Mismo código Python en el Mac y en n8n; en n8n se agrega `return analizar(_items)` | R2: nodo Code con lógica propia. Probar primero localmente facilita encontrar errores | Resultados idénticos en ambos (B: z = 6,73; 2,16 veces la meta) |
| 19 | Modelo Gemini flash vigente (gemini-3.8-flash / flash-latest), temperatura 0 | Temperatura 0 = misma respuesta ante mismos datos (consistencia). Google retira modelos antiguos (2.5-flash dio error 404) | El nodo reintenta 3 veces ante fallas |
| 20 | Prompt con formato de respuesta explícito + modelo Flash-Lite | Sin formato explícito el LLM respondió "Seguir." (mayúscula y punto) y el esquema lo rechazó, causando reintentos. Flash Latest tardó ~5 min por respuesta | Prueba de diagnóstico sin esquema: decisiones correctas en A, B y C, pero formato inválido |
| 21 | Basic LLM Chain + Gemini Flash-Lite (temp. 0) + Structured Output Parser con enum | R1: JSON con diagnóstico, recomendación, prioridad y justificación. Flash-Lite responde en segundos | 3/3 recomendaciones coinciden con la regla de Python; cifras citadas correctas |
| 22 | Nodo Merge + "Verificar IA" (Python): la decisión final es la regla; si la IA no coincide, se pide revisión humana | "El LLM lee, las reglas deciden"; mismo patrón que Python (3) del Ejercicio 5; control de alucinaciones | Prueba: IA coincide 3/3; caso simulado de desacuerdo → se aplica la regla y se marca revisión humana |
| 23 | Registro en hoja `Registro` + un solo correo HTML ordenado por prioridad | Instrucciones: registro histórico y Gmail (R11). Un resumen con lo urgente primero en vez de 3 correos | Registro con columnas IA_coincide y Revisión_humana para trazabilidad |
| 24 | Se reemplaza Telegram (decisión 3) por WhatsApp Cloud API (número de prueba de Meta) | R11 acepta "WhatsApp o Telegram". En Chile, Telegram cobra el SMS de verificación para crear una cuenta nueva ($990 CLP); WhatsApp es gratis | Limitación: el número de prueba solo envía si el destinatario escribió en las últimas 24 h y admite máximo 5 números verificados |

## Resultados del análisis (al 4-may-2026)

| Línea | Estado | Mediana 7 d | Veces la meta | z | MAE Holt | MAE Prom. móvil | MAE Ingenuo | Modelo recomendado | Decisión por reglas |
|---|---|---|---|---|---|---|---|---|---|
| A | estable | 1,57 % | 0,63 | −1,83 | 0,00373 | 0,00374 | 0,00583 | promedio móvil | seguir · baja |
| B | cambio de nivel | 5,41 % | 2,16 | 6,73 | 0,01024 | 0,01151 | 0,01205 | Holt | detener · alta |
| C | estable | 1,16 % | 0,46 | −1,18 | 0,00203 | 0,00197 | 0,00287 | promedio móvil | seguir · baja |

Código: `codigo/analisis.py` · Datos: `datos/datos.csv`
