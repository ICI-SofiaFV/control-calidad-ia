# Control de calidad automatizado por línea de producción

Hito 1 – Certamen 2 · IA Generativa para la Gestión Industrial
Autora: Sofía Fariña

## 1. Problema (R7)

Una planta manufacturera tiene tres líneas de producción (L1, L2 y L3) que fabrican
cerca de 1.000 piezas diarias cada una. Hoy, detectar que una línea empezó a producir
más piezas defectuosas exige revisar planillas a mano, y un empeoramiento sostenido
puede pasar varios días sin verse, lo que genera merma.

| Elemento | Definición |
|---|---|
| Industria | Manufactura (3 líneas de producción) |
| Usuario que decide | Responsable de calidad de la planta |
| Decisión recurrente | Cada mañana, para cada línea: seguir, ajustar, detener o pedir revisión humana |
| Indicador de negocio | Tasa de defectos = n° de piezas defectuosas ÷ n° de piezas producidas |
| Meta de calidad | Tasa de defectos ≤ 2,5 % |

El sistema revisa las tres líneas automáticamente cada mañana, detecta si hubo un
cambio real o solo un dato aislado, propone una decisión con un LLM y avisa al
responsable por Gmail y Telegram.
