# =====================================================================
# Verificar IA: compara la decisión del LLM con la regla de negocio en Python.
# "El LLM lee, las reglas deciden" (mismo patrón que Python (3) del Ejercicio 5).
# =====================================================================

salida = []
for item in _items:
    d = item["json"]
    ia = d.get("output", {})                      # respuesta del LLM

    ia_rec = ia.get("recomendacion")
    ia_pri = ia.get("prioridad")
    regla_rec = d["regla_recomendacion"]          # lo que dicen las reglas
    regla_pri = d["regla_prioridad"]

    coincide = (ia_rec == regla_rec) and (ia_pri == regla_pri)

    if coincide:
        nota = "La recomendación de la IA coincide con las reglas de negocio."
    else:
        nota = (f"La IA propuso '{ia_rec}' (prioridad {ia_pri}), pero las reglas indican "
                f"'{regla_rec}' (prioridad {regla_pri}). Se aplica la regla y se pide revisión humana.")

    resultado = dict(d)                           # conserva todas las cifras del análisis
    resultado.pop("output", None)
    resultado.update({
        "diagnostico": ia.get("diagnostico", ""),
        "justificacion": ia.get("justificacion", ""),
        "recomendacion_ia": ia_rec,
        "prioridad_ia": ia_pri,
        "recomendacion": regla_rec,               # decisión final: siempre la regla
        "prioridad": regla_pri,
        "ia_coincide": coincide,
        "requiere_revision_humana": (not coincide) or d["estado"] == "valor_atipico",
        "nota_verificacion": nota,
    })
    salida.append({"json": resultado})

return salida
