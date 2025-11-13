"""
Migration Script - Crear tabla GameRules

Este script crea la tabla 'game_rules' en la base de datos para almacenar
la relación muchos-a-muchos entre juegos y reglas.
"""

import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from sqlalchemy import create_engine, inspect
from app.core.database import DATABASE_URL, Base
from app.modules.expert_system.models.game_rule import GameRule

def main():
    print("=" * 70)
    print("MIGRACIÓN: Crear Tabla GameRules")
    print("=" * 70)

    # Crear engine
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    # Verificar si la tabla ya existe
    existing_tables = inspector.get_table_names()

    if "game_rules" in existing_tables:
        print("\n⚠️  La tabla 'game_rules' ya existe.")
        response = input("¿Deseas recrearla? (se perderán todos los datos) [y/N]: ")

        if response.lower() != 'y':
            print("❌ Migración cancelada")
            return

        print("\n🗑️  Eliminando tabla 'game_rules'...")
        GameRule.__table__.drop(engine)
        print("✅ Tabla eliminada")

    # Crear tabla
    print("\n📋 Creando tabla 'game_rules'...")
    GameRule.__table__.create(engine)
    print("✅ Tabla 'game_rules' creada exitosamente")

    # Verificar creación
    print("\n🔍 Verificando tabla...")
    inspector = inspect(engine)

    if "game_rules" in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns("game_rules")]
        print(f"✅ Tabla 'game_rules' verificada con {len(columns)} columnas:")
        for col in columns:
            print(f"   - {col}")
    else:
        print("❌ Error: La tabla no se creó correctamente")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("✅ MIGRACIÓN COMPLETADA")
    print("=" * 70)
    print("\nAhora puedes asignar reglas a juegos desde el panel de administración")

if __name__ == "__main__":
    main()
