"""
Migration Script - Crear tabla Games

Este script crea la tabla 'games' en la base de datos para almacenar
el catálogo completo de juegos.
"""

import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from sqlalchemy import create_engine, inspect
from app.core.database import DATABASE_URL, Base
from app.modules.expert_system.models.game import Game

def main():
    print("=" * 70)
    print("MIGRACIÓN: Crear Tabla Games")
    print("=" * 70)

    # Crear engine
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    # Verificar si la tabla ya existe
    existing_tables = inspector.get_table_names()

    if "games" in existing_tables:
        print("\n⚠️  La tabla 'games' ya existe.")
        response = input("¿Deseas recrearla? (se perderán todos los datos) [y/N]: ")

        if response.lower() != 'y':
            print("❌ Migración cancelada")
            return

        print("\n🗑️  Eliminando tabla 'games'...")
        Game.__table__.drop(engine)
        print("✅ Tabla eliminada")

    # Crear tabla
    print("\n📋 Creando tabla 'games'...")
    Game.__table__.create(engine)
    print("✅ Tabla 'games' creada exitosamente")

    # Verificar creación
    print("\n🔍 Verificando tabla...")
    inspector = inspect(engine)

    if "games" in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns("games")]
        print(f"✅ Tabla 'games' verificada con {len(columns)} columnas:")
        for col in columns:
            print(f"   - {col}")
    else:
        print("❌ Error: La tabla no se creó correctamente")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("✅ MIGRACIÓN COMPLETADA")
    print("=" * 70)
    print("\nPróximo paso: Ejecutar 'python populate_games_table.py' para llenar la tabla")

if __name__ == "__main__":
    main()
