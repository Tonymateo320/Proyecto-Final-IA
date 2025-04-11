"""
Simulador de daltonismo basado en deep learning.

Este módulo implementa simulaciones de diferentes tipos de daltonismo usando
transformaciones matriciales y modelos de PyTorch para procesar imágenes.
"""

import torch
import numpy as np
from PIL import Image
import cv2
import logging
from typing import Optional, List, Dict, Any, Tuple

# Configurar logging Tony Mateo 23-EISN-2-044
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class ColorBlindSimulator:
    """
    Clase que implementa simulaciones de daltonismo utilizando PyTorch.
    """
    
    def __init__(self, use_gpu: bool = False):
        """
        Inicializa el simulador de daltonismo.
        
        Args:
            use_gpu (bool): Si se debe usar GPU para el procesamiento (si está disponible)
        """
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = torch.device('cuda' if self.use_gpu else 'cpu')
        
        logging.info(f"Inicializando ColorBlindSimulator (usando {'GPU' if self.use_gpu else 'CPU'})")
        
        # Definir matrices de transformación para diferentes tipos de daltonismo
        # Basado en los algoritmos de Brettel Tony Mateo 23-EISN-2-044
        
        # Protanopia (deficiencia en receptores de rojo - 1% de hombres) Tony Mateo 23-EISN-2-044
        self.protanopia_matrix = torch.tensor([
            [0.567, 0.433, 0.000],
            [0.558, 0.442, 0.000],
            [0.000, 0.242, 0.758]
        ], dtype=torch.float32, device=self.device)
        
        # Deuteranopia (deficiencia en receptores de verde - 6% de hombres) Tony Mateo 23-EISN-2-044
        self.deuteranopia_matrix = torch.tensor([
            [0.625, 0.375, 0.000],
            [0.700, 0.300, 0.000],
            [0.000, 0.300, 0.700]
        ], dtype=torch.float32, device=self.device)
        
        # Tritanopia (deficiencia en receptores de azul - muy raro, 0.01% de población) Tony Mateo 23-EISN-2-044
        self.tritanopia_matrix = torch.tensor([
            [0.950, 0.050, 0.000],
            [0.000, 0.433, 0.567],
            [0.000, 0.475, 0.525]
        ], dtype=torch.float32, device=self.device)
        
        # Acromatopsia visión completamente monocromática muy raro
        # Implementada como una matriz de conversión a escala de grises  Tony Mateo 23-EISN-2-044 
        self.achromatopsia_matrix = torch.tensor([
            [0.299, 0.587, 0.114],
            [0.299, 0.587, 0.114],
            [0.299, 0.587, 0.114]
        ], dtype=torch.float32, device=self.device)
    
    def simulate_colorblindness(self, image: Image.Image, colorblind_type: str) -> Image.Image:
        """
        Simula cómo vería la imagen una persona con el tipo especificado de daltonismo.
        
        Args:
            image (PIL.Image): Imagen a transformar
            colorblind_type (str): Tipo de daltonismo a simular
                ('protanopia', 'deuteranopia', 'tritanopia', 'achromatopsia')
                
        Returns:
            PIL.Image: Imagen transformada
        """
        # Convertir imagen PIL a tensor de PyTorch Tony Mateo 23-EISN-2-044
        img_array = np.array(image)
        img_tensor = torch.tensor(img_array, dtype=torch.float32, device=self.device)
        
        # Seleccionar matriz de transformación según el tipo de daltonismo Tony Mateo 23-EISN-2-044
        if colorblind_type == 'protanopia':
            transform_matrix = self.protanopia_matrix
        elif colorblind_type == 'deuteranopia':
            transform_matrix = self.deuteranopia_matrix
        elif colorblind_type == 'tritanopia':
            transform_matrix = self.tritanopia_matrix
        elif colorblind_type == 'achromatopsia':
            transform_matrix = self.achromatopsia_matrix
        else:
            logging.warning(f"Tipo de daltonismo no reconocido: {colorblind_type}, usando visión normal")
            return image
        
        # Obtener dimensiones de la imagen
        height, width, channels = img_array.shape
        
        # Asegurar que la imagen tiene 3 canales (RGB) Tony Mateo 23-EISN-2-044
        if channels != 3:
            logging.warning("La imagen no tiene 3 canales. Convirtiendo a RGB.")
            image = image.convert('RGB')
            img_array = np.array(image)
            img_tensor = torch.tensor(img_array, dtype=torch.float32, device=self.device)
            height, width, channels = img_array.shape
        
        # Reshapear el tensor para aplicar la transformación matricial Tony Mateo 23-EISN-2-044
        img_reshaped = img_tensor.reshape(-1, 3)
        
        # Aplicar transformación matricial
        transformed = torch.matmul(img_reshaped, transform_matrix.T)
        
        # Volver a la forma original
        transformed = transformed.reshape(height, width, 3)
        
        # Asegurar que los valores estén en el rango 0-255
        transformed = torch.clamp(transformed, 0, 255)
        
        # Convertir a numpy array y luego a imagen PIL
        transformed_array = transformed.cpu().numpy().astype(np.uint8)
        transformed_image = Image.fromarray(transformed_array)
        
        return transformed_image
    
    def get_all_simulations(self, image: Image.Image) -> Dict[str, Image.Image]:
        """
        Genera simulaciones para todos los tipos de daltonismo soportados.
        
        Args:
            image (PIL.Image): Imagen original
            
        Returns:
            Dict[str, PIL.Image]: Diccionario con simulaciones para cada tipo
        """
        simulations = {
            'original': image,
            'protanopia': self.simulate_colorblindness(image, 'protanopia'),
            'deuteranopia': self.simulate_colorblindness(image, 'deuteranopia'),
            'tritanopia': self.simulate_colorblindness(image, 'tritanopia'),
            'achromatopsia': self.simulate_colorblindness(image, 'achromatopsia')
        }
        
        return simulations
    
    def analyze_color_contrast_issues(self, 
                                     image: Image.Image, 
                                     colorblind_type: str) -> List[Dict[str, Any]]:
        """
        Identifica áreas con problemas potenciales de contraste para un tipo específico de daltonismo.
        
        Args:
            image (PIL.Image): Imagen a analizar
            colorblind_type (str): Tipo de daltonismo a considerar
            
        Returns:
            List[Dict]: Problemas potenciales con su ubicación e impacto
        """
        # Generar versión con daltonismo simulado Tony Mateo 23-EISN-2-044
        colorblind_image = self.simulate_colorblindness(image, colorblind_type)
        
        # Convertir ambas imágenes a Lab para comparación de contraste perceptual Tony Mateo 23-EISN-2-044
        img_original = np.array(image)
        img_colorblind = np.array(colorblind_image)
        
        # Convertir de BGR a Lab
        lab_original = cv2.cvtColor(img_original, cv2.COLOR_RGB2LAB)
        lab_colorblind = cv2.cvtColor(img_colorblind, cv2.COLOR_RGB2LAB)
        
        # Calcular diferencia de contraste
        diff = cv2.absdiff(lab_original, lab_colorblind)
        
        # La mayor diferencia estará en los canales a y b (color) Tony Mateo 23-EISN-2-044
        diff_color = diff[:,:,1:3]
        
        # Sumar diferencias y normalizar
        total_diff = np.sum(diff_color, axis=2)
        max_diff = np.max(total_diff)
        if max_diff > 0:  # Evitar división por cero
            norm_diff = (total_diff / max_diff * 255).astype(np.uint8)
        else:
            norm_diff = total_diff.astype(np.uint8)
        
        # Aplicar umbral para encontrar áreas con diferencias significativas Tony Mateo 23-EISN-2-044
        threshold = 50  # Umbral ajustable
        _, thresholded = cv2.threshold(norm_diff, threshold, 255, cv2.THRESH_BINARY)
        
        # Encontrar contornos de áreas problemáticas Tony Mateo 23-EISN-2-044
        contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrar por tamaño mínimo
        min_area = 100
        problem_areas = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calcular el valor promedio de diferencia en esta área Tony Mateo 23-EISN-2-044
                avg_diff = np.mean(total_diff[y:y+h, x:x+w])
                
                severity = "Alto" if avg_diff > 100 else "Medio" if avg_diff > 50 else "Bajo"
                
                problem_areas.append({
                    'region': (x, y, w, h),
                    'color_difference': float(avg_diff),
                    'severity': severity,
                    'colorblind_type': colorblind_type
                })
        
        return problem_areas

    def get_colorblind_info(self) -> Dict[str, Dict[str, str]]:
        """
        Proporciona información educativa sobre cada tipo de daltonismo.
        
        Returns:
            Dict: Información sobre cada tipo de daltonismo
        """
        return {
            'protanopia': {
                'name': 'Protanopia',
                'description': 'Deficiencia en los conos sensibles al rojo. Las personas con protanopia tienen dificultad para distinguir entre rojo y verde, y el rojo puede aparecer más oscuro.',
                'prevalence': 'Afecta aproximadamente al 1% de los hombres.',
                'impact': 'Dificultad con información codificada por color que usa rojo/verde, como enlaces visitados/no visitados, campos obligatorios en formularios, etc.'
            },
            'deuteranopia': {
                'name': 'Deuteranopia',
                'description': 'Deficiencia en los conos sensibles al verde. Similar a la protanopia, pero los verdes pueden aparecer más claros.',
                'prevalence': 'Es el tipo más común, afectando aproximadamente al 6% de los hombres.',
                'impact': 'Problemas con los mismos elementos que la protanopia, pero con diferente percepción.'
            },
            'tritanopia': {
                'name': 'Tritanopia',
                'description': 'Deficiencia en los conos sensibles al azul. Dificulta distinguir entre azul y amarillo.',
                'prevalence': 'Muy raro, afecta a menos del 0.01% de la población.',
                'impact': 'Problemas con elementos que usan contrastes azul/amarillo, como algunas paletas de gráficos.'
            },
            'achromatopsia': {
                'name': 'Acromatopsia',
                'description': 'Ausencia total de visión de color (visión monocromática). Todo se percibe en tonos de gris.',
                'prevalence': 'Extremadamente raro, afecta aproximadamente a 1 de cada 30,000 personas.',
                'impact': 'Cualquier información que dependa exclusivamente del color es inaccesible.'
            }
        }

# Ejemplo de uso
if __name__ == "__main__":
    # Este código solo se ejecuta si se ejecuta este archivo directamente Tony Mateo 23-EISN-2-044
    simulator = ColorBlindSimulator()
    img = Image.open("example.jpg")
    deuteranopia_img = simulator.simulate_colorblindness(img, 'deuteranopia')
    deuteranopia_img.save("deuteranopia_example.jpg")