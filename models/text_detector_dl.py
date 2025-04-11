"""
Detector de texto en imágenes basado en deep learning.

Este módulo utiliza EasyOCR (basado en PyTorch) para detectar texto en imágenes
y un modelo de Transformers para evaluar la calidad de textos alternativos.
"""

import torch
import numpy as np
import cv2
from PIL import Image
import easyocr
from transformers import DistilBertTokenizer, DistilBertModel
import logging
import os
import time
from typing import List, Dict, Tuple, Any, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class TextDetectorDL:
    """
    Clase para detectar texto en imágenes usando deep learning.
    Utiliza EasyOCR (PyTorch) para OCR y DistilBERT para evaluación de textos alternativos.
    """
    
    def __init__(self, use_gpu: bool = False):
        """
        Inicializa el detector de texto con modelos de deep learning.
        
        Args:
            use_gpu (bool): Si se debe usar GPU para inferencia (si está disponible)
        """
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = torch.device('cuda' if self.use_gpu else 'cpu')
        
        logging.info(f"Inicializando TextDetectorDL (usando {'GPU' if self.use_gpu else 'CPU'})")
        
        # Inicializar detector OCR (basado en CRNN - Convolutional Recurrent Neural Network) Tony Mateo 23-EISN-2-044"
        self._init_ocr()
        
        # Inicializar modelo de NLP para evaluación de texto alternativo Tony Mateo 23-EISN-2-044"
        self._init_nlp_model()
    
    def _init_ocr(self):
        """Inicializa el modelo OCR basado en deep learning (EasyOCR)"""
        try:
            # Crear un directorio temporal para los modelos si no existe Tony Mateo 23-EISN-2-044"
            os.makedirs('./models_cache', exist_ok=True)
            
            start_time = time.time()
            logging.info("Cargando modelo OCR (EasyOCR)... Esto puede tardar unos segundos")
            
            # EasyOCR usa PyTorch internamente para sus modelos de detección y reconocimiento Tony Mateo 23-EISN-2-044"
            self.reader = easyocr.Reader(['es', 'en'], gpu=self.use_gpu, model_storage_directory='./models_cache')
            
            elapsed = time.time() - start_time
            logging.info(f"Modelo OCR cargado en {elapsed:.2f} segundos")
        except Exception as e:
            logging.error(f"Error al inicializar el modelo OCR: {e}")
            raise
    
    def _init_nlp_model(self):
        """Inicializa el modelo de NLP para evaluación de texto alternativo"""
        try:
            start_time = time.time()
            logging.info("Cargando modelo NLP (DistilBERT)...")
            
            # Cargar el modelo DistilBERT preentrenado Tony Mateo 23-EISN-2-044"
            self.tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
            self.nlp_model = DistilBertModel.from_pretrained('distilbert-base-uncased')
            
            # Mover el modelo a GPU si está disponible Tony Mateo 23-EISN-2-044"
            self.nlp_model = self.nlp_model.to(self.device)
            self.nlp_model.eval()  # Establecer en modo evaluación Tony Mateo 23-EISN-2-044"
            
            elapsed = time.time() - start_time
            logging.info(f"Modelo NLP cargado en {elapsed:.2f} segundos")
        except Exception as e:
            logging.error(f"Error al inicializar el modelo NLP: {e}")
            raise
    
    def detect_text_in_image(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        Detecta texto en una imagen usando deep learning.
        
        Args:
            image (PIL.Image): Imagen a analizar
            
        Returns:
            List[Dict]: Lista de detecciones con coordenadas, texto y confianza
        """
        try:
            # Convertir PIL Image a numpy array para EasyOCR Tony Mateo 23-EISN-2-044"
            img_array = np.array(image)
            
            # Detectar texto en la imagen usando el modelo CRNN de EasyOCR
            # Este paso utiliza:
            # 1. Una CNN para extraer características de la imagen
            # 2. Una red CRAFT para detección de regiones de texto
            # 3. Una CRNN (CNN + RNN) para reconocimiento de caracteres Tony Mateo 23-EISN-2-044"
            raw_results = self.reader.readtext(img_array)
            
            # Procesar y formatear resultados Tony Mateo 23-EISN-2-044"
            detections = []
            for bbox, text, confidence in raw_results:
                # bbox es [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] Tony Mateo 23-EISN-2-044"
                # Convertir a formato (x, y, w, h) Tony Mateo 23-EISN-2-044"
                x_min = min(point[0] for point in bbox)
                y_min = min(point[1] for point in bbox)
                x_max = max(point[0] for point in bbox)
                y_max = max(point[1] for point in bbox)
                width = x_max - x_min
                height = y_max - y_min
                
                # Solo incluir detecciones con confianza razonable y texto no vacío Tony Mateo 23-EISN-2-044"
                if confidence > 0.2 and text.strip():
                    detections.append({
                        'region': (int(x_min), int(y_min), int(width), int(height)),
                        'detected_text': text,
                        'confidence': confidence,
                        'has_alt_text': False,  # Por defecto, asumimos que no tiene alt text 
                    })
            
            logging.info(f"Detectados {len(detections)} textos en la imagen")
            return detections
            
        except Exception as e:
            logging.error(f"Error en la detección de texto: {e}")
            return []
    
    def get_text_embedding(self, text: str) -> np.ndarray:
        """
        Obtiene embedding vectorial de un texto usando DistilBERT.
        
        Args:
            text (str): Texto a procesar
            
        Returns:
            np.ndarray: Vector de embedding
        """
        try:
            # Tokenizar texto Tony Mateo 23-EISN-2-044"
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Obtener embeddings con el modelo preentrenado Tony Mateo 23-EISN-2-044"
            with torch.no_grad():  # No calcular gradientes para inferencia 
                outputs = self.nlp_model(**inputs)
            
            # Usar el embedding del token [CLS] como representación del texto completo Tony Mateo 23-EISN-2-044"
            embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            return embedding
            
        except Exception as e:
            logging.error(f"Error al obtener embedding: {e}")
            return np.zeros((1, self.nlp_model.config.hidden_size))
    
    def evaluate_alt_text(self, detected_text: str, alt_text: Optional[str]) -> Dict[str, Any]:
        """
        Evalúa la calidad del texto alternativo comparado con el texto detectado.
        
        Args:
            detected_text (str): Texto detectado en la imagen
            alt_text (str, optional): Texto alternativo a evaluar
            
        Returns:
            Dict: Resultados de la evaluación
        """
        # Si no hay texto alternativo Tony Mateo 23-EISN-2-044"
        if not alt_text or not alt_text.strip():
            return {
                'has_alt_text': False,
                'similarity_score': 0.0,
                'quality': 'Missing',
                'recommendation': 'Añadir texto alternativo que describa el contenido textual de la imagen'
            }
        
        # Si el texto detectado está vacío (posible error de detección) Tony Mateo 23-EISN-2-044"
        if not detected_text or not detected_text.strip():
            return {
                'has_alt_text': True,
                'similarity_score': 1.0,  # Asumimos que está bien
                'quality': 'Good',
                'recommendation': 'El texto alternativo parece adecuado'
            }
        
        # Calcular embeddings Tony Mateo 23-EISN-2-044"
        detected_embedding = self.get_text_embedding(detected_text)
        alt_embedding = self.get_text_embedding(alt_text)
        
        # Calcular similitud de coseno entre los embeddings Tony Mateo 23-EISN-2-044"
        similarity = np.dot(detected_embedding, alt_embedding.T) / (
            np.linalg.norm(detected_embedding) * np.linalg.norm(alt_embedding)
        )
        similarity_score = float(similarity[0][0])
        
        # Evaluar calidad basada en la similitud Tony Mateo 23-EISN-2-044"
        if similarity_score < 0.3:
            quality = 'Poor'
            recommendation = 'El texto alternativo no describe adecuadamente el contenido textual de la imagen'
        elif similarity_score < 0.6:
            quality = 'Average'
            recommendation = 'El texto alternativo describe parcialmente el contenido. Considera mejorarlo'
        else:
            quality = 'Good'
            recommendation = 'El texto alternativo describe adecuadamente el contenido'
        
        return {
            'has_alt_text': True,
            'similarity_score': similarity_score,
            'quality': quality,
            'recommendation': recommendation
        }
    
    def analyze_image_with_alt(self, image: Image.Image, alt_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Analiza una imagen para detectar texto y evalúa su texto alternativo.
        
        Args:
            image (PIL.Image): Imagen a analizar
            alt_text (str, optional): Texto alternativo de la imagen
            
        Returns:
            List[Dict]: Resultados del análisis
        """
        # Detectar texto en la imagen Tony Mateo 23-EISN-2-044"
        detections = self.detect_text_in_image(image)
        
        # Si hay detecciones y un texto alternativo, evaluar Tony Mateo 23-EISN-2-044"
        if detections and alt_text:
            # Combinar todos los textos detectados Tony Mateo 23-EISN-2-044"
            all_detected_text = ' '.join(d['detected_text'] for d in detections)
            
            # Evaluar el texto alternativo Tony Mateo 23-EISN-2-044"
            evaluation = self.evaluate_alt_text(all_detected_text, alt_text)
            
            # Actualizar todas las detecciones con el resultado de la evaluación Tony Mateo 23-EISN-2-044"
            for detection in detections:
                detection.update({
                    'has_alt_text': evaluation['has_alt_text'],
                    'alt_text_quality': evaluation['quality'],
                    'alt_text': alt_text,
                    'recommendation': evaluation['recommendation']
                })
        
        return detections


if __name__ == "__main__":
    # Este código solo se ejecuta si se ejecuta este archivo directamente
    detector = TextDetectorDL()
    img = Image.open("example.jpeg")
    results = detector.detect_text_in_image(img)
    print(f"Textos detectados: {results}")