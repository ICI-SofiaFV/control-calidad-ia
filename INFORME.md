# Informe Hito 1 · Control de calidad automatizado por línea de producción

IA Generativa para la Gestión Industrial · Certamen 2 · Autora: Sofía Fariña · Noviembre 2026

---

## 1. Problema y usuario

**Caso A: control de calidad en manufactura.** Una planta tiene tres líneas de producción
(A, B y C) que trabajan en turno mañana y tarde. Cada turno registra unidades producidas,
unidades defectuosas y minutos de detención. Hoy el responsable de calidad debe revisar la
planilla a mano: es lento y un empeoramiento sostenido puede pasar semanas sin verse.
En los datos usados, la Línea B pasó de 3,3 % a más de 5 % de defectos en abril.

| Elemento | Definición |
|---|---|
| Usuario que decide | Responsable de calidad de la planta |
| Decisión recurrente | Cada mañana, para cada línea: seguir, ajustar, detener o pedir revisión humana |
| Indicador de negocio | Tasa de defectos = defectuosas ÷ producidas (merma) |
| Meta | Tasa ≤ 2,5 % (supuesto del proyecto) |

**Objetivo:** que el diagnóstico llegue solo, antes de que parta el turno de mañana, con una
recomendación explicada y trazable, dejando la decisión final en manos de una persona.

## 2. Datos

- **Fuente:** planilla *Producción planta* del Módulo IV del curso, citada en el enunciado. Cargada en Google Sheets.
- **Contenido:** 516 filas (5-ene a 4-may-2026, 86 días hábiles × 3 líneas × 2 turnos).
- **Limpieza (Python):** se descartaron 8 filas (sin línea o sin unidades producidas) y se validan
  casos imposibles (unidades ≤ 0, defectos negativos o mayores que las unidades). Una celda vacía
  no se trata como 0, porque eso mejoraría la tasa artificialmente.
- **Transformación:** se suman los dos turnos de cada día → serie diaria de tasa de defectos por línea.
- **Limitaciones:** origen real desconocido; la serie termina el 4-may; solo días hábiles; sin causa del defecto.

## 3. Diagrama del flujo (n8n)

| Paso del enunciado | Implementación |
|---|---|
| 1. Disparador | Schedule Trigger diario a las 7:00 (America/Santiago) + disparador manual para pruebas |
| 2. Ingesta | Google Sheets, hoja `produccion_planta` |
| 3. Python | Nodo Code (Python nativo, sin librerías): limpieza, modelo e indicadores |
| 4. LLM | Basic LLM Chain + Gemini Flash-Lite (temperatura 0) + Structured Output Parser |
| 5. Acción | Registro en hoja `Registro`, correo HTML por Gmail y alerta corta por WhatsApp |
| Robustez | Reintento del LLM (3 veces), esquema con `enum`, verificación con reglas y workflow de alerta de errores |

## 4. Modelo y comparación con la alternativa simple

### 4.1 Detección de anomalías (gráfico de control)

- **Lo normal:** primeros 60 días → media y desviación estándar; límite superior = media + 3σ.
- **Lo de ahora:** mediana de los últimos 7 días. Se usa la mediana porque un solo día extremo no la mueve.
- **z de cambio** = (mediana 7 d − media normal) / (1,25 · σ / √7). Si z > 3, hay cambio de nivel
  (regla de 3 sigmas; 1,25 corrige el error estándar de la mediana).
- **Estados:** cambio de nivel → valor atípico (un día de los últimos 3 sobre el límite) →
  estable sobre meta → estable. Este orden prioriza lo más grave.

| Línea | Normal | Límite | Mediana 7 d | z | Veces la meta | Estado |
|---|---|---|---|---|---|---|
| A | 1,89 % | 2,97 % | 1,57 % | −1,83 | 0,63 | Estable |
| B | 3,29 % | 5,29 % | 5,41 % | 6,73 | 2,16 | Cambio de nivel |
| C | 1,30 % | 2,05 % | 1,16 % | −1,18 | 0,46 | Estable |

### 4.2 Pronóstico: Holt frente a modelos simples (navaja de Occam)

- **Ingenuo:** mañana igual que hoy. **Promedio móvil 7 d:** promedio de la última semana.
  **Holt:** sigue nivel (α) y tendencia (β).
- **Entrenamiento:** los primeros 60 días, donde se eligen α y β por búsqueda en grilla (45 combinaciones).
  **Prueba:** los 26 días restantes, no vistos. Métrica: MAE.
- **Regla de Occam:** Holt solo se recomienda si mejora en ≥ 5 % al mejor modelo simple.

| Línea | Holt (α, β) | MAE Holt | MAE Prom. móvil | MAE Ingenuo | Mejora Holt | Recomendado |
|---|---|---|---|---|---|---|
| A | 0,1 / 0,05 | 0,00373 | 0,00374 | 0,00583 | +0,1 % | Promedio móvil |
| B | 0,4 / 0,1 | 0,01024 | 0,01151 | 0,01205 | +11,1 % | **Holt** |
| C | 0,4 / 0,2 | 0,00203 | 0,00197 | 0,00287 | −3,0 % | Promedio móvil |

**Discusión:** el ingenuo pierde siempre, porque copia el ruido diario. Holt gana claramente solo en
la Línea B, la única que cambió, porque se adapta antes al nuevo nivel. En las líneas estables no hay
tendencia que seguir: el modelo complejo no aporta y se prefiere el simple. Además, la **decisión no
depende del pronóstico, sino del gráfico de control**: el pronóstico dice cuánto viene; el gráfico
dice si eso es normal.

## 5. Prompt del LLM y ejemplo de salida

**Principio de diseño: "el LLM lee, las reglas deciden".**
1. El LLM recibe solo resultados ya calculados, con las cifras formateadas (5,41 %), para que copie y no calcule.
2. El prompt incluye las reglas de decisión, instrucciones de redacción ("usa SOLO las cifras entregadas")
   y un formato de respuesta explícito.
3. Un esquema JSON con `enum` rechaza cualquier respuesta fuera de formato.
4. El nodo **Verificar IA** compara la respuesta con la regla calculada en Python, que no se entrega
   al LLM. Si difieren, se aplica la regla y se marca revisión humana.

Prompt completo y esquema: [`codigo/prompt_llm.md`](codigo/prompt_llm.md).

**Ejemplo de entrada (Línea B, resumida):**

**Salida real de Gemini:**
```json
{
  "diagnostico": "Se registra un cambio de nivel desfavorable en la calidad de la línea de producción. La tasa actual de defectos excede significativamente los parámetros permitidos.",
  "recomendacion": "detener la línea",
  "prioridad": "alta",
  "justificacion": "El análisis muestra que las veces que supera la meta es 2,16 y la tasa mediana de los últimos 7 días es 5,41 %."
}
```
**Verificación:** coincide con la regla (detener · alta) → `IA_coincide = sí`.

**Problemas encontrados y resueltos:**
- Sin formato explícito, el LLM respondió "Seguir." (mayúscula y punto). El esquema lo rechazó y el nodo
  reintentaba sin fin. Se agregó la sección "Formato de respuesta" al prompt.
- `gemini-2.5-flash` fue retirado por Google (error 404), y "Flash Latest" tardó ~5 min por respuesta
  porque razona antes de contestar. Se eligió Flash-Lite: responde en segundos y la tarea es redactar, no razonar.

## 6. Evidencia y resultados

| Ejecución | Datos | Línea A | Línea B | Línea C | IA coincide |
|---|---|---|---|---|---|
| 1 | Al 4-may (originales) | Seguir · baja | Detener · alta | Seguir · baja | 3/3 |
| 2 | + 5-may simulado | Seguir · baja | Detener · alta | Seguir · baja | 3/3 |
| 3 | + 6-may simulado, pico de 5,1 % en A | **Revisión humana · media** | Detener · alta | Seguir · baja | 3/3 |

En la ejecución 3, la tasa de un día de la Línea A duplicó la meta, pero su mediana de 7 días se mantuvo
en 1,78 %: el sistema no detuvo la línea por una posible falsa alarma y pidió revisión humana.
Cada ejecución envió un correo HTML ordenado por prioridad (asunto con la peor prioridad), un WhatsApp
y 3 filas al registro. Capturas en [`evidencia/`](evidencia/).

## 7. Limitaciones

| Limitación | Efecto | Mitigación / próximo paso |
|---|---|---|
| Datos de referencia del curso, hasta el 4-may | Cada mañana se analiza la misma serie | En operación real, los supervisores agregan filas diarias |
| Meta (2,5 %) y umbral de detención (1,5×) supuestos | Decisiones sensibles a estos valores | Calibrar con el responsable de calidad; están en constantes del código |
| Base "normal" fija (primeros 60 días) | Si la línea se repara, la base no se actualiza | Recalcular la fase I tras cada intervención |
| Número de prueba de WhatsApp | Ventana de 24 h, máx. 5 números, token de 24 h | Número propio con plantillas aprobadas y token permanente |
| Proveedor externo de IA | Modelos retirados o lentos | Modelo fijado en el flujo + reintentos + alerta de errores |
| El LLM puede redactar con imprecisión | Diagnóstico poco claro | Solo copia cifras dadas; la decisión la valida Python; persona en el circuito |
| Sin causa del defecto | No se sabe por qué falla la línea | Hito 2: clasificar reportes de no conformidad con Transformers |

**Próximos pasos (Hito 2):** clasificación de imágenes de piezas (modelo preentrenado), LSTM/GRU frente
a Holt, componente Transformer sobre texto, aprobación humana antes de detener una línea, tablero y ROI.

---
Bitácora de decisiones: [`DECISIONES.md`](DECISIONES.md) · Código: [`codigo/`](codigo/) · Flujos: [`flujo/`](flujo/)
