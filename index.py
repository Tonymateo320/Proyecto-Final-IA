

"""
Analizador de Accesibilidad Web - Versión con UI mejorada y soporte para análisis de página completa

Esta aplicación utiliza Streamlit para proporcionar una interfaz de usuario
que permite analizar la accesibilidad de sitios web, usando modelos de deep learning
para detectar problemas como texto en imágenes sin alternativas adecuadas y
simular cómo verían las páginas personas con daltonismo.
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw
import io
import os
import time
from datetime import datetime
import base64

try:
    import matplotlib.pyplot as plt
    matplotlib_available = True
except ImportError:
    matplotlib_available = False

# Importar de módulos """Tony Mateo 23-EISN-2-044"""
from utils.web_capture import WebCapture
from utils.dom_extractor import DOMExtractor
from models.text_detector_dl import TextDetectorDL
from models.colorblind_simulator import ColorBlindSimulator

# Configuración de la página """Tony Mateo 23-EISN-2-044"""
st.set_page_config(
    page_title="Analizador de Accesibilidad Web", 
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejorar la apariencia """Tony Mateo 23-EISN-2-044"""
st.markdown("""
<style>
    /* Colores principales y estilos */
    :root {
        --primary: #4361ee;
        --secondary: #3f37c9;
        --accent: #4895ef;
        --background: #f8f9fa;
        --success: #4cc9f0;
        --warning: #f72585;
        --error: #7209b7;
    }
    
    /* Estilo general */
    .main {
        background-color: var(--background);
        padding: 1rem;
    }
    
    h1, h2, h3 {
        color: var(--primary);
    }
    
    /* Personalización de encabezados y texto */
    .title-container {
        background-color: var(--primary);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .subtitle {
        opacity: 0.8;
        margin-top: 0.5rem;
    }
    
    /* Tarjetas para resultados */
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* Iconos e indicadores */
    .metric-container {
        background-color: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        text-align: center;
        height: 100%;
    }
    
    .metric {
        font-size: 2.5rem;
        font-weight: bold;
        color: var(--primary);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
    }
    
    /* Botones personalizados */
    .custom-button {
        background-color: var(--primary);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        font-weight: bold;
    }
    
    .custom-button:hover {
        background-color: var(--secondary);
    }
    
    /* Indicadores de calidad */
    .quality-high {
        color: #00cc66;
        font-weight: bold;
    }
    
    .quality-medium {
        color: #ffc107;
        font-weight: bold;
    }
    
    .quality-low {
        color: #ff3860;
        font-weight: bold;
    }
    
    /* Tabs personalizados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f0f0;
        border-radius: 5px 5px 0 0;
        border: none;
        padding: 10px 20px;
        color: #333;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary) !important;
        color: white !important;
    }
    
    /* Espaciado y márgenes */
    .spacer {
        height: 2rem;
    }
    
    .small-spacer {
        height: 1rem;
    }
    
    /* Animaciones y efectos */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    /* Estilos para mensajes de progreso */
    .progress-message {
        padding: 10px 15px;
        background-color: #f8f9fa;
        border-left: 5px solid var(--primary);
        margin-bottom: 10px;
        border-radius: 0 5px 5px 0;
    }
    
    /* Responsive ajustes */
    @media (max-width: 768px) {
        .metric {
            font-size: 1.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Función para analizar el contraste """Tony Mateo 23-EISN-2-044"""
def analyze_contrast(image):
    """
    Analiza la imagen para detectar posibles problemas de contraste.
    Esta es una versión muy simplificada del análisis de contraste.
    
    Args:
        image (PIL.Image): Imagen a analizar
        
    Returns:
        list: Lista de problemas de contraste detectados
    """
    # Convertir a array numpy para procesamiento con OpenCV """Tony Mateo 23-EISN-2-044"""
    np_image = np.array(image)
    
    # Convertir a escala de grises """Tony Mateo 23-EISN-2-044"""
    gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
    
    # Detectar bordes (posible texto) """Tony Mateo 23-EISN-2-044"""
    edges = cv2.Canny(gray, 50, 150)
    
    # Dilatación para conectar componentes cercanos """Tony Mateo 23-EISN-2-044"""
    kernel = np.ones((3,3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)
    
    # Encontrar contornos posibles regiones de texto """Tony Mateo 23-EISN-2-044"""
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtrar contornos por tamaño """Tony Mateo 23-EISN-2-044"""
    min_area = 100
    contrast_issues = []
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h > min_area and w > h:  
            # Extraer región """Tony Mateo 23-EISN-2-044"""
            region = np_image[y:y+h, x:x+w]

            # Evitar regiones vacías """Tony Mateo 23-EISN-2-044"""
            
            if region.size == 0:  
                continue
                
            # Análisis de contraste muy simplificado: """Tony Mateo 23-EISN-2-044"""
            # Calcular el valor medio de gris en la región
            region_gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
            mean_value = np.mean(region_gray)
            
            # Si el valor medio está en un rango cercano al fondo,
            # podría ser un problema de contraste
            # (Este es un método muy simplificado y no es preciso)
            if 70 < mean_value < 200:  # Valores arbitrarios para demostración """Tony Mateo 23-EISN-2-044"""
                contrast_issues.append({
                    'region': (x, y, w, h),
                    'contrast_value': mean_value,
                    'severity': 'Medio' if mean_value > 120 else 'Alto'
                })
    
    return contrast_issues

# Función para crear un encabezado  """Tony Mateo 23-EISN-2-044"""
def display_header():
    st.markdown("""
    <div class="title-container fade-in">
        <h1>Analizador de Accesibilidad Web con Deep Learning</h1>
        <p class="subtitle">Analiza sitios web para problemas de accesibilidad y simula cómo los verían personas con daltonismo</p>
    </div>
    """, unsafe_allow_html=True)

# Función para mostrar una tarjeta de métrica """Tony Mateo 23-EISN-2-044"""
def metric_card(title, value, description="", icon="📊", color="primary"):
    st.markdown(f"""
    <div class="metric-container">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        <div class="metric" style="color: var(--{color});">{value}</div>
        <div class="metric-label">{title}</div>
        <div style="font-size: 0.8rem; margin-top: 0.5rem; color: #6c757d;">{description}</div>
    </div>
    """, unsafe_allow_html=True)

# Función para mostrar un mensaje de progreso """Tony Mateo 23-EISN-2-044"""
def progress_message(message, icon="⏳"):
    st.markdown(f"""
    <div class="progress-message">
        <p><strong>{icon} {message}</strong></p>
    </div>
    """, unsafe_allow_html=True)

# Función para crear gráfico de resumen de accesibilidad con matplotlib """Tony Mateo 23-EISN-2-044"""
def create_accessibility_chart(contrast_issues, text_issues, colorblind_issues):
    # Verificar si matplotlib está disponible """Tony Mateo 23-EISN-2-044"""
    if not matplotlib_available:
        st.warning("La biblioteca matplotlib no está instalada. No se puede mostrar el gráfico.")
        return None
    
    # Crear datos para el gráfico """Tony Mateo 23-EISN-2-044"""
    categories = ['Contraste', 'Texto en imágenes', 'Protanopia', 'Deuteranopia', 'Tritanopia']
    values = [
        len(contrast_issues),
        len(text_issues),
        len(colorblind_issues['protanopia']),
        len(colorblind_issues['deuteranopia']),
        len(colorblind_issues['tritanopia'])
    ]
    
    # Crear colores para las barras """Tony Mateo 23-EISN-2-044"""
    colors = ['#FF9E80', '#4FC3F7', '#FF7043', '#4DB6AC', '#7986CB']
    
    # Crear gráfico de barras con matplotlib básico """Tony Mateo 23-EISN-2-044"""
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(categories, values, color=colors)
    
    # Añadir etiquetas """Tony Mateo 23-EISN-2-044"""
    ax.set_title('Resumen de problemas de accesibilidad', fontsize=16)
    ax.set_xlabel('Categoría de problema', fontsize=12)
    ax.set_ylabel('Número de problemas', fontsize=12)
    
    # Añadir valores en las barras """Tony Mateo 23-EISN-2-044"""
    for i, v in enumerate(values):
        ax.text(i, v + 0.1, str(v), ha='center', fontsize=12, fontweight='bold')
    
    # Ajustar diseño
    plt.tight_layout()
    
    return fig

# Función para generar informe HTML mejorado """Tony Mateo 23-EISN-2-044"""
def generate_html_report(url, screenshot, contrast_issues, text_issues, score, colorblind_issues=None, is_full_page=False):
    """
    Genera un informe HTML mejorado con los resultados del análisis.
    
    Args:
        url (str): URL analizada
        screenshot (PIL.Image): Captura de pantalla
        contrast_issues (list): Problemas de contraste detectados
        text_issues (list): Problemas de texto en imágenes detectados
        score (int): Puntuación global
        colorblind_issues (list, optional): Problemas detectados para daltonismo
        is_full_page (bool): Indica si se realizó un análisis de página completa
        
    Returns:
        str: Documento HTML
    """
    # Convertir imagen a base64 para incluirla en HTML """Tony Mateo 23-EISN-2-044"""
    buffered = io.BytesIO()
    screenshot.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Generar HTML con diseño mejorado """Tony Mateo 23-EISN-2-044"""
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Informe de Accesibilidad - {url}</title>
        <style>
            :root {{
                --primary: #4361ee;
                --secondary: #3f37c9;
                --accent: #4895ef;
                --success: #4cc9f0;
                --warning: #f72585;
                --error: #7209b7;
                --light-bg: #f8f9fa;
                --dark-text: #2c3e50;
                --light-text: #6c757d;
                --border-radius: 8px;
                --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                line-height: 1.6;
                color: var(--dark-text); 
                background-color: #f5f7fa;
                margin: 0;
                padding: 0;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            
            h1, h2, h3, h4 {{ 
                color: var(--primary);
                margin-bottom: 1rem;
            }}
            
            p {{
                margin-bottom: 1rem;
            }}
            
            .header {{ 
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                color: white;
                padding: 40px;
                border-radius: var(--border-radius);
                margin-bottom: 30px;
                box-shadow: var(--box-shadow);
            }}
            
            .header h1 {{
                color: white;
                margin-bottom: 10px;
            }}
            
            .header p {{
                color: rgba(255, 255, 255, 0.9);
                margin-bottom: 5px;
            }}
            
            .score-container {{
                display: flex;
                align-items: center;
                margin-top: 20px;
            }}
            
            .score {{ 
                font-size: 36px; 
                font-weight: bold; 
                color: #fff; 
                background-color: #{
                    "28a745" if score >= 90 else "ffc107" if score >= 70 else "dc3545"
                }; 
                padding: 15px 20px; 
                border-radius: 50%; 
                display: inline-block;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                margin-right: 20px;
            }}
            
            .score-label {{
                font-size: 18px;
                color: white;
            }}
            
            .section {{ 
                background-color: white;
                padding: 30px;
                border-radius: var(--border-radius);
                margin-bottom: 30px;
                box-shadow: var(--box-shadow);
            }}
            
            .issue {{ 
                background-color: var(--light-bg); 
                padding: 20px; 
                border-radius: var(--border-radius);
                margin-bottom: 15px;
                border-left: 5px solid #ddd;
                transition: transform 0.2s ease;
            }}
            
            .issue:hover {{
                transform: translateY(-3px);
            }}
            
            .issue-header {{ 
                display: flex; 
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }}
            
            .severity {{ 
                font-weight: bold; 
                color: #fff; 
                padding: 5px 10px; 
                border-radius: 20px;
                font-size: 14px;
            }}
            
            .high {{ 
                background-color: var(--error);
                border-left-color: var(--error);
            }}
            
            .medium {{ 
                background-color: var(--warning);
                border-left-color: var(--warning);
            }}
            
            .low {{ 
                background-color: var(--success);
                border-left-color: var(--success);
            }}
            
            .screenshot {{ 
                max-width: 100%; 
                height: auto; 
                border: 1px solid #ddd; 
                border-radius: var(--border-radius);
                margin: 20px 0;
                box-shadow: var(--box-shadow);
            }}
            
            table {{ 
                width: 100%; 
                border-collapse: collapse;
                margin: 20px 0;
                box-shadow: var(--box-shadow);
                border-radius: var(--border-radius);
                overflow: hidden;
            }}
            
            th, td {{ 
                border: 1px solid #eee; 
                padding: 12px 15px; 
                text-align: left;
            }}
            
            th {{ 
                background-color: var(--primary);
                color: white;
                font-weight: 600;
            }}
            
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            .recommendation {{
                padding: 15px;
                background-color: #e3f2fd;
                border-radius: var(--border-radius);
                margin-top: 10px;
                border-left: 5px solid var(--accent);
            }}
            
            .recommendation h4 {{
                color: var(--accent);
                margin-bottom: 8px;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 50px;
                padding: 20px;
                color: var(--light-text);
                font-size: 14px;
            }}
            
            a {{
                color: var(--primary);
                text-decoration: none;
            }}
            
            a:hover {{
                text-decoration: underline;
            }}
            
            .card {{
                background-color: white;
                border-radius: var(--border-radius);
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: var(--box-shadow);
            }}
            
            ul, ol {{
                margin-left: 20px;
                margin-bottom: 15px;
            }}
            
            li {{
                margin-bottom: 5px;
            }}
            
            @media print {{
                .section {{
                    break-inside: avoid;
                }}
                
                body {{
                    background-color: white;
                }}
                
                .container {{
                    max-width: 100%;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Informe de Accesibilidad Web</h1>
                <p><strong>URL analizada:</strong> {url}</p>
                <p><strong>Fecha:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
                <p><strong>Tipo de análisis:</strong> {'Página completa' if is_full_page else 'Vista inicial solamente'}</p>
                <p><strong>Dimensiones de captura:</strong> {screenshot.width}x{screenshot.height} píxeles</p>
                <div class="score-container">
                    <span class="score">{score}</span>
                    <div class="score-label">
                        <p>Puntuación global</p>
                        <p style="font-size: 14px; opacity: 0.9;">
                            {
                                "Excelente accesibilidad" if score >= 90 else
                                "Accesibilidad aceptable" if score >= 70 else
                                "Necesita mejoras importantes"
                            }
                        </p>
                    </div>
                </div>
            </div>
        
            <div class="section">
                <h2>📸 Captura de la página</h2>
                <p>Visualización del sitio web analizado:</p>
                <img src="data:image/png;base64,{img_str}" alt="Captura de la página web" class="screenshot">
            </div>
            
            <div class="section">
                <h2>📊 Resumen de problemas</h2>
                <p>La siguiente tabla muestra un resumen de los problemas de accesibilidad detectados:</p>
                <table>
                    <tr>
                        <th>Tipo de problema</th>
                        <th>Cantidad</th>
                        <th>Impacto</th>
                        <th>Relevancia WCAG</th>
                    </tr>
                    <tr>
                        <td>Contraste insuficiente</td>
                        <td>{len(contrast_issues)}</td>
                        <td>Medio-Alto</td>
                        <td>WCAG 1.4.3 (AA)</td>
                    </tr>
                    <tr>
                        <td>Texto en imágenes sin alternativa</td>
                        <td>{len(text_issues)}</td>
                        <td>Alto</td>
                        <td>WCAG 1.1.1 (A)</td>
                    </tr>
    """
    
    # Añadir problemas de daltonismo si se proporcionaron """Tony Mateo 23-EISN-2-044"""
    if colorblind_issues:
        for cb_type, issues in colorblind_issues.items():
            if issues:
                html += f"""
                <tr>
                    <td>Problemas para {cb_type}</td>
                    <td>{len(issues)}</td>
                    <td>Alto</td>
                    <td>WCAG 1.4.1 (A)</td>
                </tr>
                """
    
    html += """
                </table>
            </div>
    """
    
    # Agregar sección de problemas de contraste """Tony Mateo 23-EISN-2-044"""
    if contrast_issues:
        html += """
        <div class="section">
            <h2>🎨 Problemas de contraste</h2>
            <p>Se detectaron los siguientes problemas de contraste que pueden dificultar la lectura:</p>
        """
        
        for i, issue in enumerate(contrast_issues):
            severity_class = "high" if issue['severity'] == "Alto" else "medium"
            html += f"""
            <div class="issue">
                <div class="issue-header">
                    <h3>Problema de contraste #{i+1}</h3>
                    <span class="severity {severity_class}">{issue['severity']}</span>
                </div>
                <p><strong>Valor de contraste:</strong> {issue['contrast_value']:.2f}</p>
                <div class="recommendation">
                    <h4>Recomendación:</h4>
                    <p>Aumentar el contraste entre el texto y el fondo para cumplir con WCAG 2.1 AA (mínimo 4.5:1).</p>
                    <p>Considere utilizar colores más oscuros para el texto o un fondo más claro para mejorar la legibilidad.</p>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # Agregar sección de texto en imágenes """Tony Mateo 23-EISN-2-044"""
    if text_issues:
        html += """
        <div class="section">
            <h2>🖼️ Texto en imágenes sin alternativa adecuada</h2>
            <p>Se detectaron imágenes con texto que no tienen una descripción alternativa adecuada:</p>
        """
        
        for i, issue in enumerate(text_issues):
            html += f"""
            <div class="issue">
                <div class="issue-header">
                    <h3>Problema de texto #{i+1}</h3>
                    <span class="severity high">Alto</span>
                </div>
                <p><strong>Texto detectado:</strong> {issue['detected_text']}</p>
                <p><strong>Confianza de detección:</strong> {issue['confidence']:.2f}</p>
                <p><strong>Tiene texto alternativo:</strong> {"Sí" if issue.get('has_alt_text', False) else "No"}</p>
                
                {f'<p><strong>Texto alternativo actual:</strong> "{issue.get("alt_text", "")}"</p>' if issue.get('has_alt_text', False) else ''}
                
                <div class="recommendation">
                    <h4>Recomendación:</h4>
                    <p>{issue.get('recommendation', 'Añadir texto alternativo descriptivo que transmita la misma información que el texto en la imagen.')}</p>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # Agregar recomendaciones generales """Tony Mateo 23-EISN-2-044"""
    html += """
        <div class="section">
            <h2>📝 Recomendaciones generales</h2>
            <p>Basándonos en el análisis realizado, recomendamos las siguientes mejoras:</p>
            
            <div class="card">
                <h3>🎨 Mejoras de contraste</h3>
                <ul>
                    <li>Asegúrese de que el contraste entre texto y fondo cumpla con WCAG 2.1 nivel AA (4.5:1 para texto normal, 3:1 para texto grande)</li>
                    <li>Evite usar colores similares para texto y fondo</li>
                    <li>Considere usar herramientas como el Verificador de Contraste de WebAIM para validar sus combinaciones de colores</li>
                </ul>
            </div>
            
            <div class="card">
                <h3>🖼️ Texto alternativo para imágenes</h3>
                <ul>
                    <li>Proporcione texto alternativo (atributo alt) para todas las imágenes que contienen información</li>
                    <li>El texto alternativo debe comunicar el mismo contenido y función que la imagen</li>
                    <li>Para imágenes decorativas, use alt="" para que los lectores de pantalla las ignoren</li>
                    <li>Considere evitar el uso de texto dentro de imágenes cuando sea posible</li>
                </ul>
            </div>
            
            <div class="card">
                <h3>👁️ Diseño accesible para daltonismo</h3>
                <ul>
                    <li>No dependa únicamente del color para transmitir información importante</li>
                    <li>Use patrones, formas o texto adicional junto con el color</li>
                    <li>Elija combinaciones de colores que sean distinguibles para personas con daltonismo</li>
                    <li>Pruebe su sitio con simuladores de daltonismo para identificar problemas potenciales</li>
                </ul>
            </div>
            
            <div class="card">
                <h3>⌨️ Navegación y estructura</h3>
                <ul>
                    <li>Asegúrese de que todos los elementos interactivos sean accesibles mediante teclado</li>
                    <li>Use una estructura de encabezados jerárquica (h1-h6) para organizar el contenido</li>
                    <li>Proporcione etiquetas descriptivas para formularios y controles</li>
                    <li>Incluya texto alternativo para todas las imágenes informativas</li>
                    <li>Asegúrese de que el sitio sea navegable con lectores de pantalla</li>
                </ul>
            </div>
        </div>
        
        <div class="section">
            <h2>🔗 Referencias y recursos útiles</h2>
            <ul>
                <li><a href="https://www.w3.org/WAI/WCAG21/quickref/" target="_blank">Guía rápida de WCAG 2.1</a></li>
                <li><a href="https://webaim.org/resources/contrastchecker/" target="_blank">Verificador de contraste WebAIM</a></li>
                <li><a href="https://www.w3.org/WAI/tutorials/images/decision-tree/" target="_blank">Árbol de decisión para textos alternativos</a></li>
                <li><a href="https://color.a11y.com/" target="_blank">Herramienta de contraste de color para accesibilidad</a></li>
                <li><a href="https://wave.webaim.org/" target="_blank">WAVE - Herramienta de evaluación de accesibilidad web</a></li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Generado por el Analizador de Accesibilidad Web con Deep Learning</p>
            <p>Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
        </div>
    </div>
    </body>
    </html>
    """
    
    return html

# Función principal  """Tony Mateo 23-EISN-2-044"""
def main():
    """Función principal que ejecuta la aplicación Streamlit con mejoras visuales."""
    
    # Mostrar encabezado atractivo"""Tony Mateo 23-EISN-2-044"""
    display_header()
    
    # Inicializar componentes """Tony Mateo 23-EISN-2-044"""
    if 'text_detector' not in st.session_state:
        with st.spinner("Cargando modelos de deep learning..."):
            st.session_state.text_detector = TextDetectorDL(use_gpu=False)
    
    if 'colorblind_simulator' not in st.session_state:
        with st.spinner("Cargando simulador de daltonismo..."):
            st.session_state.colorblind_simulator = ColorBlindSimulator(use_gpu=False)
    
    # Sección de introducción y entrada de URL """Tony Mateo 23-EISN-2-044"""
    st.markdown("""
    <div class="card">
        <h3>📋 Instrucciones</h3>
        <p>Este analizador utiliza inteligencia artificial para detectar problemas de accesibilidad en sitios web, incluyendo:</p>
        <ul>
            <li>Contraste insuficiente que dificulta la lectura</li>
            <li>Texto en imágenes sin alternativas adecuadas</li>
            <li>Visualización para diferentes tipos de daltonismo</li>
        </ul>
        <p>Ingresa la URL de un sitio web para comenzar el análisis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Entrada de URL con mejor diseño """Tony Mateo 23-EISN-2-044"""
    col1, col2 = st.columns([3, 1])
    with col1:
        url = st.text_input("", value="https://example.com", placeholder="Ingrese la URL del sitio web")
    with col2:
        analyze_button = st.button("🔍 Analizar sitio", type="primary", use_container_width=True)
    
    # Opciones avanzadas """Tony Mateo 23-EISN-2-044"""
    with st.expander("⚙️ Opciones avanzadas"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_page_analysis = st.checkbox("Análisis de página completa", value=True, 
                                           help="Analiza toda la página incluyendo contenido que requiere scroll. Toma más tiempo.")
        
        with col2:
            max_scroll = st.slider("Máximo de secciones a analizar", 1, 20, 10, 
                                 help="Limita el número de secciones capturadas en páginas muy largas.")
    
    # Espaciador
    st.markdown('<div class="small-spacer"></div>', unsafe_allow_html=True)
    
    # Contenedor principal para mostrar resultados """Tony Mateo 23-EISN-2-044"""
    results_container = st.container()
    
    if analyze_button:
        if url:
            # Mostrar indicador de progreso mejorado """Tony Mateo 23-EISN-2-044"""
            progress_placeholder = st.empty()
            progress_placeholder.markdown("""
            <div style="padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #4361ee;">
                <h3 style="margin-bottom: 15px;">⚙️ Analizando sitio web...</h3>
                <div id="progress"></div>
            </div>
            """, unsafe_allow_html=True)
            
            # Crear directorio para capturas si no existe """Tony Mateo 23-EISN-2-044"""
            os.makedirs("screenshots", exist_ok=True)
            
            # Capturar página con el método seleccionado """Tony Mateo 23-EISN-2-044"""
            progress_message("Iniciando captura de página web...")
            web_capture = WebCapture(timeout=60)  # Aumentamos el timeout para páginas grandes """Tony Mateo 23-EISN-2-044"""
            
            if full_page_analysis:
                progress_message("Realizando captura de página completa (esto puede tomar un momento)...", "⏳")
                screenshot = web_capture.capture_full_page_screenshot(url, max_scroll=max_scroll)
                
                # Si falla la captura completa, intentar con captura normal como fallback """Tony Mateo 23-EISN-2-044"""
                if screenshot is None:
                    progress_message("La captura completa falló, intentando captura estándar...", "⚠️")
                    screenshot = web_capture.capture_screenshot(url)
            else:
                # Captura rápida (solo primera vista) """Tony Mateo 23-EISN-2-044"""
                progress_message("Realizando captura estándar...", "⏳")
                screenshot = web_capture.capture_screenshot(url)
            
            html_content = web_capture.get_page_source(url)
            web_capture.close()
            
            if screenshot is None:
                st.error("❌ No se pudo capturar la página. Verifique la URL e intente nuevamente.")
                return
            
            # Mostrar información sobre la captura """Tony Mateo 23-EISN-2-044"""
            screenshot_info = f"Dimensiones: {screenshot.width}x{screenshot.height} píxeles"
            progress_message(f"Página capturada correctamente. {screenshot_info}", "✅")
            
            progress_message("Analizando el DOM y la estructura de la página...", "🔍")
            
            # Extraer información del DOM """Tony Mateo 23-EISN-2-044"""
            dom_extractor = DOMExtractor()
            dom_images = []
            if html_content:
                dom_images = dom_extractor.extract_images_info(html_content)
                progress_message(f"Extraídas {len(dom_images)} imágenes del DOM", "📊")
            
            # Ejecutar análisis """Tony Mateo 23-EISN-2-044"""
            progress_message("Ejecutando análisis con deep learning...", "🧠")
            
            #  Análisis de contraste """Tony Mateo 23-EISN-2-044"""
            contrast_issues = analyze_contrast(screenshot)
            progress_message(f"Detectados {len(contrast_issues)} problemas de contraste", "🎨")
            
            #  Detección de texto en imágenes con deep learning """Tony Mateo 23-EISN-2-044"""
            text_detector = st.session_state.text_detector
            text_in_images = text_detector.detect_text_in_image(screenshot)
            
            # Vincular con información del DOM si está disponible """Tony Mateo 23-EISN-2-044"""
            for text_issue in text_in_images:
                x, y, w, h = text_issue['region']
                matched_dom_image = dom_extractor.match_image_with_dom(
                    (x, y, w, h), dom_images, screenshot.width, screenshot.height)
                
                if matched_dom_image:
                    # Evaluar texto alternativo """Tony Mateo 23-EISN-2-044"""
                    alt_text = matched_dom_image.get('alt', '')
                    evaluation = text_detector.evaluate_alt_text(
                        text_issue['detected_text'], alt_text)
                    
                    text_issue.update({
                        'has_alt_text': matched_dom_image.get('has_alt', False),
                        'alt_text': alt_text,
                        'alt_text_quality': evaluation.get('quality', 'Missing'),
                        'recommendation': evaluation.get('recommendation', '')
                    })
            
            # Filtrar solo los problemas (texto en imágenes  adecuado) """Tony Mateo 23-EISN-2-044"""
            text_issues = [
                t for t in text_in_images 
                if not t.get('has_alt_text', False) or t.get('alt_text_quality', 'Missing') != 'Good'
            ]
            progress_message(f"Detectados {len(text_issues)} textos en imágenes sin alternativas adecuadas", "🔤")
            
            #  Simulación de daltonismo y análisis  """Tony Mateo 23-EISN-2-044"""
            progress_message("Generando simulaciones de daltonismo...", "👁️")
            colorblind_simulator = st.session_state.colorblind_simulator
            colorblind_simulations = colorblind_simulator.get_all_simulations(screenshot)
            
            # Analizar problemas específicos para cada tipo de daltonismo """Tony Mateo 23-EISN-2-044"""
            colorblind_issues = {
                'protanopia': colorblind_simulator.analyze_color_contrast_issues(screenshot, 'protanopia'),
                'deuteranopia': colorblind_simulator.analyze_color_contrast_issues(screenshot, 'deuteranopia'),
                'tritanopia': colorblind_simulator.analyze_color_contrast_issues(screenshot, 'tritanopia')
            }
            
            # Limpiar el placeholder de progreso cuando se complete """Tony Mateo 23-EISN-2-044"""
            progress_placeholder.empty()
            
            # Mostrar mensaje de éxito """Tony Mateo 23-EISN-2-044"""
            if full_page_analysis:
                st.success("✅ Análisis de página completa finalizado correctamente!")
            else:
                st.success("✅ Análisis de vista inicial finalizado correctamente!")
            
            # Espaciador """Tony Mateo 23-EISN-2-044"""
            st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
            
            # Mostrar resumen general con métricas visuales atractivas """Tony Mateo 23-EISN-2-044"""
            st.markdown("<h2>📊 Panel de Accesibilidad</h2>", unsafe_allow_html=True)
            
            # Calcular puntuación """Tony Mateo 23-EISN-2-044"""
            max_score = 100
            penalty_per_contrast = 3
            penalty_per_text = 5
            penalty_per_colorblind = 2
            
            # Contar problemas de daltonismo """Tony Mateo 23-EISN-2-044"""
            total_colorblind_issues = sum(len(issues) for issues in colorblind_issues.values())
            
            score = max(0, max_score - 
                       (len(contrast_issues) * penalty_per_contrast) - 
                       (len(text_issues) * penalty_per_text) - 
                       (total_colorblind_issues * penalty_per_colorblind))
            
            # Mostrar puntuación y métricas en una fila de tarjetas """Tony Mateo 23-EISN-2-044"""
            cols = st.columns(4)
            
            # Color basado en puntuación """Tony Mateo 23-EISN-2-044"""
            score_color = "success" if score >= 90 else "warning" if score >= 70 else "error"
            
            with cols[0]:
                metric_card("Puntuación", f"{score}/100", 
                           "Calificación global de accesibilidad", 
                           icon="🏆", color=score_color)
            
            with cols[1]:
                metric_card("Problemas de contraste", str(len(contrast_issues)), 
                           "Áreas con contraste insuficiente", 
                           icon="🔍", color="warning" if len(contrast_issues) > 0 else "success")
            
            with cols[2]:
                metric_card("Texto en imágenes", str(len(text_issues)), 
                           "Sin alternativas adecuadas", 
                           icon="🖼️", color="warning" if len(text_issues) > 0 else "success")
            
            with cols[3]:
                metric_card("Problemas daltonismo", str(total_colorblind_issues), 
                           "Dificultades de percepción de color", 
                           icon="👁️", color="warning" if total_colorblind_issues > 0 else "success")
            
            # Espaciador """Tony Mateo 23-EISN-2-044"""
            st.markdown('<div class="small-spacer"></div>', unsafe_allow_html=True)
            
            # Mostrar captura original con estilo """Tony Mateo 23-EISN-2-044"""
            st.markdown(f"""
            <div class="card">
                <h3>🖥️ Página web capturada</h3>
                <p>Captura de pantalla {' completa' if full_page_analysis else ' de vista inicial'} ({screenshot.width}x{screenshot.height} píxeles)</p>
            </div>
            """, unsafe_allow_html=True)
            st.image(screenshot, use_column_width=True)
            
            # Gráfico de resumen si matplotlib está disponible """Tony Mateo 23-EISN-2-044"""
            if matplotlib_available:
                st.markdown("<h3>📊 Distribución de problemas detectados</h3>", unsafe_allow_html=True)
                
                chart = create_accessibility_chart(contrast_issues, text_issues, colorblind_issues)
                if chart is not None:
                    st.pyplot(chart)
            
            # Espaciador """Tony Mateo 23-EISN-2-044"""
            st.markdown('<div class="small-spacer"></div>', unsafe_allow_html=True)
            
            # Tabs con resultados detallados """Tony Mateo 23-EISN-2-044"""
            tab1, tab2, tab3, tab4 = st.tabs(["🎨 Contraste", "🔤 Texto en imágenes", "👁️ Daltonismo", "📝 Recomendaciones"])
            
            with tab1:
                st.markdown(f"""
                <div class="card">
                    <h3>Análisis de contraste</h3>
                    <p>Se encontraron <span class="{'quality-high' if len(contrast_issues) == 0 else 'quality-low'}">{len(contrast_issues)}</span> posibles problemas de contraste</p>
                </div>
                """, unsafe_allow_html=True)
                
                if contrast_issues:
                    # Crear imagen con marcas """Tony Mateo 23-EISN-2-044"""
                    marked_img = screenshot.copy()
                    draw = ImageDraw.Draw(marked_img)
                    
                    for issue in contrast_issues:
                        x, y, w, h = issue['region']
                        # Verificar dimensiones válidas """Tony Mateo 23-EISN-2-044"""
                        if w > 0 and h > 0:
                            # Dibujar rectángulo rojo alrededor del problema """Tony Mateo 23-EISN-2-044"""
                            draw.rectangle([x, y, x+w, y+h], outline="red", width=3)
                    
                    st.image(marked_img, caption="Problemas de contraste marcados en rojo", use_column_width=True)
                    
                    # Mostrar primeros 5 problemas en detalle con mejor formato """Tony Mateo 23-EISN-2-044"""
                    for i, issue in enumerate(contrast_issues[:5]):
                        with st.expander(f"Problema #{i+1} - Severidad: {issue['severity']}"):
                            cols = st.columns(2)
                            with cols[0]:
                                x, y, w, h = issue['region']
                                # Verificar que las dimensiones sean válidas
                                if w > 0 and h > 0:
                                    # Asegurarse de que las coordenadas estén dentro de los límites de la imagen
                                    x = max(0, x)
                                    y = max(0, y)
                                    x_end = min(screenshot.width, x + w)
                                    y_end = min(screenshot.height, y + h)
                                    
                                    # Solo recortar y mostrar si el área es válida
                                    if x_end > x and y_end > y:
                                        region_img = screenshot.crop((x, y, x_end, y_end))
                                        st.image(region_img, width=200)
                                    else:
                                        st.warning("Región demasiado pequeña para mostrar")
                                else:
                                    st.warning("Región con dimensiones inválidas")
                                #x, y, w, h = issue['region']
                                ## Verificar dimensiones válidas
                                #if w > 0 and h > 0:
                                #    # Extraer región
                                #    region_img = screenshot.crop((x, y, x+w, y+h))
                                #    st.image(region_img, width=200)
                                #else:
                                #    st.warning("Región demasiado pequeña para mostrar")
                            with cols[1]:
                                st.markdown(f"""
                                    <div style="padding: 15px; background-color: #f8f9fa; border-radius: 10px;">
                                        <h4>Detalles del problema</h4>
                                        <p><strong>Valor de contraste:</strong> {issue['contrast_value']:.2f}</p>
                                        <p><strong>Severidad:</strong> <span class="{'quality-high' if issue['severity'] == 'Bajo' else 'quality-medium' if issue['severity'] == 'Medio' else 'quality-low'}">{issue['severity']}</span></p>
                                        <h4>Recomendación:</h4>
                                        <p>Aumentar el contraste entre texto y fondo para cumplir con WCAG 2.1 AA (relación mínima de 4.5:1)</p>
                                    </div>
                                """, unsafe_allow_html=True)
                else:
                    st.success("✅ ¡No se encontraron problemas de contraste!")
            
            with tab2:
                st.markdown(f"""
                <div class="card">
                    <h3>Texto en imágenes</h3>
                    <p>Se encontraron <span class="{'quality-high' if len(text_issues) == 0 else 'quality-low'}">{len(text_issues)}</span> imágenes con texto sin alternativas adecuadas</p>
                </div>
                """, unsafe_allow_html=True)
                
                if text_issues:
                    # Crear imagen con marcas """Tony Mateo 23-EISN-2-044"""
                    marked_img = screenshot.copy()
                    draw = ImageDraw.Draw(marked_img)
                    
                    for issue in text_issues:
                        x, y, w, h = issue['region']
                        # Verificar dimensiones válidas """Tony Mateo 23-EISN-2-044"""
                        if w > 0 and h > 0:
                            # Dibujar rectángulo azul alrededor del problema """Tony Mateo 23-EISN-2-044"""
                            draw.rectangle([x, y, x+w, y+h], outline="blue", width=3)
                            # Añadir etiqueta con texto detectado """Tony Mateo 23-EISN-2-044"""
                            draw.text((x, y-15), issue['detected_text'][:20], fill="blue")
                    
                    st.image(marked_img, caption="Texto en imágenes detectado con deep learning", use_column_width=True)
                    
                    # Mostrar información detallada mejorada """Tony Mateo 23-EISN-2-044"""
                    st.subheader("Detalles de las detecciones")
                    for i, issue in enumerate(text_issues):
                        with st.expander(f"Texto #{i+1}: {issue['detected_text'][:30]}{'...' if len(issue['detected_text']) > 30 else ''}"):
                            cols = st.columns(2)
                            with cols[0]:
                                x, y, w, h = issue['region']
                                # Verificar dimensiones válidas """Tony Mateo 23-EISN-2-044"""
                                if w > 0 and h > 0:
                                    # Extraer región """Tony Mateo 23-EISN-2-044"""
                                    region_img = screenshot.crop((x, y, x+w, y+h))
                                    st.image(region_img, width=200)
                                else:
                                    st.warning("Región demasiado pequeña para mostrar")
                                
                            with cols[1]:
                                alt_status = "No" if not issue.get('has_alt_text', False) else "Sí"
                                alt_quality = issue.get('alt_text_quality', 'Missing')
                                quality_class = "quality-high" if alt_quality == "Good" else "quality-medium" if alt_quality == "Average" else "quality-low"
                                
                                st.markdown(f"""
                                    <div style="padding: 15px; background-color: #f8f9fa; border-radius: 10px;">
                                        <h4>Texto detectado:</h4>
                                        <p style="background-color: white; padding: 10px; border-radius: 5px;">{issue['detected_text']}</p>
                                        <p><strong>Confianza de detección:</strong> {issue['confidence']:.2f}</p>
                                        <p><strong>Tiene texto alternativo:</strong> {alt_status}</p>
                                        
                                        {f'<p><strong>Texto alternativo actual:</strong> "{issue.get("alt_text", "")}"</p>' if issue.get('has_alt_text', False) else ''}
                                        {f'<p><strong>Calidad:</strong> <span class="{quality_class}">{alt_quality}</span></p>' if issue.get('has_alt_text', False) else ''}
                                        
                                        <h4>Recomendación:</h4>
                                        <p>{issue.get('recommendation', 'Añadir texto alternativo descriptivo que transmita la misma información que el texto en la imagen.')}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                else:
                    st.success("✅ ¡No se detectó texto en imágenes sin alternativas adecuadas!")
            
            with tab3:
                st.markdown("""
                <div class="card">
                    <h3>Simulación de daltonismo</h3>
                    <p>Esta función muestra cómo vería la página una persona con diferentes tipos de daltonismo, 
                    ayudando a comprender problemas de accesibilidad relacionados con el color.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Obtener información educativa sobre daltonismo """Tony Mateo 23-EISN-2-044"""
                colorblind_info = colorblind_simulator.get_colorblind_info()
                
                # Crear selectores para tipo de daltonismo con mejor presentación """Tony Mateo 23-EISN-2-044"""
                cb_options = ["Vista normal", "Protanopia", "Deuteranopia", "Tritanopia", "Acromatopsia"]
                cb_icons = ["👁️", "🔴", "🟢", "🔵", "⚪"]
                
                # Crear tabs para los diferentes tipos """Tony Mateo 23-EISN-2-044"""
                cb_tabs = st.tabs([f"{icon} {opt}" for icon, opt in zip(cb_icons, cb_options)])
                
                with cb_tabs[0]:  # Vista normal """Tony Mateo 23-EISN-2-044"""
                    st.image(colorblind_simulations['original'], caption="Vista normal", use_column_width=True)
                    st.info("Esta es la apariencia normal de la página web tal como la vería una persona sin deficiencias de visión cromática.")
                
                for i, cb_type in enumerate(["protanopia", "deuteranopia", "tritanopia", "achromatopsia"]):
                    with cb_tabs[i+1]:
                        # Mostrar imagen simulada """Tony Mateo 23-EISN-2-044"""
                        st.image(colorblind_simulations[cb_type], caption=f"Simulación de {cb_options[i+1]}", use_column_width=True)
                        
                        # Mostrar información educativa mejorada """Tony Mateo 23-EISN-2-044"""
                        if cb_type in colorblind_info:
                            info = colorblind_info[cb_type]
                            
                            st.markdown(f"""
                            <div style="padding: 15px; background-color: #f8f9fa; border-radius: 10px;">
                                <h4>{info['name']}</h4>
                                <p>{info['description']}</p>
                                <p><strong>Prevalencia:</strong> {info['prevalence']}</p>
                                <p><strong>Impacto en accesibilidad web:</strong> {info['impact']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Mostrar problemas específicos para este tipo de daltonismo """Tony Mateo 23-EISN-2-044"""
                        if cb_type in colorblind_issues and colorblind_issues[cb_type]:
                            issues = colorblind_issues[cb_type]
                            st.subheader(f"Problemas detectados para {cb_options[i+1]}")
                            
                            # Crear imagen con problemas marcados """Tony Mateo 23-EISN-2-044"""
                            marked_img = colorblind_simulations[cb_type].copy()
                            draw = ImageDraw.Draw(marked_img)
                            
                            for issue in issues:
                                x, y, w, h = issue['region']
                                # Verificar dimensiones válidas """Tony Mateo 23-EISN-2-044"""
                                if w > 0 and h > 0:
                                    # Dibujar rectángulo amarillo alrededor del problema """Tony Mateo 23-EISN-2-044"""
                                    draw.rectangle([x, y, x+w, y+h], outline="yellow", width=3)
                            
                            st.image(marked_img, caption=f"Áreas problemáticas para personas con {cb_options[i+1]}", use_column_width=True)
                            
                            for j, issue in enumerate(issues[:3]):  # Mostrar solo los primeros 3 problemas """Tony Mateo 23-EISN-2-044"""
                                with st.expander(f"Problema #{j+1} para {cb_options[i+1]} - Severidad: {issue['severity']}"):
                                    cols = st.columns(2)
                                    with cols[0]:
                                        x, y, w, h = issue['region']
                                        # Verificar dimensiones válidas """Tony Mateo 23-EISN-2-044"""
                                        if w > 0 and h > 0:
                                            # Mostrar comparación lado a lado """Tony Mateo 23-EISN-2-044"""
                                            normal_region = screenshot.crop((x, y, x+w, y+h))
                                            cb_region = colorblind_simulations[cb_type].crop((x, y, x+w, y+h))
                                            
                                            st.markdown("<p><strong>Comparación:</strong></p>", unsafe_allow_html=True)
                                            comp_cols = st.columns(2)
                                            with comp_cols[0]:
                                                st.markdown("<p style='text-align: center;'>Vista normal</p>", unsafe_allow_html=True)
                                                st.image(normal_region)
                                            with comp_cols[1]:
                                                st.markdown(f"<p style='text-align: center;'>Con {cb_options[i+1]}</p>", unsafe_allow_html=True)
                                                st.image(cb_region)
                                        else:
                                            st.warning("Región demasiado pequeña para mostrar")
                                    
                                    with cols[1]:
                                        st.markdown(f"""
                                        <div style="padding: 15px; background-color: #f8f9fa; border-radius: 10px;">
                                            <h4>Detalles del problema</h4>
                                            <p><strong>Diferencia de color:</strong> {issue['color_difference']:.2f}</p>
                                            <p><strong>Severidad:</strong> <span class="{'quality-high' if issue['severity'] == 'Bajo' else 'quality-medium' if issue['severity'] == 'Medio' else 'quality-low'}">{issue['severity']}</span></p>
                                            
                                            <h4>Recomendaciones:</h4>
                                            <ul>
                                                <li>No depender solo del color para transmitir información</li>
                                                <li>Usar patrones, formas o texto adicional</li>
                                                <li>Aumentar el contraste entre colores problemáticos</li>
                                                <li>Considerar paletas de colores seguras para daltonismo</li>
                                            </ul>
                                        </div>
                                        """, unsafe_allow_html=True)
                        else:
                            st.success(f"✅ No se detectaron problemas específicos para personas con {cb_options[i+1]}")
            
            with tab4:
                # Recomendaciones generales con formato mejorado """Tony Mateo 23-EISN-2-044"""
                st.markdown("""
                <div class="card">
                    <h3>Recomendaciones de accesibilidad</h3>
                    <p>Basado en el análisis, estas son las recomendaciones para mejorar la accesibilidad del sitio:</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Recomendaciones basadas en problemas detectados
                if contrast_issues or text_issues or total_colorblind_issues > 0:
                    # Mostrar recomendaciones específicas
                    if contrast_issues:
                        st.markdown("""
                        <div style="margin-bottom: 15px; padding: 15px; background-color: #f8f9fa; border-radius: 10px;">
                            <h4>🎨 Mejorar contraste</h4>
                            <p>Para cumplir con WCAG 2.1 AA, asegúrese de que el contraste entre texto y fondo sea al menos 4.5:1 (3:1 para texto grande).</p>
                            <ul>
                                <li>Considere usar colores más oscuros para el texto</li>
                                <li>Evite texto sobre fondos con patrones o imágenes</li>
                                <li>Use herramientas como el Verificador de Contraste de WebAIM para validar colores</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if text_issues:
                        st.markdown("""
                        <div style="margin-bottom: 15px; padding: 15px; background-color: #f8f9fa; border-radius: 10px;">
                            <h4>🖼️ Texto alternativo para imágenes</h4>
                            <p>Proporcione texto alternativo adecuado para todas las imágenes que contienen información textual.</p>
                            <ul>
                                <li>El texto alternativo debe comunicar la misma información que está presente en la imagen</li>
                                <li>Sea descriptivo y conciso</li>
                                <li>Para imágenes con texto, incluya ese texto en el atributo alt</li>
                                <li>Considere si el texto en la imagen podría ser parte del contenido HTML para mejor accesibilidad</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if total_colorblind_issues > 0:
                        st.markdown("""
                        <div style="margin-bottom: 15px; padding: 15px; background-color: #f8f9fa; border-radius: 10px;">
                            <h4>👁️ Diseño accesible para daltonismo</h4>
                            <p>Mejore la accesibilidad para personas con diferentes tipos de daltonismo.</p>
                            <ul>
                                <li>No dependa únicamente del color para transmitir información importante</li>
                                <li>Use combinaciones de formas, patrones y etiquetas además del color</li>
                                <li>Considere usar paletas de colores seguras para daltonismo</li>
                                <li>Asegúrese de que el sitio sea navegable con lectores de pantalla</li>
                            <li>Incluya subtítulos y transcripciones para contenido multimedia</li>
                            <li>Haga que el contenido sea legible y comprensible</li>
                            <li>Asegúrese de que las animaciones y efectos sean sutiles y no provoquen mareos</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Recursos adicionales
                    st.markdown("""
                    <div style="margin-top: 15px; padding: 15px; background-color: #f8f9fa; border-radius: 10px;">
                        <h4>🔗 Recursos adicionales</h4>
                        <ul>
                            <li><a href="https://www.w3.org/WAI/WCAG21/quickref/" target="_blank">Guía rápida de WCAG 2.1</a></li>
                            <li><a href="https://webaim.org/resources/contrastchecker/" target="_blank">Verificador de contraste WebAIM</a></li>
                            <li><a href="https://www.w3.org/WAI/tutorials/images/decision-tree/" target="_blank">Árbol de decisión para textos alternativos</a></li>
                            <li><a href="https://accessibilityinsights.io/" target="_blank">Accessibility Insights</a></li>
                            <li><a href="https://wave.webaim.org/" target="_blank">WAVE Web Accessibility Evaluation Tool</a></li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.success("""
                    ✅ ¡Felicidades! No se encontraron problemas significativos de accesibilidad.
                    
                    Sin embargo, este es un análisis automatizado y limitado. Para garantizar la máxima accesibilidad, recomendamos:
                    
                    - Realizar pruebas manuales adicionales
                    - Obtener retroalimentación de usuarios con discapacidades
                    - Seguir las pautas WCAG 2.1 nivel AA o AAA
                    """)
                
                # Botón para descargar informe mejorado visualmente """Tony Mateo 23-EISN-2-044"""
                st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
                
                report_html = generate_html_report(
                    url, 
                    screenshot, 
                    contrast_issues, 
                    text_issues, 
                    score, 
                    colorblind_issues, 
                    is_full_page=full_page_analysis
                )
                
                st.download_button(
                    label="📥 Descargar informe completo",
                    data=report_html,
                    file_name=f"accesibilidad_{url.replace('https://', '').replace('http://', '').split('/')[0]}.html",
                    mime="text/html",
                    help="Descarga un informe HTML detallado con todos los problemas y recomendaciones",
                )

# Llamada a la función principal al ejecutar el script """Tony Mateo 23-EISN-2-044"""
if __name__ == "__main__":
    main() 