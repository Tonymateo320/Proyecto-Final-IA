"""
Visualizador 3D de la estructura DOM de páginas web.

Este módulo implementa funcionalidades para crear representaciones tridimensionales 
de la estructura jerárquica del DOM de una página web, permitiendo visualizar 
la estructura semántica y profundidad de los elementos.
"""

import torch
import numpy as np
from bs4 import BeautifulSoup
import json
import logging
import random
from typing import Dict, List, Any, Tuple, Optional

# Configurar logging Tony Mateo 23-EISN-2-044
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DOM3DVisualizer:
    """
    Clase para generar visualizaciones 3D de la estructura del DOM.
    """
    
    def __init__(self):
        """Inicializa el visualizador 3D del DOM."""
        logging.info("Inicializando DOM3DVisualizer")
        
        # Definir colores para diferentes tipos de elementos Tony Mateo 23-EISN-2-044
        self.element_colors = {
            # Elementos de estructura principal Tony Mateo 23-EISN-2-044
            'html': '#E8EAED',
            'body': '#C8D1E0',
            'head': '#B8C4D4',
            
            # Elementos de sección Tony Mateo 23-EISN-2-044
            'header': '#5C8AE6',
            'footer': '#5C8AE6',
            'nav': '#7B68EE',
            'main': '#4285F4',
            'section': '#5E97F6',
            'article': '#4FC3F7',
            'aside': '#B388FF',
            'div': '#A0C3FF',
            
            # Elementos de encabezado Tony Mateo 23-EISN-2-044
            'h1': '#FF8A65',
            'h2': '#FF9E80',
            'h3': '#FFAB91',
            'h4': '#FFCC80',
            'h5': '#FFD180',
            'h6': '#FFE0B2',
            
            # Elementos de texto Tony Mateo 23-EISN-2-044
            'p': '#81C784',
            'span': '#A5D6A7',
            'blockquote': '#4DB6AC',
            
            # Elementos de lista Tony Mateo 23-EISN-2-044
            'ul': '#FFA726',
            'ol': '#FFB74D',
            'li': '#FFCC80',
            
            # Elementos de tabla Tony Mateo 23-EISN-2-044
            'table': '#BA68C8',
            'tr': '#CE93D8',
            'td': '#E1BEE7',
            'th': '#D1C4E9',
            
            # Elementos de formulario Tony Mateo 23-EISN-2-044
            'form': '#FF7043',
            'input': '#FF8A65',
            'button': '#FFA726',
            'select': '#FFB74D',
            'textarea': '#FFCC80',
            
            # Elementos multimedia Tony Mateo 23-EISN-2-044
            'img': '#26A69A',
            'video': '#26C6DA',
            'audio': '#29B6F6',
            'iframe': '#42A5F5',
            
            # Elemento por defecto para cualquier otro tipo Tony Mateo 23-EISN-2-044
            'default': '#9E9E9E'
        }
        
        # Definir importancia relativa de los elementos para altura en visualización
        self.element_importance = {
            # Elementos principales/estructurales Tony Mateo 23-EISN-2-044
            'html': 10,
            'body': 9,
            'head': 8,
            'main': 8,
            'header': 7,
            'footer': 7,
            'nav': 7,
            
            # Elementos de contenido principal Tony Mateo 23-EISN-2-044
            'section': 6,
            'article': 6,
            'aside': 6,
            
            # Encabezados Tony Mateo 23-EISN-2-044
            'h1': 5,
            'h2': 4.8,
            'h3': 4.6,
            'h4': 4.4,
            'h5': 4.2,
            'h6': 4,
            
            # Contenedores comunes Tony Mateo 23-EISN-2-044
            'div': 3.5,
            'form': 5,
            
            # Elementos de contenido Tony Mateo 23-EISN-2-044
            'p': 3,
            'ul': 3,
            'ol': 3,
            'li': 2.5,
            'table': 4,
            'tr': 2,
            'td': 1.5,
            'th': 2,
            
            # Elementos en línea e interactivos Tony Mateo 23-EISN-2-044
            'span': 1,
            'a': 2,
            'button': 2.5,
            'input': 2.5,
            'img': 3,
            'video': 4,
            'audio': 3,
            'iframe': 4,
            
            # Valor por defecto Tony Mateo 23-EISN-2-044
            'default': 2
        }
    
    def parse_dom(self, html_content: str) -> Dict:
        """
        Analiza el DOM de una página web y crea una estructura de datos jerárquica.
        
        Args:
            html_content (str): Contenido HTML de la página
            
        Returns:
            Dict: Estructura jerárquica del DOM
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Función recursiva para procesar nodos Tony Mateo 23-EISN-2-044
            def process_node(node, depth=0):
                # Ignorar nodos de texto y comentarios
                if node.name is None:
                    return None
                
                # Obtener tag name Tony Mateo 23-EISN-2-044
                tag_name = node.name.lower()
                
                # Obtener atributos importantes Tony Mateo 23-EISN-2-044
                attributes = {}
                for attr in ['id', 'class', 'role', 'aria-label']:
                    if node.has_attr(attr):
                        attributes[attr] = node[attr]
                
                # Contenido de texto resumido (si existe) Tony Mateo 23-EISN-2-044
                text_content = ""
                if node.string and node.string.strip():
                    text = node.string.strip()
                    text_content = text[:50] + "..." if len(text) > 50 else text
                
                # Estructura del nodo Tony Mateo 23-EISN-2-044
                node_data = {
                    'tag': tag_name,
                    'depth': depth,
                    'attributes': attributes,
                    'text_preview': text_content,
                    'children': []
                }
                
                # Añadir dimensiones visuales para la representación 3D Tony Mateo 23-EISN-2-044
                node_data['visual'] = {
                    'color': self.element_colors.get(tag_name, self.element_colors['default']),
                    'importance': self.element_importance.get(tag_name, self.element_importance['default']),
                    'width': 1.0,  # Valor base, se ajustará luego
                    'height': self.element_importance.get(tag_name, self.element_importance['default']),
                    'x': 0,  # Se calculará luego
                    'y': 0,  # Se calculará luego
                    'z': depth  # Profundidad en el árbol = coordenada Z Tony Mateo 23-EISN-2-044
                }
                
                # Procesar hijos recursivamente Tony Mateo 23-EISN-2-044
                for child in node.children:
                    child_data = process_node(child, depth + 1)
                    if child_data:
                        node_data['children'].append(child_data)
                
                return node_data
            
            # Comenzar el procesamiento desde el elemento raíz Tony Mateo 23-EISN-2-044
            dom_tree = process_node(soup.html if soup.html else soup)
            
            # Calcular posiciones X e Y
            self._calculate_positions(dom_tree)
            
            return dom_tree
            
        except Exception as e:
            logging.error(f"Error al analizar el DOM: {e}")
            return {"tag": "error", "message": str(e)}
    
    def _calculate_positions(self, node, x=0, y=0, width=100):
        """
        Calcula las posiciones X e Y para cada nodo en la visualización.
        
        Args:
            node (Dict): Nodo actual
            x (float): Posición X base
            y (float): Posición Y base
            width (float): Ancho disponible para este nodo y sus hermanos
        """
        node['visual']['x'] = x
        node['visual']['y'] = y
        node['visual']['width'] = width
        
        if not node['children']:
            return
        
        # Calcular el ancho para cada hijo Tony Mateo 23-EISN-2-044
        child_width = width / max(1, len(node['children']))
        
        # Asignar posiciones a los hijos Tony Mateo 23-EISN-2-044
        current_x = x
        for child in node['children']:
            self._calculate_positions(child, 
                                      current_x, 
                                      y + node['visual']['height'] * 2,  # Espacio vertical entre niveles
                                      child_width)
            current_x += child_width
    
    def generate_3d_visualization_data(self, html_content: str) -> Dict:
        """
        Genera los datos para la visualización 3D del DOM.
        
        Args:
            html_content (str): Contenido HTML de la página
            
        Returns:
            Dict: Datos estructurados para la visualización 3D
        """
        # Analizar el DOM Tony Mateo 23-EISN-2-044
        dom_tree = self.parse_dom(html_content)
        
        # Extraer elementos para la visualización 3D Tony Mateo 23-EISN-2-044
        nodes = []
        links = []
        
        def extract_visualization_data(node, parent_id=None, node_id=None):
            if not node_id:
                node_id = 0
            
            # Crear datos del nodo para visualización Tony Mateo 23-EISN-2-044
            nodes.append({
                'id': node_id,
                'tag': node['tag'],
                'depth': node['depth'],
                'text': node.get('text_preview', ''),
                'x': node['visual']['x'],
                'y': node['visual']['y'],
                'z': node['visual']['z'],
                'color': node['visual']['color'],
                'height': node['visual']['height'],
                'width': node['visual']['width']
            })
            
            # Crear enlace al padre si existe Tony Mateo 23-EISN-2-044
            if parent_id is not None:
                links.append({
                    'source': parent_id,
                    'target': node_id
                })
            
            # Procesar hijos recursivamente Tony Mateo 23-EISN-2-044
            current_id = node_id
            for child in node['children']:
                current_id += 1
                current_id = extract_visualization_data(child, node_id, current_id)
            
            return current_id
        
        # Extraer datos comenzando desde la raíz Tony Mateo 23-EISN-2-044
        extract_visualization_data(dom_tree)
        
        return {
            'nodes': nodes,
            'links': links
        }
    
    def analyze_hierarchy_quality(self, html_content: str) -> Dict:
        """
        Analiza la calidad de la jerarquía del DOM.
        
        Args:
            html_content (str): Contenido HTML de la página
            
        Returns:
            Dict: Análisis de la jerarquía con problemas y recomendaciones
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            issues = []
            
            # Verificar estructura de encabezados Tony Mateo 23-EISN-2-044
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            heading_levels = [int(h.name[1]) for h in headings]
            
            # Comprobar si hay un solo h1 Tony Mateo 23-EISN-2-044
            h1_count = heading_levels.count(1)
            if h1_count == 0:
                issues.append({
                    'type': 'heading_hierarchy',
                    'severity': 'high',
                    'message': 'No se encontró un encabezado H1 en la página',
                    'recommendation': 'Añadir un encabezado H1 como título principal de la página'
                })
            elif h1_count > 1:
                issues.append({
                    'type': 'heading_hierarchy',
                    'severity': 'medium',
                    'message': f'Se encontraron múltiples encabezados H1 ({h1_count})',
                    'recommendation': 'Usar solo un encabezado H1 como título principal de la página'
                })
            
            # Comprobar saltos en la jerarquía de encabezados Tony Mateo 23-EISN-2-044
            for i in range(len(heading_levels) - 1):
                if heading_levels[i+1] > heading_levels[i] + 1:
                    issues.append({
                        'type': 'heading_hierarchy',
                        'severity': 'medium',
                        'message': f'Salto en la jerarquía de encabezados: H{heading_levels[i]} a H{heading_levels[i+1]}',
                        'recommendation': f'Evitar saltos en la jerarquía de encabezados. Usar H{heading_levels[i]+1} después de H{heading_levels[i]}'
                    })
            
            # Verificar uso de elementos semánticos Tony Mateo 23-EISN-2-044
            semantic_elements = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']
            semantic_count = {}
            for elem in semantic_elements:
                count = len(soup.find_all(elem))
                semantic_count[elem] = count
            
            if semantic_count['main'] == 0:
                issues.append({
                    'type': 'semantic_structure',
                    'severity': 'high',
                    'message': 'No se encontró un elemento <main>',
                    'recommendation': 'Añadir un elemento <main> para el contenido principal de la página'
                })
            
            if semantic_count['main'] > 1:
                issues.append({
                    'type': 'semantic_structure',
                    'severity': 'medium',
                    'message': 'Se encontraron múltiples elementos <main>',
                    'recommendation': 'Usar solo un elemento <main> por página'
                })
            
            # Verificar anidamiento excesivo Tony Mateo 23-EISN-2-044
            all_elements = soup.find_all()
            max_depth = 0
            deep_elements = []
            
            for element in all_elements:
                depth = len(list(element.parents))
                if depth > max_depth:
                    max_depth = depth
                
                if depth > 10:  
                    deep_elements.append({
                        'tag': element.name,
                        'depth': depth
                    })
            
            if len(deep_elements) > 0:
                issues.append({
                    'type': 'nesting',
                    'severity': 'low',
                    'message': f'Se detectaron {len(deep_elements)} elementos con anidamiento excesivo (profundidad > 10)',
                    'recommendation': 'Simplificar la estructura del DOM para mejorar el rendimiento y mantenibilidad'
                })
            
            # Contar número total de elementos Tony Mateo 23-EISN-2-044
            total_elements = len(all_elements)
            
            # Calcular calidad general (escala 0-100) Tony Mateo 23-EISN-2-044
            num_issues = len(issues)
            severity_weights = {'high': 3, 'medium': 2, 'low': 1}
            weighted_issues = sum(severity_weights[issue['severity']] for issue in issues)
            
            # Fórmula simplificada para calcular la calidad Tony Mateo 23-EISN-2-044
            quality_score = max(0, 100 - (weighted_issues * 5))
            
            return {
                'issues': issues,
                'statistics': {
                    'total_elements': total_elements,
                    'max_depth': max_depth,
                    'semantic_elements': semantic_count
                },
                'quality_score': quality_score
            }
            
        except Exception as e:
            logging.error(f"Error al analizar la jerarquía del DOM: {e}")
            return {
                'issues': [{
                    'type': 'error',
                    'severity': 'high',
                    'message': f'Error al analizar la jerarquía: {e}',
                    'recommendation': 'Verificar que el HTML sea válido'
                }],
                'quality_score': 0
            }
    
    def get_3d_visualization_code(self) -> str:
        """
        Retorna el código JavaScript necesario para la visualización 3D.
        
        Returns:
            str: Código JavaScript para la visualización 3D
        """
        return """
        function create3DVisualization(containerId, data) {
            // Configurar escena Three.js
            const container = document.getElementById(containerId);
            const width = container.clientWidth;
            const height = 500;
            
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf0f0f0);
            
            const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
            camera.position.z = 50;
            camera.position.y = 20;
            camera.position.x = 20;
            
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(width, height);
            container.appendChild(renderer.domElement);
            
            // Añadir controles
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.25;
            
            // Añadir luz
            const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
            directionalLight.position.set(1, 1, 1);
            scene.add(directionalLight);
            
            // Crear objetos para nodos
            const nodes = data.nodes;
            const links = data.links;
            const nodeObjects = {};
            const scale = 2; // Factor de escala para espaciado
            
            nodes.forEach(node => {
                // Crear geometría para el nodo
                const width = node.width * scale * 0.2;
                const height = node.height * scale;
                const depth = width; // Profundidad = ancho para bloques
                
                const geometry = new THREE.BoxGeometry(width, height, depth);
                const material = new THREE.MeshLambertMaterial({ 
                    color: node.color || 0x3366cc,
                    transparent: true,
                    opacity: 0.8
                });
                
                const cube = new THREE.Mesh(geometry, material);
                
                // Posicionar el nodo
                cube.position.x = (node.x - 50) * scale * 0.15;
                cube.position.y = -node.y * scale * 0.05;
                cube.position.z = -node.z * scale;
                
                // Guardar referencia del nodo
                nodeObjects[node.id] = {
                    object: cube,
                    data: node
                };
                
                // Añadir etiqueta con el tipo de elemento
                const textDiv = document.createElement('div');
                textDiv.className = 'node-label';
                textDiv.textContent = node.tag;
                textDiv.style.color = 'white';
                textDiv.style.fontSize = '10px';
                
                const label = new THREE.CSS2DObject(textDiv);
                label.position.set(0, height/2 + 0.5, 0);
                cube.add(label);
                
                scene.add(cube);
            });
            
            // Crear líneas para enlaces
            links.forEach(link => {
                if (nodeObjects[link.source] && nodeObjects[link.target]) {
                    const sourceObj = nodeObjects[link.source].object;
                    const targetObj = nodeObjects[link.target].object;
                    
                    const sourcePosition = new THREE.Vector3().copy(sourceObj.position);
                    const targetPosition = new THREE.Vector3().copy(targetObj.position);
                    
                    const points = [sourcePosition, targetPosition];
                    const geometry = new THREE.BufferGeometry().setFromPoints(points);
                    
                    const material = new THREE.LineBasicMaterial({ 
                        color: 0x888888,
                        transparent: true,
                        opacity: 0.6
                    });
                    
                    const line = new THREE.Line(geometry, material);
                    scene.add(line);
                }
            });
            
            // Función de animación
            function animate() {
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }
            
            // Iniciar animación
            animate();
            
            // Añadir manejo de redimensionamiento
            window.addEventListener('resize', () => {
                const width = container.clientWidth;
                camera.aspect = width / height;
                camera.updateProjectionMatrix();
                renderer.setSize(width, height);
            });
            
            return {
                scene: scene,
                camera: camera,
                renderer: renderer,
                controls: controls,
                nodeObjects: nodeObjects
            };
        }
        """


if __name__ == "__main__":
    # Este código solo se ejecuta si se ejecuta este archivo directamente
    visualizer = DOM3DVisualizer()
    with open("example.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    visualization_data = visualizer.generate_3d_visualization_data(html_content)
    print(f"Generados {len(visualization_data['nodes'])} nodos y {len(visualization_data['links'])} enlaces")