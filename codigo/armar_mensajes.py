# =====================================================================
# Armar mensajes: 3 líneas entran -> 1 correo HTML + 1 mensaje de WhatsApp
# Ordena por prioridad (lo urgente primero), igual que la Estación 5 del curso.
# =====================================================================

def pct(x):                      # 0.05407 -> "5,41 %"
    return f"{x * 100:.2f}".replace(".", ",") + " %"

def dec(x):                      # 2.16 -> "2,16"
    return f"{x:.2f}".replace(".", ",")

ORDEN = {"alta": 0, "media": 1, "baja": 2}
COLOR = {"alta": "#c5221f", "media": "#b06000", "baja": "#137333"}
FONDO = {"alta": "#fce8e6", "media": "#fef7e0", "baja": "#e6f4ea"}
ESTADO = {"cambio_de_nivel": "Cambio de nivel sostenido", "valor_atipico": "Valor atípico aislado",
          "estable_sobre_meta": "Estable, pero sobre la meta", "estable": "Proceso estable"}
MODELO = {"holt": "Holt", "promedio_movil": "Promedio móvil 7 días", "ingenuo": "Ingenuo"}

lineas = sorted([it["json"] for it in _items], key=lambda d: ORDEN[d["prioridad"]])
peor = lineas[0]
fecha_datos = peor["fecha_ultima"]

# ---------- Correo HTML ----------
bloques = ""
for d in lineas:
    p = d["prioridad"]
    revision = ("<p style='color:#c5221f'><b>⚠ Requiere revisión humana.</b> " + d["nota_verificacion"] + "</p>"
                if d["requiere_revision_humana"] else "")
    pronostico = d["pronostico_holt"] if d["modelo_recomendado"] == "holt" else d["pronostico_promedio_movil"]
    bloques += f"""
<div style="border-left:6px solid {COLOR[p]};background:{FONDO[p]};padding:12px 16px;margin:14px 0">
  <h3 style="margin:0 0 6px 0">{d['linea']} · {d['recomendacion'].capitalize()}
      <span style="color:{COLOR[p]}">(prioridad {p})</span></h3>
  <p style="margin:4px 0"><b>Estado:</b> {ESTADO[d['estado']]}</p>
  <p style="margin:4px 0"><b>Diagnóstico:</b> {d['diagnostico']}</p>
  <p style="margin:4px 0"><b>Justificación:</b> {d['justificacion']}</p>
  {revision}
  <table cellpadding="4" style="font-size:13px;border-collapse:collapse">
    <tr><td>Tasa mediana 7 días</td><td><b>{pct(d['tasa_mediana_7d'])}</b> ({dec(d['veces_la_meta'])} veces la meta de 2,5 %)</td></tr>
    <tr><td>Tasa normal / límite de control</td><td>{pct(d['promedio_normal'])} / {pct(d['limite_superior'])}</td></tr>
    <tr><td>Pronóstico próximo día</td><td>{pct(pronostico)} ({MODELO[d['modelo_recomendado']]})</td></tr>
    <tr><td>Detención promedio 7 días</td><td>{d['detencion_media_7d_min']} min/día</td></tr>
  </table>
</div>"""

html = f"""<div style="font-family:Arial,sans-serif;max-width:640px">
<h2 style="color:#091D44">Control de calidad por línea</h2>
<p>Datos hasta el <b>{fecha_datos}</b> · {len(lineas)} líneas analizadas · {peor['filas_descartadas']} filas descartadas en la limpieza.</p>
{bloques}
<p style="color:#666;font-size:12px">Generado automáticamente por n8n: análisis en Python (gráfico de control y pronóstico),
interpretación con Gemini y verificación con reglas de negocio. La decisión final la toma el responsable de calidad.</p>
</div>"""

asunto = f"[{peor['prioridad'].upper()}] Control de calidad {fecha_datos}: {peor['linea']} – {peor['recomendacion']}"

# ---------- WhatsApp (texto corto) ----------
iconos = {"alta": "🔴", "media": "🟡", "baja": "🟢"}
texto = f"CONTROL DE CALIDAD · datos al {fecha_datos}\n"
for d in lineas:
    texto += (f"\n{iconos[d['prioridad']]} {d['linea']}: {d['recomendacion'].upper()} (prioridad {d['prioridad']})\n"
              f"   Tasa 7 días {pct(d['tasa_mediana_7d'])} · {dec(d['veces_la_meta'])} veces la meta")
    if d["requiere_revision_humana"]:
        texto += "\n   ⚠ Requiere revisión humana"
texto += "\n\nEl detalle está en el correo."

return [{"json": {"asunto": asunto, "html": html, "mensaje_corto": texto,
                  "hay_prioridad_alta": peor["prioridad"] == "alta"}}]
