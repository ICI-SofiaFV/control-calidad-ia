# =====================================================================
# Análisis de calidad por línea de producción (Hito 1 · Caso A)
# Autora: Sofía Fariña
# Python puro (sin librerías): así puede correr dentro del nodo Code de n8n.
# =====================================================================


# ---------- PARTE 4.1: limpiar los datos y sumar los turnos ----------

def num(valor):
    #Convierte texto a número. Si la celda viene vacía o con texto, devuelve None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def limpiar_y_agrupar(items):
    #Recibe las filas de la planilla (una por turno) y devuelve,
    # para cada línea, su serie diaria ordenada por fecha.
    dias = {}          # clave: (linea, fecha) -> totales del día
    descartadas = 0    # contador de filas sucias

    for item in items:
        fila = item["json"]
        linea = fila.get("linea")
        fecha = fila.get("fecha")
        unidades = num(fila.get("unidades_producidas"))
        defectos = num(fila.get("unidades_defectuosas"))
        detencion = num(fila.get("minutos_detencion")) or 0

        # Validación: se descarta la fila si le falta algo o es imposible
        if (not linea or not fecha or unidades is None or defectos is None
                or unidades <= 0 or defectos < 0 or defectos > unidades):
            descartadas += 1
            continue

        # Sumar los dos turnos (mañana y tarde) del mismo día
        clave = (linea, str(fecha)[:10])
        if clave not in dias:
            dias[clave] = {"unidades": 0, "defectos": 0, "detencion": 0}
        dias[clave]["unidades"] += unidades
        dias[clave]["defectos"] += defectos
        dias[clave]["detencion"] += detencion

    # Armar una serie por línea, ordenada por fecha, con la tasa diaria
    series = {}
    for (linea, fecha) in sorted(dias):
        d = dias[(linea, fecha)]
        series.setdefault(linea, []).append({
            "fecha": fecha,
            "unidades": int(d["unidades"]),
            "defectos": int(d["defectos"]),
            "detencion": int(d["detencion"]),
            "tasa": d["defectos"] / d["unidades"],
        })
    return series, descartadas


# ---------- PARTE 4.2: gráfico de control -> estado de la línea ----------

META = 0.025        # meta de calidad: tasa de defectos <= 2,5 % (supuesto del proyecto)
BASE_DIAS = 60      # días que definen "lo normal" (fase I del gráfico de control)
VENTANA = 7         # última semana: lo que se compara contra lo normal
RECIENTES = 3       # días recientes donde se buscan valores atípicos


def media(valores):
    return sum(valores) / len(valores)


def desviacion(valores):
    #Desviación estándar: cuánto varía normalmente la tasa de un día a otro.
    m = media(valores)
    return (sum((v - m) ** 2 for v in valores) / (len(valores) - 1)) ** 0.5


def mediana(valores):
    #Valor del medio: no se deja engañar por un día extremo.
    ordenados = sorted(valores)
    n = len(ordenados)
    mitad = n // 2
    return ordenados[mitad] if n % 2 else (ordenados[mitad - 1] + ordenados[mitad]) / 2


def grafico_control(serie):
    #Compara la última semana de una línea contra su comportamiento normal.
    tasas = [dia["tasa"] for dia in serie]
    if len(tasas) < BASE_DIAS + VENTANA:
        raise ValueError(f"Datos insuficientes: {len(tasas)} días (se necesitan {BASE_DIAS + VENTANA})")

    # 1. Lo normal: primeros 60 días
    base = tasas[:BASE_DIAS]
    promedio_base = media(base)
    desv_base = desviacion(base)
    limite_superior = promedio_base + 3 * desv_base

    # 2. Lo de ahora: mediana de la última semana
    mediana_7d = mediana(tasas[-VENTANA:])

    # 3. ¿Cuánto se alejó la última semana de lo normal? (en "errores estándar")
    #    El error estándar de una mediana es ~1,25 veces el de un promedio.
    error_estandar = 1.25 * desv_base / VENTANA ** 0.5
    z = (mediana_7d - promedio_base) / error_estandar

    # 4. Clasificación
    max_recientes = max(tasas[-RECIENTES:])
    if z > 3:
        estado = "cambio_de_nivel"
    elif max_recientes > limite_superior:
        estado = "valor_atipico"
    elif mediana_7d > META:
        estado = "estable_sobre_meta"
    else:
        estado = "estable"

    return {
        "estado": estado,
        "fecha_ultima": serie[-1]["fecha"],
        "tasa_ultimo_dia": round(tasas[-1], 5),
        "tasa_mediana_7d": round(mediana_7d, 5),
        "max_tasa_ultimos_3d": round(max_recientes, 5),
        "promedio_normal": round(promedio_base, 5),
        "limite_superior": round(limite_superior, 5),
        "z_cambio": round(z, 2),
        "veces_la_meta": round(mediana_7d / META, 2),
        "detencion_media_7d_min": round(media([d["detencion"] for d in serie[-VENTANA:]])),
    }

# ---------- PARTE 4.3: modelos de pronóstico (navaja de Occam) ----------
# Cada modelo predice la tasa del día siguiente usando solo los días anteriores.
# Entrenamiento = primeros 60 días (BASE_DIAS); prueba = días restantes.

MEJORA_MINIMA = 0.05   # Holt debe mejorar >= 5 % al mejor modelo simple para preferirlo

def pronosticos_holt(tasas, alfa, beta):
    """Holt (suavizamiento exponencial doble): sigue el nivel y la tendencia.
    Devuelve la predicción para cada día (desde el día 2) y la del día siguiente."""
    nivel, tendencia = tasas[0], tasas[1] - tasas[0]
    predicciones = {}
    for t in range(1, len(tasas)):
        predicciones[t] = nivel + tendencia                      # lo que Holt esperaba para el día t
        nuevo_nivel = alfa * tasas[t] + (1 - alfa) * (nivel + tendencia)
        tendencia = beta * (nuevo_nivel - nivel) + (1 - beta) * tendencia
        nivel = nuevo_nivel
    return predicciones, nivel + tendencia


def error_medio(tasas, predicciones, dias):
    """MAE: error absoluto medio entre lo real y lo predicho."""
    return media([abs(tasas[t] - predicciones[t]) for t in dias])


def comparar_modelos(serie):
    tasas = [dia["tasa"] for dia in serie]
    n = len(tasas)
    entrenamiento = range(VENTANA, BASE_DIAS)   # días para ajustar Holt
    prueba = range(BASE_DIAS, n)                # días para comparar (no vistos al ajustar)

    # 1. Ajustar Holt: probar combinaciones de alfa y beta y quedarse con la de menor error
    mejor = None
    for alfa in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        for beta in [0.01, 0.05, 0.1, 0.2, 0.3]:
            pred, _ = pronosticos_holt(tasas[:BASE_DIAS], alfa, beta)
            mae = error_medio(tasas, pred, entrenamiento)
            if mejor is None or mae < mejor[0]:
                mejor = (mae, alfa, beta)
    _, alfa, beta = mejor

    # 2. Predicciones de los 3 modelos sobre toda la serie
    pred_holt, proximo_holt = pronosticos_holt(tasas, alfa, beta)
    pred_movil = {t: media(tasas[t - VENTANA:t]) for t in range(VENTANA, n)}
    pred_ingenuo = {t: tasas[t - 1] for t in range(1, n)}

    # 3. Error de cada modelo en el periodo de prueba
    errores = {
        "holt": error_medio(tasas, pred_holt, prueba),
        "promedio_movil": error_medio(tasas, pred_movil, prueba),
        "ingenuo": error_medio(tasas, pred_ingenuo, prueba),
    }
    # 4. Navaja de Occam: Holt solo se recomienda si mejora en al menos 5 % al mejor modelo simple
    mejor_simple = min(["promedio_movil", "ingenuo"], key=errores.get)
    mejora_holt = (errores[mejor_simple] - errores["holt"]) / errores[mejor_simple]
    recomendado = "holt" if mejora_holt >= MEJORA_MINIMA else mejor_simple

    return {
        "holt_alfa": alfa,
        "holt_beta": beta,
        "mae_holt": round(errores["holt"], 5),
        "mae_promedio_movil": round(errores["promedio_movil"], 5),
        "mae_ingenuo": round(errores["ingenuo"], 5),
        "mejora_holt_pct": round(mejora_holt * 100, 1),
        "modelo_recomendado": recomendado,
        "dias_prueba": len(prueba),
        "pronostico_holt": round(proximo_holt, 5),
        "pronostico_promedio_movil": round(media(tasas[-VENTANA:]), 5),
    }


# ---------- PARTE 4.4: regla de decisión y resultado final ----------

UMBRAL_DETENER = 1.5   # sobre 1,5 veces la meta, un cambio de nivel justifica detener (supuesto)


def decision_esperada(estado, veces_la_meta):
    """Lo que DEBERÍA recomendarse según las reglas del negocio.
    No se le entrega al LLM: se usa después para verificar su respuesta."""
    if estado == "cambio_de_nivel":
        if veces_la_meta > UMBRAL_DETENER:
            return "detener la línea", "alta"
        return "ajustar la línea", "media"
    if estado == "valor_atipico":
        return "revisión humana antes de actuar", "media"
    if estado == "estable_sobre_meta":
        return "ajustar la línea", "media"
    return "seguir", "baja"


def analizar(items):
    """Función principal: de las filas de la planilla a un resultado por línea."""
    series, descartadas = limpiar_y_agrupar(items)
    salida = []
    for linea, serie in series.items():
        control = grafico_control(serie)
        modelos = comparar_modelos(serie)
        recomendacion, prioridad = decision_esperada(control["estado"], control["veces_la_meta"])
        resultado = {"linea": linea, "dias_analizados": len(serie), "filas_descartadas": descartadas}
        resultado.update(control)
        resultado.update(modelos)
        resultado["regla_recomendacion"] = recomendacion
        resultado["regla_prioridad"] = prioridad
        salida.append({"json": resultado})
    return salida


# ---------- PRUEBA LOCAL (solo en el Mac; esto NO se pega en n8n) ----------
if __name__ == "__main__":
    import csv
    import json
    with open("datos.csv", encoding="utf-8") as f:
        items = [{"json": fila} for fila in csv.DictReader(f)]

    for item in analizar(items):
        r = item["json"]
        print(f"{r['linea']}: {r['estado']} -> {r['regla_recomendacion']} (prioridad {r['regla_prioridad']})")

    # Así se ve lo que n8n recibirá para una línea:
    print("\nResultado completo de la Linea B:")
    print(json.dumps(analizar(items)[1]["json"], indent=2, ensure_ascii=False))
