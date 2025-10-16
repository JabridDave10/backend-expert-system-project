from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")

# Para Render, usar DATABASE_URL si está disponible (recomendado)
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Fallback para desarrollo local
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def create_tables():
    """Crear todas las tablas en la base de datos"""
    from app.modules.auth.models.user import User
    from app.modules.auth.models.role import Role
    from app.modules.auth.models.user_role import UserRole
    from app.modules.auth.models.credentials import Credentials

    print("Creando tablas...")
    print(f"Tablas a crear: {list(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente")

def initialize_default_roles():
    """Inicializar roles por defecto (usuario y admin)"""
    from app.modules.auth.models.role import Role
    
    db = SessionLocal()
    try:
        # Verificar si ya existen los roles
        existing_roles = db.query(Role).all()
        existing_role_names = [role.name for role in existing_roles]
        
        # Definir roles por defecto
        default_roles = [
            {"name": "usuario", "description": "Rol de usuario estándar"},
            {"name": "admin", "description": "Rol de administrador del sistema"}
        ]
        
        # Crear roles que no existen
        for role_data in default_roles:
            if role_data["name"] not in existing_role_names:
                new_role = Role(
                    name=role_data["name"],
                    description=role_data["description"]
                )
                db.add(new_role)
                print(f"✅ Rol '{role_data['name']}' creado exitosamente")
            else:
                print(f"ℹ️  Rol '{role_data['name']}' ya existe")
        
        db.commit()
        print("✅ Inicialización de roles completada")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al inicializar roles: {e}")
        raise e
    finally:
        db.close()