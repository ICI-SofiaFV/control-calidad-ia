# Control de calidad automatizado por línea de producción

Hito 1 – Certamen 2 · IA Generativa para la Gestión Industrial

Autora: Sofía Fariña

Flujo en **n8n** que cada mañana revisa la tasa de defectos de tres líneas de producción,
detecta si hubo un cambio real o solo un día aislado (Python), pide a un **LLM (Gemini)**
que explique la decisión, **verifica** que la IA respete las reglas del negocio y avisa
al responsable por **Gmail y WhatsApp**, dejando todo registrado en Google Sheets.

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
- Una celda vacía se trata como "dato desconocido" y no como 0, para no mejorar artificialmente la tasa.
- Los dos turnos de cada día se suman para obtener una tasa diaria por línea.

## 3. Cómo funciona (R6)

```
⏰ Cada día 7:00 ─┐
                  ├─► Leer datos ─► Análisis Python ─┬─► Interpretar con IA ─┐
⚡ Probar ahora ──┘                                  └───────────────────────┴─► Juntar ─► Verificar IA ─┬─► Registro (Sheets)
                                                                                                         └─► Armar mensajes ─► Gmail ─► WhatsApp

Flujo aparte "Alerta de errores": si cualquier nodo falla, envía un correo con el nodo y el error.
```

| Nodo | Qué hace |
|---|---|
| Cada día 7:00 / Probar ahora | Disparador programado (zona horaria America/Santiago) y botón para pruebas |
| Leer datos | Lee las 516 filas de Google Sheets |
| Análisis Python | Limpieza, gráfico de control, comparación de modelos y regla de decisión ([`codigo/analisis.py`](codigo/analisis.py)) |
| Interpretar con IA | Gemini Flash-Lite (temperatura 0) recibe solo los resultados y devuelve un JSON validado ([`codigo/prompt_llm.md`](codigo/prompt_llm.md)) |
| Juntar análisis e IA | Une los resultados de Python con la respuesta de la IA |
| Verificar IA | Compara la recomendación de la IA con la regla de negocio; si no coinciden, aplica la regla y pide revisión humana ([`codigo/verificar_ia.py`](codigo/verificar_ia.py)) |
| Registro | Agrega una fila por línea a la hoja `Registro` |
| Armar mensajes | Une las 3 líneas en un correo HTML y un mensaje corto, ordenados por prioridad ([`codigo/armar_mensajes.py`](codigo/armar_mensajes.py)) |
| Gmail / WhatsApp | Gmail lleva el detalle; WhatsApp, la alerta corta al celular (R11) |

## 4. Modelo y comparación con alternativas simples (R2, R3)

**Detección de anomalías (gráfico de control):** "lo normal" son los primeros 60 días
(límite superior = media + 3 desviaciones). La última semana se resume con la **mediana**
(robusta a un día extremo) y se clasifica la línea en:

| Estado | Condición | Decisión | Prioridad |
|---|---|---|---|
| Cambio de nivel | z > 3 y más de 1,5 veces la meta | Detener la línea | Alta |
| Cambio de nivel | z > 3 y hasta 1,5 veces la meta | Ajustar la línea | Media |
| Valor atípico | Un día de los últimos 3 sobre el límite, sin cambio sostenido | Revisión humana antes de actuar | Media |
| Estable sobre meta | Sin cambio, pero la mediana supera la meta | Ajustar la línea | Media |
| Estable | Sin cambio y cumple la meta | Seguir | Baja |

**Pronóstico (navaja de Occam):** se comparan tres modelos que predicen la tasa del día
siguiente. Holt ajusta α y β con los primeros 60 días y todos se evalúan en los 26 días
restantes (no vistos). Holt solo se recomienda si mejora en al menos 5 % al mejor modelo simple.

| Línea | Estado | Mediana 7 d | Veces la meta | MAE Holt | MAE Prom. móvil 7 d | MAE Ingenuo | Modelo recomendado |
|---|---|---|---|---|---|---|---|
| A | Estable | 1,57 % | 0,63 | 0,00373 | 0,00374 | 0,00583 | Promedio móvil (Holt +0,1 %) |
| B | Cambio de nivel | 5,41 % | 2,16 | 0,01024 | 0,01151 | 0,01205 | **Holt (+11,1 %)** |
| C | Estable | 1,16 % | 0,46 | 0,00203 | 0,00197 | 0,00287 | Promedio móvil (Holt −3,0 %) |

**Conclusión:** el modelo ingenuo pierde en las tres líneas, así que promediar sí aporta.
Holt solo se justifica en la Línea B, la única con un cambio real (abril), porque sigue la tendencia.
En las líneas estables basta el promedio móvil.

## 5. IA generativa con control (R1)

- El LLM recibe los **resultados** del análisis, con cifras ya formateadas; no calcula nada.
- Responde un JSON con `diagnostico`, `recomendacion`, `prioridad` y `justificacion`,
  validado con un esquema (`enum`) y con reintento ante fallas.
- **"El LLM lee, las reglas deciden":** Python calcula la decisión esperada sin mostrársela a la IA
  y luego la compara. La decisión final siempre es la regla; la IA aporta la explicación.
  Cada ejecución registra `IA_coincide` y `Revisión_humana` (trazabilidad).

## 6. Resultados (evidencia)

| Ejecución | Datos | Línea A | Línea B | Línea C |
|---|---|---|---|---|
| 1 | Originales (al 4-may) | Seguir · baja | Detener · alta | Seguir · baja |
| 2 | + día 5-may simulado (normal) | Seguir · baja | Detener · alta | Seguir · baja |
| 3 | + día 6-may simulado (pico de 5,1 % en A) | **Revisión humana · media** | Detener · alta | Seguir · baja |

En las tres ejecuciones la IA coincidió con las reglas (3/3 líneas). En la ejecución 3, la
mediana de 7 días de la Línea A se mantuvo en 1,78 %: el sistema distinguió un día aislado
de un problema real. Capturas en [`evidencia/`](evidencia/).

## 7. Limitaciones

- Se desconoce si la planilla proviene de una planta real o fue preparada para el curso.
- La serie termina el 4-may-2026: en operación real se agregarían filas cada día.
  Los días 5 y 6 de mayo de la evidencia son simulados y se borraron después.
- La meta de 2,5 % y el umbral de 1,5 veces la meta son supuestos; deben calibrarse con el responsable de calidad.
- Solo hay días hábiles y un tipo de defecto, sin su causa.
- WhatsApp usa el número de prueba de Meta: solo envía texto libre si el destinatario escribió
  en las últimas 24 h, admite máximo 5 números y el token temporal dura 24 h.
- Dependencia de un proveedor externo de IA: Google retiró `gemini-2.5-flash` durante el desarrollo.

## 8. Estructura del repositorio

```
├── README.md          este documento
├── INFORME.md         informe del Hito 1
├── DECISIONES.md      bitácora: cada decisión, su justificación y su evidencia
├── codigo/            Python de cada nodo y prompt del LLM
├── datos/             datos.csv y su ficha (FUENTE.md)
├── flujo/             flujos de n8n exportados sin credenciales
└── evidencia/         capturas de las ejecuciones
```

**Para replicarlo:** importar los JSON de `flujo/` en n8n, reemplazar `CORREO_DEL_RESPONSABLE`,
`56XXXXXXXXX`, `ID_DEL_NUMERO_DE_WHATSAPP` y `URL_DE_TU_HOJA`, y crear credenciales propias
de Google Sheets, Gmail, Gemini y WhatsApp. El código Python usa solo la biblioteca estándar.

## 9. Uso de IA

Se usó Claude (Anthropic) como tutor: para guiar la construcción paso a paso,
revisar código y ayudar a diagnosticar errores. Cada nodo fue construido, probado y comprendido
por la autora; las decisiones y su justificación están registradas en `DECISIONES.md`.
