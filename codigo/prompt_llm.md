# Prompt y salida estructurada del LLM (R1)

- **Nodo:** Basic LLM Chain "Interpretar con IA"
- **Modelo:** Google Gemini Flash-Lite Latest, temperatura 0, reintento hasta 3 veces
- **Entrada:** el resultado del análisis en Python (no los datos crudos), con las cifras ya formateadas.
- **No recibe** `regla_recomendacion` ni `regla_prioridad`: se usan después en "Verificar IA".

## Prompt

```
(pega aquí el prompt completo copiado desde el nodo "Interpretar con IA")
```

## Esquema JSON (Structured Output Parser)

```json
{
  "type": "object",
  "properties": {
    "diagnostico": { "type": "string" },
    "recomendacion": {
      "type": "string",
      "enum": ["seguir", "ajustar la línea", "detener la línea", "revisión humana antes de actuar"]
    },
    "prioridad": { "type": "string", "enum": ["alta", "media", "baja"] },
    "justificacion": { "type": "string" }
  },
  "required": ["diagnostico", "recomendacion", "prioridad", "justificacion"]
}
```
