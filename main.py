import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import io

# 1. CONFIGURACIÓN INTERFAZ (BARRA LATERAL BLANCA)
st.set_page_config(page_title="SISTEMA FORENSE TELEFONÍA", layout="wide")

st.markdown("""
    <style>
    /* Fondo principal de la aplicación: Negro */
    .main { background-color: #000000; color: #0f0; font-family: 'Courier New'; }
    
    /* Fondo de la Barra Lateral Izquierda: Blanco */
    [data-testid="stSidebar"] { 
        background-color: #ffffff !important; 
        border-right: 2px solid #0f0; 
    }
    
    /* Textos y etiquetas legibles en la barra lateral */
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span { 
        color: #111111 !important; 
    }
    
    /* Botones y contenedores */
    .stButton>button { width: 100%; border: 1px solid #0f0; background-color: black; color: #0f0; font-weight: bold; }
    h1, h2, h3 { color: #0f0 !important; text-shadow: 0 0 8px #0f0; text-transform: uppercase; }
    .stDataFrame { border: 1px solid #0f0; }
    </style>
    """, unsafe_allow_html=True)

# Función para limpiar registros visuales (quitar .0 a los teléfonos/IMEIs)
def limpiar_texto(valor):
    if pd.isna(valor):
        return 'DESCONOCIDO'
    v_str = str(valor).strip()
    if v_str.endswith('.0') and len(v_str) > 5:
        return v_str.split('.')[0]
    return v_str

# Función auxiliar para procesar y estructurar de manera forense cualquier archivo cargado
def procesar_sabana(archivo_bytes, nombre_archivo):
    if nombre_archivo.endswith('.csv'):
        df_temp = pd.read_csv(archivo_bytes)
    else:
        df_temp = pd.read_excel(archivo_bytes)
        
    df_temp.columns = [str(c).strip() for c in df_temp.columns]
    
    if 'Fecha' not in df_temp.columns or 'Hora' not in df_temp.columns:
        st.error(f"❌ El archivo '{nombre_archivo}' no contiene las columnas exactas llamadas 'Fecha' u 'Hora'.")
        st.stop()
        
    df_temp['__Fecha_Hora_Str'] = df_temp['Fecha'].astype(str).str.strip() + ' ' + df_temp['Hora'].astype(str).str.strip()
    df_temp['__Timestamp_Forense'] = pd.to_datetime(df_temp['__Fecha_Hora_Str'], dayfirst=True, errors='coerce')
    
    idx_na = df_temp['__Timestamp_Forense'].isna()
    if idx_na.any():
        df_temp.loc[idx_na, '__Timestamp_Forense'] = pd.to_datetime(df_temp.loc[idx_na, 'Fecha'], dayfirst=True, errors='coerce')
        
    df_temp = df_temp.sort_values(by='__Timestamp_Forense', ascending=True).reset_index(drop=True)
    
    # Determinar número analizado de manera dinámica
    if 'Linea_A' in df_temp.columns:
        try:
            num_analizado = str(df_temp['Linea_A'].mode()[0]).strip().split('.')[0]
        except:
            num_analizado = "OBJETIVO"
    else:
        num_analizado = "OBJETIVO"
        
    # Calcular Contacto Interacción
    if 'Linea_B' in df_temp.columns and 'Linea_A' in df_temp.columns:
        def obtener_contacto(fila):
            tipo_ev = str(fila.get('Tipo', '')).strip().upper()
            num_a = limpiar_texto(fila['Linea_A'])
            num_b = limpiar_texto(fila['Linea_B'])
            if 'ENTRANTE' in tipo_ev or num_b == num_analizado:
                return num_a
            elif 'SALIENTE' in tipo_ev or num_a == num_analizado:
                return num_b
            return num_b
        df_temp['Contacto_Calculado'] = df_temp.apply(obtener_contacto, axis=1)
    else:
        df_temp['Contacto_Calculado'] = df_temp['Linea_B'].apply(limpiar_texto) if 'Linea_B' in df_temp.columns else 'N/A'
        
    return df_temp

st.title("⚡ ANALIZADOR DE SÁBANAS")
st.write("---")

# --- MENÚ DE NAVEGACIÓN EN LA BARRA BLANCA ---
st.sidebar.header("🎯 FILTROS DE ANÁLISIS")
opcion = st.sidebar.radio("Selecciona una opción:", ["Vista General", "Pernocta (23:00 - 06:00)", "Top 10 Más Frecuentes", "🔗 Cruce de Sábanas (Multi-Objetivo)"])

st.sidebar.markdown("---")
st.sidebar.subheader("📂 CARGA DE ARCHIVOS")

# Primer cargador global de archivos (Sábana Principal)
archivo_principal = st.sidebar.file_uploader("📂 SÁBANA OBJETIVO PRINCIPAL (1)", type=["xlsx", "xls", "csv"], key="sabana_p1")

if archivo_principal:
    try:
        # Procesar Sábana Principal usando la lógica forense estandarizada
        df = procesar_sabana(archivo_principal, archivo_principal.name)
        df_final = df.copy()

        # --- LÓGICA DE CONTROL EXCLUSIVA: CRUCE DE SÁBANAS (OPCIÓN 2 ACTUALIZADA) ---
        if opcion == "🔗 Cruce de Sábanas (Multi-Objetivo)":
            st.subheader("🔗 ANÁLISIS FORENSE DE CRUCE Y COINCIDENCIAS MULTI-OBJETIVO")
            st.write("Esta sección analiza las interacciones y celdas comunes entre dos objetivos telefónicos independientes.")
            
            st.info("💡 Por favor, carga la segunda sábana telefónica en el panel inferior para ejecutar el cruce.")
            archivo_secundario = st.file_uploader("📂 CARGAR SÁBANA OBJETIVO SECUNDARIO (2)", type=["xlsx", "xls", "csv"], key="sabana_s2")
            
            if archivo_secundario:
                with st.spinner("⚡ Ejecutando algoritmos forenses de cruce multidimensional..."):
                    df_secundario = procesar_sabana(archivo_secundario, archivo_secundario.name)
                    
                    # Crear Pestañas limpias para organizar los hallazgos criminalísticos
                    tab_contactos, tab_mapa, tab_cronologia = st.tabs([
                        "🤝 CONTACTOS COMPARTIDOS", 
                        "🗺️ MAPA DE COINCIDENCIA GEOGRÁFICA",
                        "⏳ COINCIDENCIAS CRONOLÓGICAS (MISMO DÍA)"
                    ])
                    
                    # ---- PESTAÑA 1: CRUCE DE CONTACTOS ----
                    with tab_contactos:
                        st.write("### 👥 Números Telefónicos o Portales en Común")
                        excluir = ['DESCONOCIDO', 'N/A', '']
                        c1 = df_final[~df_final['Contacto_Calculado'].isin(excluir)]['Contacto_Calculado'].value_counts().reset_index(name='Conexiones_Obj1')
                        c2 = df_secundario[~df_secundario['Contacto_Calculado'].isin(excluir)]['Contacto_Calculado'].value_counts().reset_index(name='Conexiones_Obj2')
                        
                        c1.columns = ['Contacto', 'Conexiones Objetivo 1']
                        c2.columns = ['Contacto', 'Conexiones Objetivo 2']
                        
                        df_cruce_contactos = pd.merge(c1, c2, on='Contacto', how='inner')
                        df_cruce_contactos['Total Interacciones Combinadas'] = df_cruce_contactos['Conexiones Objetivo 1'] + df_cruce_contactos['Conexiones Objetivo 2']
                        df_cruce_contactos = df_cruce_contactos.sort_values(by='Total Interacciones Combinadas', ascending=False).reset_index(drop=True)
                        
                        if not df_cruce_contactos.empty:
                            st.success(f"🔍 Se identificaron {len(df_cruce_contactos)} entidades/contactos vinculados con ambos objetivos.")
                            st.dataframe(df_cruce_contactos, use_container_width=True)
                        else:
                            st.warning("⚠️ No se encontraron números de contacto ni portales web compartidos.")
                            
                    # ---- PRE-PROCESAMIENTO PARA CRUCE GEOGRÁFICO Y TEMPORAL ----
                    columnas_geo = ['Latitud', 'Longitud']
                    if all(col in df_final.columns for col in columnas_geo) and all(col in df_secundario.columns for col in columnas_geo):
                        
                        # Limpieza Sábana 1
                        g1 = df_final.dropna(subset=columnas_geo).copy()
                        g1['Latitud'] = pd.to_numeric(g1['Latitud'], errors='coerce')
                        g1['Longitud'] = pd.to_numeric(g1['Longitud'], errors='coerce')
                        g1 = g1[(g1['Latitud'] != 0) & (g1['Longitud'] != 0)].dropna(subset=columnas_geo)
                        g1['Fecha_Clean'] = g1['Fecha'].astype(str).str.strip()
                        g1['Lat_R'] = g1['Latitud'].round(4)
                        g1['Lon_R'] = g1['Longitud'].round(4)
                        
                        # Limpieza Sábana 2
                        g2 = df_secundario.dropna(subset=columnas_geo).copy()
                        g2['Latitud'] = pd.to_numeric(g2['Latitud'], errors='coerce')
                        g2['Longitud'] = pd.to_numeric(g2['Longitud'], errors='coerce')
                        g2 = g2[(g2['Latitud'] != 0) & (g2['Longitud'] != 0)].dropna(subset=columnas_geo)
                        g2['Fecha_Clean'] = g2['Fecha'].astype(str).str.strip()
                        g2['Lat_R'] = g2['Latitud'].round(4)
                        g2['Lon_R'] = g2['Longitud'].round(4)

                        # Encontrar cruces exactos de lugar Y fecha
                        df_cruce_tiempo_real = pd.merge(
                            g1[['Lat_R', 'Lon_R', 'Latitud', 'Longitud', 'Fecha_Clean', 'Hora', 'Tipo', 'Contacto_Calculado']],
                            g2[['Lat_R', 'Lon_R', 'Fecha_Clean', 'Hora', 'Tipo', 'Contacto_Calculado']],
                            on=['Lat_R', 'Lon_R', 'Fecha_Clean'],
                            how='inner'
                        )
                        
                        # Agrupación base de lugares comunes
                        puntos_g1 = g1.groupby(['Lat_R', 'Lon_R']).size().reset_index(name='Hits_Obj1')
                        puntos_g2 = g2.groupby(['Lat_R', 'Lon_R']).size().reset_index(name='Hits_Obj2')
                        df_cruce_geo = pd.merge(puntos_g1, puntos_g2, on=['Lat_R', 'Lon_R'], how='inner')
                        
                        # Recuperar coordenadas originales para mapear
                        coords_orig = g1.drop_duplicates(subset=['Lat_R', 'Lon_R'])[['Lat_R', 'Lon_R', 'Latitud', 'Longitud']]
                        df_cruce_geo = df_cruce_geo.merge(coords_orig, on=['Lat_R', 'Lon_R'], how='left')

                        # Conjunto de coordenadas que tienen coincidencia de fecha para identificar el color velozmente
                        puntos_mismo_dia = set(zip(df_cruce_tiempo_real['Lat_R'], df_cruce_tiempo_real['Lon_R']))

                        # ---- PESTAÑA 2: CRUCE GEOGRÁFICO EN MAPA ----
                        with tab_mapa:
                            st.write("### 🗺️ Coincidencias Espaciales (Código de Colores Forense)")
                            
                            st.markdown("""
                            <div style="background-color: #111; padding: 10px; border: 1px solid #333; margin-bottom: 15px;">
                                <span style="color: #FF0000; font-weight: bold;">🔴🟡 AMARILLO BORDE ROJO:</span> Coincidencia Crítica (Estuvieron en el <b>mismo lugar el MISMO DÍA</b>).<br>
                                <span style="color: #800080; font-weight: bold;">🟣 PÚRPURA:</span> Coincidencia Simple (Comparten lugar, pero asistieron en <b>fechas diferentes</b>).
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if not df_cruce_geo.empty:
                                centro_lat = df_cruce_geo['Latitud'].mean()
                                centro_lon = df_cruce_geo['Longitud'].mean()
                                mapa_cruce = folium.Map(location=[centro_lat, centro_lon], zoom_start=12, tiles='CartoDB positron')
                                
                                count_criticos = 0
                                for _, renglon in df_cruce_geo.iterrows():
                                    lat_r = renglon['Lat_R']
                                    lon_r = renglon['Lon_R']
                                    lat_orig = float(renglon['Latitud'])
                                    lon_orig = float(renglon['Longitud'])
                                    hits_1 = int(renglon['Hits_Obj1'])
                                    hits_2 = int(renglon['Hits_Obj2'])
                                    
                                    # Validar si este punto específico comparte misma fecha
                                    es_critico = (lat_r, lon_r) in puntos_mismo_dia
                                    
                                    if es_critico:
                                        color_borde, color_relleno, radio, animacion = '#FF0000', '#FFFF00', 16, "⚠️ COINCIDENCIA DE FECHA ACTIVA"
                                        count_criticos += 1
                                    else:
                                        color_borde, color_relleno, radio, animacion = '#800080', '#DA70D6', 11, "Misma celda (Diferente fecha)"
                                        
                                    html_popup = f"""
                                    <div style="font-family: 'Courier New', monospace; font-size: 11px; width: 290px;">
                                        <h5 style="margin: 0 0 5px 0; color: {color_borde}; font-weight: bold;">{animacion}</h5>
                                        <b>LAT:</b> {lat_orig} | <b>LON:</b> {lon_orig}<br><br>
                                        <b>📌 ACTIVIDAD OBJETIVO 1:</b> {hits_1} registros.<br>
                                        <b>📌 ACTIVIDAD OBJETIVO 2:</b> {hits_2} registros.
                                    </div>
                                    """
                                    iframe = folium.IFrame(html_popup, width=310, height=130)
                                    folium.CircleMarker(
                                        location=[lat_orig, lon_orig],
                                        radius=radio,
                                        color=color_borde,
                                        weight=3 if es_critico else 1,
                                        fill=True,
                                        fill_color=color_relleno,
                                        fill_opacity=0.8 if es_critico else 0.6,
                                        popup=folium.Popup(iframe, max_width=330)
                                    ).add_to(mapa_cruce)
                                
                                st_folium(mapa_cruce, width="100%", height=550, key="mapa_cruce_espejo_colores")
                                
                                # --- BOTÓN DESCARGA MAPA HTML ---
                                buffer_mapa = io.BytesIO()
                                mapa_cruce.save(buffer_mapa, close_file=False)
                                st.download_button(
                                    label="📥 DESCARGAR MAPA DE CRUCES (.html)",
                                    data=buffer_mapa.getvalue(),
                                    file_name="Mapa_Cruce_Forense.html",
                                    mime="text/html"
                                )
                                
                                if count_criticos > 0:
                                    st.error(f"🚨 ALERTAS CRÍTICAS: Se localizaron {count_criticos} puntos geográficos donde coincidieron en el mismo día.")
                            else:
                                st.warning("⚠️ Ambos objetivos no comparten celdas.")

                        # ---- PESTAÑA 3: CRUCE CRONOLÓGICO DETALLADO ----
                        with tab_cronologia:
                            st.write("### ⏳ Bitácora de Eventos Simultáneos (Mismo Lugar e Identidad de Fecha)")
                            if not df_cruce_tiempo_real.empty:
                                df_reporte_tiempo = df_cruce_tiempo_real[[
                                    'Fecha_Clean', 'Latitud', 'Longitud', 
                                    'Hora_x', 'Tipo_x', 'Contacto_Calculado_x',
                                    'Hora_y', 'Tipo_y', 'Contacto_Calculado_y'
                                ]].copy()
                                
                                df_reporte_tiempo.columns = [
                                    'Fecha Coincidencia', 'Latitud', 'Longitud',
                                    'Hora Obj 1', 'Evento Obj 1', 'Contacto Obj 1',
                                    'Hora Obj 2', 'Evento Obj 2', 'Contacto Obj 2'
                                ]
                                
                                st.success(f"🔥 Se encontraron {len(df_reporte_tiempo)} registros sincronizados exactamente en fecha y espacio.")
                                st.dataframe(df_reporte_tiempo, use_container_width=True)
                            else:
                                st.warning("📋 No se registraron interacciones en el mismo día dentro de la misma celda.")
                    else:
                        st.error("❌ Archivos sin columnas de geolocalización necesarias ('Latitud', 'Longitud').")
                    st.stop()

        # --- PROCESAMIENTO DE FILTROS BÁSICOS (VISTA GENERAL / PERNOCTA) ---
        if opcion == "Pernocta (23:00 - 06:00)":
            st.sidebar.subheader("🌙 MODO PERNOCTA ACTIVO")
            horas_numericas = df_final['__Timestamp_Forense'].dt.hour
            df_final = df_final[(horas_numericas >= 23) | (horas_numericas <= 6)]
            st.sidebar.success(f"🔍 Registros nocturnos: {len(df_final)}")
        elif opcion == "Top 10 Más Frecuentes":
            st.sidebar.subheader("📊 CONFIGURACIÓN DEL TOP 10")
            sub_tipo = st.sidebar.selectbox("Elegir tipo de tráfico:", ["Llamadas (Voz/SMS)", "Internet (Datos)"])
        else:
            st.sidebar.info(f"📊 Total de la sábana: {len(df_final)} registros.")

        # --- CONTROL EXCLUSIVO DE PANTALLA: TOP 10 CONSOLIDADO CON DETALLES ---
        if opcion == "Top 10 Más Frecuentes":
            st.subheader(f"📊 ANÁLISIS DE FRECUENCIA: TOP 10 {sub_tipo.upper()}")
            
            es_dominio = df_final['Contacto_Calculado'].str.contains(r'[a-zA-Z\.]', regex=True, na=False)
            es_tipo_datos = df_final['Tipo'].astype(str).str.upper().str.contains(r'(GPRS|DATOS|INTERNET)', regex=True, na=False)
            es_trafico_internet = es_dominio | es_tipo_datos
            
            if sub_tipo == "Llamadas (Voz/SMS)":
                df_top = df_final[~es_trafico_internet & (df_final['Contacto_Calculado'] != 'DESCONOCIDO')].copy()
                label_columna = "Número Telefónico"
            else:
                df_top = df_final[es_trafico_internet].copy()
                label_columna = "Portal / Punto de Acceso"

            if not df_top.empty:
                frecuencias = df_top['Contacto_Calculado'].value_counts().head(10)
                df_resumen_top10 = frecuencias.reset_index()
                df_resumen_top10.columns = [label_columna, 'Cantidad de Conexiones']
                
                lista_linea_a, lista_linea_b, lista_tipo = [], [], []
                
                for contacto in df_resumen_top10[label_columna]:
                    ultimo_registro = df_top[df_top['Contacto_Calculado'] == contacto].iloc[-1]
                    lista_linea_a.append(limpiar_texto(ultimo_registro.get('Linea_A', 'N/A')))
                    lista_linea_b.append(limpiar_texto(ultimo_registro.get('Linea_B', 'N/A')))
                    lista_tipo.append(str(ultimo_registro.get('Tipo', 'N/A')).strip())
                
                df_resumen_top10['Linea_A'] = lista_linea_a
                df_resumen_top10['Linea_B'] = lista_linea_b
                df_resumen_top10['Tipo'] = lista_tipo
                
                st.bar_chart(data=df_resumen_top10, x=label_columna, y='Cantidad de Conexiones', use_container_width=True)
                
                st.write("### 📋 TABLA DETALLADA DE FRECUENCIA")
                st.dataframe(df_resumen_top10, use_container_width=True, key="tabla_frecuencia_detallada_fija")
            else:
                st.warning(f"⚠️ No se encontraron registros correspondientes a {sub_tipo} en este archivo.")
            st.stop()

        # --- RENDERIZAR RESULTADOS GENERALES EN INTERFAZ (VISTA GENERAL / PERNOCTA) ---
        df_mostrar = df_final.drop(columns=['__Fecha_Hora_Str', '__Timestamp_Forense', 'Contacto_Calculado'], errors='ignore')
        for col_limpiar in ['Linea_A', 'Linea_B', 'IMEI', 'IMSI']:
            if col_limpiar in df_mostrar.columns:
                df_mostrar[col_limpiar] = df_mostrar[col_limpiar].apply(limpiar_texto)

        st.subheader(f"📑 REGISTROS EN PANTALLA - {opcion.upper()} ({len(df_mostrar)})")
        st.dataframe(df_mostrar, use_container_width=True, key=f"grid_{opcion.lower().replace(' ', '_')}")

        # DESCARGA: Reporte Excel
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='xlsxwriter') as writer:
            df_mostrar.to_excel(writer, index=False, sheet_name='Analisis_Forense')
            
        st.sidebar.download_button(
            label="📥 DESCARGAR EXCEL FILTRADO",
            data=buffer_excel.getvalue(),
            file_name=f"reporte_{opcion.lower().replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # --- CONFIGURACIÓN DEL MAPA Y TABLA CRONOLÓGICA COORDINADA ---
        if 'Latitud' in df_final.columns and 'Longitud' in df_final.columns:
            df_mapa = df_final.dropna(subset=['Latitud', 'Longitud']).copy()
            df_mapa['Latitud'] = pd.to_numeric(df_mapa['Latitud'], errors='coerce')
            df_mapa['Longitud'] = pd.to_numeric(df_mapa['Longitud'], errors='coerce')
            df_mapa = df_mapa[(df_mapa['Latitud'] != 0) & (df_mapa['Longitud'] != 0)].dropna(subset=['Latitud', 'Longitud']).reset_index(drop=True)

            if not df_mapa.empty:
                conteo_puntos = df_mapa.groupby(['Latitud', 'Longitud']).size().reset_index(name='Conexiones_Totales')
                df_mapa = df_mapa.merge(conteo_puntos, on=['Latitud', 'Longitud'], how='left')
                df_mapa_unico = df_mapa.drop_duplicates(subset=['Latitud', 'Longitud'])

                df_cronologico = pd.DataFrame()
                df_cronologico['Secuencia (#)'] = range(1, len(df_mapa) + 1)
                df_cronologico['Fecha'] = df_mapa['Fecha']
                df_cronologico['Hora'] = df_mapa['Hora']
                df_cronologico['Latitud'] = df_mapa['Latitud']
                df_cronologico['Longitud'] = df_mapa['Longitud']
                df_cronologico['Conexiones en este Punto'] = df_mapa['Conexiones_Totales']
                if 'Tipo' in df_mapa.columns:
                    df_cronologico['Tipo Evento'] = df_mapa['Tipo']
                df_cronologico['Contacto Interacción'] = df_mapa['Contacto_Calculado']

                lat_centro = df_mapa_unico['Latitud'].mean()
                lon_centro = df_mapa_unico['Longitud'].mean()
                zoom_actual = 11
                coordenada_resaltada = None

                llave_tabla = f"tabla_interactiva_{opcion.lower().replace(' ', '_')}"
                if llave_tabla in st.session_state and st.session_state[llave_tabla]["selection"]["rows"]:
                    fila_seleccionada_idx = st.session_state[llave_tabla]["selection"]["rows"][0]
                    lat_centro = float(df_cronologico.iloc[fila_seleccionada_idx]['Latitud'])
                    lon_centro = float(df_cronologico.iloc[fila_seleccionada_idx]['Longitud'])
                    zoom_actual = 15
                    coordenada_resaltada = (lat_centro, lon_centro)

                st.write("---")
                st.subheader(f"🗺️ MAPA DE ACTIVIDAD E INTERACCIÓN DINÁMICA ({opcion.upper()})")
                
                mapa_folium = folium.Map(location=[lat_centro, lon_centro], zoom_start=zoom_actual, tiles='CartoDB positron')
                
                for _, renglon in df_mapa_unico.iterrows():
                    lat = float(renglon['Latitud'])
                    lon = float(renglon['Longitud'])
                    conexiones = int(renglon['Conexiones_Totales'])
                    
                    color_borde, color_relleno, opacidad = '#000000', '#FF0000', 0.8
                    radio_dinamico = min(6 + (conexiones * 0.5), 30)
                    
                    if coordenada_resaltada and abs(lat - coordenada_resaltada[0]) < 0.00001 and abs(lon - coordenada_resaltada[1]) < 0.00001:
                        color_borde, color_relleno, radio_dinamico, opacidad = '#00FFFF', '#0000FF', 22, 1.0

                    df_eventos_punto = df_mapa[(df_mapa['Latitud'] == lat) & (df_mapa['Longitud'] == lon)]
                    
                    html_popup = f"""
                    <div style="font-family: 'Courier New', monospace; font-size: 11px; width: 320px; max-height: 250px; overflow-y: auto;">
                        <h5 style="margin: 0 0 5px 0; color: #ff0000; font-weight: bold; text-transform: uppercase;">📊 RESUMEN DE COORDENADA</h5>
                        <b>CONEXIONES TOTALES:</b> {conexiones}<br>
                        <b>LAT:</b> {lat} | <b>LON:</b> {lon}
                        <hr style="border: 1px dashed #333; margin: 8px 0;">
                        <h5 style="margin: 0 0 5px 0; color: #000; font-weight: bold;">📑 FICHA DE REGISTROS:</h5>
                    """
                    for idx, ev in df_eventos_punto.iterrows():
                        html_popup += f"""
                        <div style="background-color: #f7f7f7; padding: 4px; margin-bottom: 4px; border-left: 3px solid #ff0000;">
                            <b>📅:</b> {ev.get('Fecha', 'N/A')} | <b>⏰:</b> {ev.get('Hora', 'N/A')}<br>
                            <b>📌 Evento:</b> {ev.get('Tipo', 'None')}<br>
                            <b>📞 Contacto:</b> {ev.get('Contacto_Calculado', 'N/A')}
                        </div>
                        """
                    html_popup += "</div>"
                    
                    iframe = folium.IFrame(html_popup, width=340, height=260)
                    folium.CircleMarker(
                        location=[lat, lon], radius=radio_dinamico, color=color_borde,
                        weight=3 if coordenada_resaltada else 2, fill=True, fill_color=color_relleno,
                        fill_opacity=opacidad, popup=folium.Popup(iframe, max_width=360)
                    ).add_to(mapa_folium)

                mapa_html_bytes = io.BytesIO()
                mapa_folium.save(mapa_html_bytes, close_file=False)
                st.sidebar.download_button(
                    label="📥 DESCARGAR MAPA INTERACTIVO (HTML)", data=mapa_html_bytes.getvalue(),
                    file_name=f"mapa_actividad_{opcion.lower().replace(' ', '_')}.html", mime="text/html"
                )

                st_folium(mapa_folium, width="100%", height=600, key=f"map_density_{opcion.lower().replace(' ', '_')}")

                st.write("---")
                st.subheader(f"⏱️ LÍNEA DE TIEMPO CRONOLÓGICA DE CONEXIONES ({opcion.upper()})")
                st.dataframe(
                    df_cronologico.set_index('Secuencia (#)'), use_container_width=True, key=llave_tabla,
                    on_select="rerun", selection_mode="single-row"
                )
            else:
                st.write("---")
                st.warning("⚠️ No hay coordenadas geográficas válidas para generar el mapa.")
    except Exception as error_general:
        st.error(f"🚨 Ocurrió un error inesperado al procesar los datos: {error_general}")
else:
    st.info("👋 BIENVENIDO. Por favor, carga la sábana del Objetivo Principal (1) desde la barra lateral izquierda para comenzar.")
