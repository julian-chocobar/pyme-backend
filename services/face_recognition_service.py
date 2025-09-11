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
        from utils.crypto_utils import VectorEncryption  # Importar aquí para evitar importación circular
        
        face_array = np.array(face_encoding)
        mejor_empleado = None
        mejor_confianza = self.threshold
        
        crypto = VectorEncryption()
        
        for empleado in stored_encodings:
            # Skip employees without biometric data
            if not empleado.vector_cifrado or not empleado.iv:
                continue
                
            try:
                # Convert IV to bytes if it's a string
                iv = empleado.iv
                if isinstance(iv, str):
                    if iv.startswith('b\'') and iv.endswith('\''):
                        # Handle string representation of bytes
                        iv = iv[2:-1].encode('latin-1')
                    else:
                        # Handle base64 encoded string
                        import base64
                        iv = base64.b64decode(iv)
                
                # Decrypt the stored face encoding
                decrypted_data = crypto.decrypt_vector(
                    empleado.vector_cifrado,
                    iv
                )
                
                # If decrypted_data is already a list, use it directly
                if isinstance(decrypted_data, list):
                    encoding_guardado = np.array(decrypted_data)
                else:
                    # Otherwise, try to parse it as JSON
                    if isinstance(decrypted_data, bytes):
                        decrypted_data = decrypted_data.decode('utf-8')
                    encoding_guardado = np.array(json.loads(decrypted_data))
                
                # Calculate distance between face encodings
                distancia = np.linalg.norm(face_array - encoding_guardado)
                
                if distancia < mejor_confianza:
                    mejor_confianza = distancia
                    mejor_empleado = empleado
                    
            except Exception as e:
                # Log the error with more details
                import traceback
                print(f"Error procesando datos biométricos del empleado {getattr(empleado, 'EmpleadoID', 'unknown')}:")
                print(f"IV type: {type(getattr(empleado, 'iv', None))}")
                print(f"IV value: {getattr(empleado, 'iv', None)}")
                print(f"Error: {str(e)}")
                print(traceback.format_exc())
                continue
        
        if mejor_empleado is not None:
            return mejor_empleado, float(1 - mejor_confianza)  # Convertir a float de Python
            
        return None, None
