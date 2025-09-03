import face_recognition
import io
import json
import numpy as np

class FaceRecognitionService:
    def __init__(self, threshold=0.6):
        self.threshold = threshold
    
    def extract_face_encoding(self, image_bytes):
        """Extrae el encoding facial de una imagen"""
        imagen = face_recognition.load_image_file(io.BytesIO(image_bytes))
        encodings = face_recognition.face_encodings(imagen)
        if len(encodings) == 0:
            raise ValueError("No se detectó rostro en la imagen")
        return encodings[0].tolist()
    
    def compare_faces(self, face_encoding, stored_encodings):
        """Compara un encoding facial con encodings almacenados"""
        face_array = np.array(face_encoding)
        mejor_empleado = None
        mejor_confianza = self.threshold
        
        for empleado in stored_encodings:
            encoding_guardado = np.array(json.loads(empleado.DatosBiometricos))
            distancia = np.linalg.norm(face_array - encoding_guardado)
            if distancia < mejor_confianza:
                mejor_confianza = distancia
                mejor_empleado = empleado
        
        if mejor_empleado is not None:
            return mejor_empleado, float(1 - mejor_confianza)  # Convertir a float de Python
        return None, None
