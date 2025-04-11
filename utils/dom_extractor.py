
"""Tony Mateo 23-EISN-2-044"""
"""
Utilidad para extraer información del DOM de una página web,
enfocado en extraer datos de accesibilidad como textos alternativos.
"""

from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Tuple, Optional
import re

# Configurar logging """Tony Mateo 23-EISN-2-044"""
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DOMExtractor:
    """
    Clase para extraer información relevante de accesibilidad del DOM de una página web. Tony Mateo 23-EISN-2-044
    """
    
    def __init__(self):
        """Inicializa el extractor de DOM."""
        logging.info("Inicializando DOMExtractor")
    
    def extract_images_info(self, html_content: str) -> List[Dict]:
        """
        Extrae información sobre imágenes del DOM, incluyendo textos alternativos.
        
        Args:
            html_content (str): Contenido HTML de la página
            
        Returns:
            List[Dict]: Lista de imágenes con sus atributos
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Encontrar todas las imágenes Tony Mateo 23-EISN-2-044
            images = []
            for img in soup.find_all('img'):
                # Extraer información básica
                image_info = {
                    'element': 'img',
                    'src': img.get('src', ''),
                    'alt': img.get('alt', ''),
                    'has_alt': 'alt' in img.attrs,
                    'empty_alt': 'alt' in img.attrs and not img['alt'].strip(),
                    'width': img.get('width', ''),
                    'height': img.get('height', ''),
                }
                
                # Intentar extraer dimensiones de style si están presentes Tony Mateo 23-EISN-2-044
                style = img.get('style', '')
                if style:
                    width_match = re.search(r'width:\s*(\d+)', style)
                    if width_match and not image_info['width']:
                        image_info['width'] = width_match.group(1)
                    
                    height_match = re.search(r'height:\s*(\d+)', style)
                    if height_match and not image_info['height']:
                        image_info['height'] = height_match.group(1)
                
                # Extraer aria-label si existe
                image_info['aria_label'] = img.get('aria-label', '')
                
                # Verificar si está dentro de un figure con figcaption
                parent_figure = img.find_parent('figure')
                if parent_figure and parent_figure.find('figcaption'):
                    image_info['figcaption'] = parent_figure.find('figcaption').get_text(strip=True)
                else:
                    image_info['figcaption'] = ''
                
                # Añadir a la lista
                images.append(image_info)
            
            # También buscar divs con imágenes de fondo Tony Mateo 23-EISN-2-044 
            background_images = []
            for element in soup.find_all(['div', 'span', 'section', 'header', 'footer']):
                style = element.get('style', '')
                if 'background-image' in style:
                    # Extraer URL de la imagen
                    bg_url_match = re.search(r'background-image:\s*url\([\'"]?([^\)]+)[\'"]?\)', style)
                    if bg_url_match:
                        bg_info = {
                            'element': element.name,
                            'src': bg_url_match.group(1),
                            'alt': '',  # Las imágenes de fondo no tienen alt
                            'has_alt': False,
                            'empty_alt': False,
                            'is_background': True,
                            'aria_label': element.get('aria-label', ''),
                            'inner_text': element.get_text(strip=True)
                        }
                        background_images.append(bg_info)
            
            # Combinar resultados Tony Mateo 23-EISN-2-044
            all_images = images + background_images
            logging.info(f"Extraídas {len(all_images)} imágenes del DOM")
            
            return all_images
            
        except Exception as e:
            logging.error(f"Error al extraer imágenes del DOM: {e}")
            return []
    
    def match_image_with_dom(self, image_region: Tuple[int, int, int, int], 
                           dom_images: List[Dict], 
                           viewport_width: int, 
                           viewport_height: int) -> Optional[Dict]:
        """
        Intenta emparejar una región de imagen detectada con un elemento del DOM.
        
        Args:
            image_region (tuple): Región de la imagen (x, y, width, height)
            dom_images (List[Dict]): Lista de imágenes extraídas del DOM
            viewport_width (int): Ancho de la ventana
            viewport_height (int): Alto de la ventana
            
        Returns:
            Optional[Dict]: Información del DOM emparejada o None
        """
        # Esta es una implementación simplificada
        # En una implementación real, utilizaríamos información de posición del DOM Tony Mateo 23-EISN-2-044
        
        # Por ahora, simplemente devolvemos la primera imagen que no tenga alt Tony Mateo 23-EISN-2-044
        for img in dom_images:
            if not img.get('has_alt', False) or img.get('empty_alt', False):
                return img
        
        return None
    
    def extract_interactive_elements(self, html_content: str) -> List[Dict]:
        """
        Extrae elementos interactivos como botones y enlaces.
        
        Args:
            html_content (str): Contenido HTML de la página
            
        Returns:
            List[Dict]: Lista de elementos interactivos
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            interactive_elements = []
            
            # Buscar enlaces Tony Mateo 23-EISN-2-044
            for link in soup.find_all('a'):
                element = {
                    'element': 'a',
                    'text': link.get_text(strip=True),
                    'href': link.get('href', ''),
                    'has_aria_label': 'aria-label' in link.attrs,
                    'aria_label': link.get('aria-label', ''),
                    'title': link.get('title', ''),
                    'role': link.get('role', ''),
                }
                interactive_elements.append(element)
            
            # Buscar botones Tony Mateo 23-EISN-2-044
            for button in soup.find_all(['button', 'input']):
                if button.name == 'input' and button.get('type') not in ['button', 'submit', 'reset', 'image']:
                    continue
                
                element = {
                    'element': button.name,
                    'text': button.get_text(strip=True) if button.name == 'button' else '',
                    'type': button.get('type', ''),
                    'has_aria_label': 'aria-label' in button.attrs,
                    'aria_label': button.get('aria-label', ''),
                    'title': button.get('title', ''),
                    'value': button.get('value', ''),
                }
                interactive_elements.append(element)
            
            logging.info(f"Extraídos {len(interactive_elements)} elementos interactivos del DOM")
            return interactive_elements
            
        except Exception as e:
            logging.error(f"Error al extraer elementos interactivos: {e}")
            return []


if __name__ == "__main__":
    # Este código solo se ejecuta si se ejecuta este archivo directamente Tony Mateo 23-EISN-2-044
    extractor = DOMExtractor()
    with open("example.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    images = extractor.extract_images_info(html_content)
    print(f"Imágenes extraídas: {len(images)}")