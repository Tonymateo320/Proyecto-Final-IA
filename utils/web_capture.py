
"""
Módulo para capturar capturas de pantalla de páginas web completas
usando Selenium y guardarlas como imágenes.
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import os
from PIL import Image
import io
import logging
import numpy as np

# Configurar logging Tony Mateo 23-EISN-2-044
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

class WebCapture:
    """Clase para capturar screenshots de páginas web completas usando Selenium."""
    
    def __init__(self, timeout=30):
        """
        Inicializa el WebCapture configurando el driver de Chrome.
        
        Args:
            timeout (int): Tiempo máximo de espera para cargar páginas en segundos
        """
        logging.info("Inicializando WebCapture")
        self.timeout = timeout
        self.setup_driver()
    
    def setup_driver(self):
        """Configura el driver de Chrome con opciones headless."""
        try:
            # Configuración de Chrome en modo headless Tony Mateo 23-EISN-2-044
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Usar el ChromeDriver local
            chromedriver_path = "./chromedriver.exe"  
            service = Service(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Configurar timeout para cargas de página Tony Mateo 23-EISN-2-044
            self.driver.set_page_load_timeout(self.timeout)
            
            logging.info(f"Driver de Chrome inicializado correctamente usando driver local en {chromedriver_path}")
        except Exception as e:
            logging.error(f"Error al configurar el driver: {e}")
            raise
    
    def capture_screenshot(self, url, output_path=None):
        """
        Captura una screenshot de la vista inicial de la página web.
        
        Args:
            url (str): URL de la página web a capturar
            output_path (str, opcional): Ruta donde guardar la imagen
            
        Returns:
            PIL.Image: Objeto de imagen con la captura de pantalla
        """
        try:
            logging.info(f"Capturando screenshot inicial de {url}")
            self.driver.get(url)
            
            # Dar tiempo para que la página cargue Tony Mateo 23-EISN-2-044
            time.sleep(3)
            
            # Obtener dimensiones de la página visible Tony Mateo 23-EISN-2-044
            width = self.driver.execute_script("return window.innerWidth")
            height = self.driver.execute_script("return window.innerHeight")
            
            # Establecer tamaño de ventana Tony Mateo 23-EISN-2-044
            self.driver.set_window_size(width, height)
            
            # Tomar screenshot Tony Mateo 23-EISN-2-044
            screenshot = self.driver.get_screenshot_as_png()
            image = Image.open(io.BytesIO(screenshot))
            
            # Guardar imagen si se especificó una ruta Tony Mateo 23-EISN-2-044
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                image.save(output_path)
                logging.info(f"Screenshot inicial guardado en {output_path}")
                
            return image
            
        except Exception as e:
            logging.error(f"Error al capturar la página {url}: {e}")
            return None
            
    def capture_full_page_screenshot(self, url, output_path=None, max_scroll=None):
        """
        Captura una screenshot de la página web completa, incluyendo contenido
        que requiere scroll.
        
        Args:
            url (str): URL de la página web a capturar
            output_path (str, opcional): Ruta donde guardar la imagen
            max_scroll (int, opcional): Número máximo de scrolls a realizar
            
        Returns:
            PIL.Image: Objeto de imagen con la captura de pantalla completa
        """
        try:
            logging.info(f"Capturando screenshot de página completa de {url}")
            
            # Cargar la página
            self.driver.get(url)
            
            # Dar tiempo para que la página cargue inicialmente Tony Mateo 23-EISN-2-044
            time.sleep(3)
            
            # Obtener dimensiones iniciales Tony Mateo 23-EISN-2-044
            viewport_width = self.driver.execute_script("return window.innerWidth")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            total_height = self.driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
            
            logging.info(f"Dimensiones de la página - Ancho: {viewport_width}, Alto visible: {viewport_height}, Alto total: {total_height}")
            
            # Método 1: Intentar usar captura de página completa nativa si está disponible Tony Mateo 23-EISN-2-044
            try:
                logging.info("Intentando usar captura de página completa nativa...")
                self.driver.set_window_size(viewport_width, total_height)
                time.sleep(1)
                
                full_screenshot = self.driver.get_full_page_screenshot_as_png()
                full_image = Image.open(io.BytesIO(full_screenshot))
                
                logging.info("Captura de página completa nativa exitosa")
                
                # Guardar imagen si se especificó una ruta Tony Mateo 23-EISN-2-044
                if output_path:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    full_image.save(output_path)
                    logging.info(f"Screenshot completo guardado en {output_path}")
                
                return full_image
                
            except (AttributeError, WebDriverException) as e:
                logging.info(f"Captura nativa de página completa no disponible: {e}")
                logging.info("Usando método alternativo de scroll y captura...")
                
                # Método 2: Scroll y captura por secciones
                # Restablecer el tamaño de la ventana Tony Mateo 23-EISN-2-044
                self.driver.set_window_size(viewport_width, viewport_height)
                time.sleep(1)
                
                # Determinar cuántos scrolls necesitamos Tony Mateo 23-EISN-2-044
                scroll_steps = (total_height // viewport_height) + 1
                
                # Limitar el número de scrolls si se especifica Tony Mateo 23-EISN-2-044
                if max_scroll and scroll_steps > max_scroll:
                    scroll_steps = max_scroll
                    logging.info(f"Limitando a {max_scroll} scrolls")
                
                # Crear una lista para almacenar capturas de pantallaTony Mateo 23-EISN-2-044
                screenshots = []
                last_height = 0
                
                # Capturar cada sección Tony Mateo 23-EISN-2-044
                for i in range(scroll_steps):
                    # Hacer scroll a la posición Tony Mateo 23-EISN-2-044
                    scroll_to = i * viewport_height
                    self.driver.execute_script(f"window.scrollTo(0, {scroll_to});")
                    time.sleep(1)  
                    
                    # Verificar si hemos llegado al final Tony Mateo 23-EISN-2-044
                    current_height = self.driver.execute_script("return window.pageYOffset")
                    if current_height == last_height and i > 0:
                        logging.info("Se alcanzó el final de la página")
                        break
                    
                    last_height = current_height
                    
                    # Capturar screenshot de la sección actual Tony Mateo 23-EISN-2-044
                    screenshot = self.driver.get_screenshot_as_png()
                    img = Image.open(io.BytesIO(screenshot))
                    screenshots.append(img)
                    
                    logging.info(f"Capturada sección {i+1}/{scroll_steps} en posición Y: {current_height}")
                
                # Combinar todas las capturas en una sola imagen Tony Mateo 23-EISN-2-044
                if screenshots:
                    # Determinar el tamaño final de la imagen Tony Mateo 23-EISN-2-044
                    final_width = screenshots[0].width
                    final_height = min(total_height, viewport_height * len(screenshots))
                    
                    # Crear imagen combinada Tony Mateo 23-EISN-2-044
                    combined_image = Image.new('RGB', (final_width, final_height))
                    
                    # Pegar cada captura en la posición correspondiente Tony Mateo 23-EISN-2-044
                    for i, img in enumerate(screenshots):
                        y_offset = i * viewport_height
                        if y_offset < final_height:
                            # Recortar si excede el tamaño final
                            paste_height = min(img.height, final_height - y_offset)
                            region = img.crop((0, 0, img.width, paste_height))
                            combined_image.paste(region, (0, y_offset))
                    
                    # Guardar imagen combinada si se especificó una ruta Tony Mateo 23-EISN-2-044
                    if output_path:
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        combined_image.save(output_path)
                        logging.info(f"Screenshot completo combinado guardado en {output_path}")
                    
                    return combined_image
                else:
                    logging.error("No se capturaron secciones")
                    return None
        
        except TimeoutException:
            logging.error(f"Timeout al cargar la página {url}")
            return None
        except Exception as e:
            logging.error(f"Error al capturar la página completa {url}: {e}")
            return None
    
    def get_page_source(self, url):
        """
        Obtiene el código HTML de la página.
        
        Args:
            url (str): URL de la página web
            
        Returns:
            str: Código fuente HTML de la página o None si hay error
        """
        try:
            self.driver.get(url)
            time.sleep(2)  # Esperar a que la página cargue
            
            # Scroll hasta el final para asegurar que se cargue todo el contenido
            # Útil para páginas con carga lazy Tony Mateo 23-EISN-2-044
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")  # Volver arriba
            
            return self.driver.page_source
        except Exception as e:
            logging.error(f"Error al obtener el código fuente de {url}: {e}")
            return None
    
    def close(self):
        """Cierra el driver y libera recursos."""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logging.info("Driver cerrado correctamente")


if __name__ == "__main__":
    # Este código solo se ejecuta si se ejecuta este archivo directamente Tony Mateo 23-EISN-2-044
    web_capture = WebCapture()
    img = web_capture.capture_full_page_screenshot("https://www.example.com", "example_full.png")
    web_capture.close()
    
    if img:
        print(f"Captura completa guardada. Dimensiones: {img.width}x{img.height}")