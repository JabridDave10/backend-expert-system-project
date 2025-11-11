"""
Script de Migración para el Sistema Experto

Este script crea todas las tablas necesarias para el sistema experto:
- facts: Base de hechos
- rules: Base de reglas
- inference_sessions: Memoria de trabajo
- inference_logs: Trazabilidad
- recommendations: Recomendaciones generadas

Uso:
    python migrate_expert_system.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from app.core.database import create_tables, engine, Base
from sqlalchemy import inspect


def check_existing_tables():
    """Verifica qué tablas ya existen"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    return existing_tables


def main():
    print("=" * 70)
    print("MIGRACIÓN DEL SISTEMA EXPERTO")
    print("=" * 70)
    print()

    # Verificar tablas existentes
    print("1. Verificando tablas existentes...")
    existing_tables = check_existing_tables()
    print(f"   Tablas existentes: {len(existing_tables)}")
    for table in existing_tables:
        print(f"   - {table}")
    print()

    # Crear nuevas tablas
    print("2. Creando tablas del sistema experto...")
    try:
        create_tables()
        print()
        print("✅ Migración completada exitosamente!")
        print()

        # Verificar tablas después de la migración
        print("3. Verificando tablas después de la migración...")
        new_tables = check_existing_tables()
        expert_system_tables = [t for t in new_tables if t in [
            "facts", "rules", "inference_sessions", "inference_logs", "recommendations"
        ]]

        print(f"   Tablas del sistema experto creadas: {len(expert_system_tables)}")
        for table in expert_system_tables:
            print(f"   ✓ {table}")

        if len(expert_system_tables) == 5:
            print()
            print("🎉 ¡Todas las tablas del sistema experto fueron creadas correctamente!")
        else:
            print()
            print("⚠️  Advertencia: No todas las tablas fueron creadas.")
            missing = set(["facts", "rules", "inference_sessions", "inference_logs", "recommendations"]) - set(expert_system_tables)
            print(f"   Tablas faltantes: {missing}")

    except Exception as e:
        print()
        print(f"❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
