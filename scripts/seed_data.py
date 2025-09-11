import os
import random
import base64
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Local imports
from database.connection import SessionLocal 
from models.database import Empleado, RolEnum, EstadoEmpleadoEnum, Acceso, TipoAccesoEnum, MetodoAccesoEnum, Area
from utils.crypto_utils import VectorEncryption

def cargar_areas_ejemplo():
    session = SessionLocal()
    try:
        # Crear áreas de ejemplo basadas en la imagen
        areas = [
            Area(
                AreaID="AREA001",
                Nombre="Preparacion",
                Descripcion="Control de materia prima entrante",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA002",
                Nombre="Procesamiento",
                Descripcion="Procesamiento inicial de alimentos",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA003",
                Nombre="Elaboración",
                Descripcion="Elaboración de productos terminados",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA004",
                Nombre="Envasado",
                Descripcion="Envasado y empaquetado final",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA005",
                Nombre="Etiquetado",
                Descripcion="Etiquetado",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA006",
                Nombre="Control Calidad",
                Descripcion="Control de calidad y laboratorio",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA007",
                Nombre="Administración",
                Descripcion="Área administrativa y gerencia",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA008",
                Nombre="Comun",
                Descripcion="Espacios comunes",
                Estado="Activo"
            ),
            Area(
                AreaID="AREA009",
                Nombre="Logistica",
                Descripcion="Gestion de almacenamiento y distribucion de insumos y productos terminados",
                Estado="Activo"
            )
        ]
        
        # Insertar áreas si no existen
        for area in areas:
            existe = session.query(Area).filter_by(AreaID=area.AreaID).first()
            if not existe:
                session.add(area)
        session.commit()
        print("Áreas de ejemplo cargadas correctamente.")
    except Exception as e:
        print("Error cargando áreas:", e)
        session.rollback()
    finally:
        session.close()

def generate_realistic_vectors(num_vectors: int, dimensions: int = 128) -> List[List[float]]:
    """Generate realistic facial vectors with some patterns."""
    # Create some clusters to simulate family resemblances
    clusters = 15
    cluster_centers = [np.random.normal(0, 0.5, dimensions) for _ in range(clusters)]
    
    vectors = []
    for _ in range(num_vectors):
        # Choose a random cluster
        center = random.choice(cluster_centers)
        # Add some noise to create variation
        vector = center + np.random.normal(0, 0.1, dimensions)
        # Normalize to unit vector
        vector = vector / np.linalg.norm(vector)
        vectors.append(vector.tolist())
    
    return vectors

def generate_employee_data(num_employees: int = 200) -> List[Dict]:
    """Generate realistic employee data with distribution across areas."""
    fake = Faker('es_ES')
    Faker.seed(42)  # For reproducibility
    
    # Area distribution (area_id: percentage of employees)
    area_distribution = {
        "AREA001": 0.12,  # Preparacion
        "AREA002": 0.15,  # Procesamiento
        "AREA003": 0.18,  # Elaboración
        "AREA004": 0.14,  # Envasado
        "AREA005": 0.08,  # Etiquetado
        "AREA006": 0.10,  # Control Calidad
        "AREA007": 0.13,  # Administración
        "AREA008": 0.05,  # Comun
        "AREA009": 0.05   # Logistica
    }
    
    # Generate area assignments
    areas = list(area_distribution.keys())
    probs = list(area_distribution.values())
    area_assignments = np.random.choice(areas, size=num_employees, p=probs)
    
    # Generate role distribution (more operarios than supervisors)
    roles = [RolEnum.Operario] * 8 + [RolEnum.Supervisor] * 2
    
    # Generate employee data
    employees = []
    used_dnis = set()
    
    for i in range(num_employees):
        # Generate unique DNI
        while True:
            dni = str(random.randint(20000000, 50000000))
            if dni not in used_dnis:
                used_dnis.add(dni)
                break
        
        # Generate name and email
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@empresa.com"
        
        # Random date of birth (18-65 years old)
        birth_date = fake.date_of_birth(minimum_age=18, maximum_age=65)
        
        # Create employee data
        employee = {
            'Nombre': first_name,
            'Apellido': last_name,
            'DNI': dni,
            'Email': email,
            'FechaNacimiento': birth_date.isoformat(),
            'Rol': random.choice(roles),
            'EstadoEmpleado': random.choices(
                [EstadoEmpleadoEnum.Activo, EstadoEmpleadoEnum.Inactivo],
                weights=[0.9, 0.1]  # 90% active, 10% inactive
            )[0],
            'AreaID': area_assignments[i],
            'PIN': str(random.randint(1000, 9999)),
            'estado': 'activo' if random.random() < 0.9 else 'inactivo',
            'FechaRegistro': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
        }
        employees.append(employee)
    
    return employees

def cargar_empleados_iniciales():
    """Load initial employees with encrypted facial vectors."""
    # Debug: Print environment variables
    print("\nDebug - Environment Variables:")
    print(f"VECTOR_ENCRYPTION_KEY exists: {'VECTOR_ENCRYPTION_KEY' in os.environ}")
    if 'VECTOR_ENCRYPTION_KEY' in os.environ:
        key = os.environ['VECTOR_ENCRYPTION_KEY']
        print(f"Key length: {len(key)} bytes")
        print(f"Key type: {type(key)}")
        print(f"Key value (first 10 chars): {key[:10]}...")
    
    session = SessionLocal()
    try:
        # Check if employees already exist
        if session.query(Empleado).count() > 0:
            print("Employees already exist in the database. Skipping employee creation.")
            return

        print("\nGenerating employee data...")
        employees_data = generate_employee_data(200)  # Generate 200 employees

        # Initialize encryption
        print("\nInitializing encryption...")
        print(f"Environment VECTOR_ENCRYPTION_KEY: {os.getenv('VECTOR_ENCRYPTION_KEY')}")
        crypto = VectorEncryption()
        
        # Generate realistic facial vectors
        print("Generating facial vectors...")
        vectors = generate_realistic_vectors(len(employees_data))
        
        print("Encrypting vectors and creating employee records...")
        for i, (emp_data, vector) in enumerate(zip(employees_data, vectors)):
            # Encrypt the facial vector
            encrypted_data, iv = crypto.encrypt_vector(vector)
            
            # Convert binary data to base64 for storage in Text field
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            iv_b64 = base64.b64encode(iv).decode('utf-8')
            
            # Create employee with encrypted vector
            employee = Empleado(
                **{k: v for k, v in emp_data.items() if k != 'estado'},
                vector_cifrado=encrypted_b64,
                iv=iv_b64,
                estado=emp_data['estado']
            )
            
            session.add(employee)
            
            # Commit in batches of 50
            if i % 50 == 0 and i > 0:
                session.commit()
                print(f"Processed {i} employees...")
        
        session.commit()
        print(f"Successfully created {len(employees_data)} employees with encrypted facial vectors.")
        
    except Exception as e:
        session.rollback()
        print(f"Error creating employees: {str(e)}")
        raise
    finally:
        session.close()

def cargar_accesos_ejemplo():
    """Generate realistic access logs for employees."""
    session = SessionLocal()
    crypto = VectorEncryption()
    
    try:
        # Check if we already have access logs
        existing_logs = session.query(Acceso).count()
        if existing_logs > 0:
            print(f"Already have {existing_logs} access logs. Skipping access log creation.")
            return
        
        print("Generating access logs...")
        # Get all active employees
        empleados = session.query(Empleado).filter(Empleado.estado == 'activo').all()
        
        if not empleados:
            print("No active employees found. Please run employee creation first.")
            return
        
        # Create only 10 access records in total
        total_logs = 10
        
        for _ in range(total_logs):
            # Select a random employee for each log
            empleado = random.choice(empleados)
            # Random date in the last 90 days
            fecha_hora = datetime.now() - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # 95% chance of successful access for active employees
            acceso_permitido = random.choices(
                ["Permitido", "Denegado"],
                weights=[0.95, 0.05]
            )[0]
            
            # For denied access, 50% chance it's because of wrong area
            if acceso_permitido == "Denegado" and random.random() < 0.5:
                # Get a random area that's not the employee's area
                areas = session.query(Area.AreaID).filter(Area.AreaID != empleado.AreaID).all()
                if areas:
                    area_id = random.choice(areas)[0]
                else:
                    area_id = empleado.AreaID
            else:
                area_id = empleado.AreaID
            
            # Create access log
            acceso = Acceso(
                EmpleadoID=empleado.EmpleadoID if acceso_permitido == "Permitido" else None,
                AreaID=area_id,
                FechaHora=fecha_hora.isoformat(),
                TipoAcceso=random.choice(list(TipoAccesoEnum)),
                MetodoAcceso=random.choice(list(MetodoAccesoEnum)),
                DispositivoAcceso=f"Dispositivo-{random.randint(1, 10)}",
                ConfianzaReconocimiento=random.uniform(0.7, 1.0) if acceso_permitido == "Permitido" else random.uniform(0.1, 0.6),
                AccesoPermitido=acceso_permitido
            )
            session.add(acceso)
            
            # Occasionally commit to avoid large transactions
            if random.random() < 0.1:  # 10% chance to commit
                session.commit()
    
        session.commit()
        print("Successfully generated 10 access logs.")
        
    except Exception as e:
        session.rollback()
        print(f"Error generating access logs: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    import time
    start_time = time.time()
    
    try:
        # Ensure required environment variable is set
        if not os.getenv("VECTOR_ENCRYPTION_KEY"):
            print("ERROR: VECTOR_ENCRYPTION_KEY environment variable is not set.")
            print(f"Generate a key by running: python -c 'from utils.crypto_utils import VectorEncryption; print(\"VECTOR_ENCRYPTION_KEY=\" + VectorEncryption.generate_key())'")
            exit(1)
        
        print("Starting data generation...")
        cargar_areas_ejemplo()
        cargar_empleados_iniciales()
        cargar_accesos_ejemplo()
        
        elapsed = time.time() - start_time
        print(f"\nData generation completed in {elapsed:.2f} seconds.")
        print("Datos de ejemplo cargados exitosamente.")
        
    except Exception as e:
        print(f"\nError during data generation: {str(e)}")
        raise
