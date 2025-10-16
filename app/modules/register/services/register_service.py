"""
Servicio para el registro de usuarios
"""
from sqlalchemy.orm import Session
from datetime import datetime
from app.modules.auth.models.user import User
from app.modules.auth.models.credentials import Credentials
from app.modules.auth.models.user_role import UserRole
from app.modules.register.schemas.create_user_dto import CreateUserDto
from app.core.security import get_password_hash
from typing import List

class RegisterService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, data: CreateUserDto) -> dict:
        """Crear un nuevo usuario"""
        print("🔍 REGISTER_SERVICE: Iniciando creación de usuario")
        
        # Verificar si el email ya existe en credentials
        print("🔍 REGISTER_SERVICE: Verificando email existente")
        try:
            existing_credentials = self.db.query(Credentials).filter(Credentials.email == data.email).first()
            print(f"🔍 REGISTER_SERVICE: Consulta de email ejecutada, resultado: {existing_credentials}")
        except Exception as e:
            print(f"❌ REGISTER_SERVICE: Error al consultar credentials: {e}")
            raise e
        
        if existing_credentials:
            print("❌ REGISTER_SERVICE: Email ya existe")
            raise ValueError("El email ya está registrado")
        
        # Verificar si la identificación ya existe
        print("🔍 REGISTER_SERVICE: Verificando username existente")
        existing_id = self.db.query(User).filter(User.username == data.username).first()
        if existing_id:
            print("❌ REGISTER_SERVICE: Username ya existe")
            raise ValueError("El username ya está registrado")
        
        # Crear nuevo usuario
        print("🔍 REGISTER_SERVICE: Creando nuevo usuario")
        new_user = User(
            firstName=data.firstName,
            lastName=data.lastName,
            username=data.username,
            phone=data.phone,
            id_status=True
        )
        
        print("🔍 REGISTER_SERVICE: Agregando usuario a la sesión")
        self.db.add(new_user)
        print("🔍 REGISTER_SERVICE: Haciendo commit del usuario")
        self.db.commit()
        print("🔍 REGISTER_SERVICE: Refrescando usuario")
        self.db.refresh(new_user)
        print(f"✅ REGISTER_SERVICE: Usuario creado con ID: {new_user.id_user}")
        
        # Crear credenciales con la contraseña hasheada
        print("🔍 REGISTER_SERVICE: Creando credenciales")
        hashed_password = get_password_hash(data.password)
        new_credentials = Credentials(
            id_user=new_user.id_user,
            email=data.email,
            password=hashed_password
        )
        
        print("🔍 REGISTER_SERVICE: Agregando credenciales a la sesión")
        self.db.add(new_credentials)
        
        # Crear la relación user_role
        print(f"🔍 REGISTER_SERVICE: Creando user_role con id_role={data.id_role}")
        new_user_role = UserRole(
            id_user=new_user.id_user,
            id_role=data.id_role
        )
        
        print("🔍 REGISTER_SERVICE: Agregando user_role a la sesión")
        self.db.add(new_user_role)
        print("🔍 REGISTER_SERVICE: Haciendo commit final")
        self.db.commit()
        print("🔍 REGISTER_SERVICE: Refrescando objetos")
        self.db.refresh(new_credentials)
        self.db.refresh(new_user_role)
        
        print("✅ REGISTER_SERVICE: Usuario creado exitosamente")
        return {
            "message": "Usuario registrado exitosamente",
            "id": new_user.id_user,
            "firstName": new_user.firstName,
            "lastName": new_user.lastName
        }
