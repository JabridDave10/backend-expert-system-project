"""
Script - Popular Tabla Games desde NDJSON

Este script carga todos los juegos desde catalog_games.ndjson
y los inserta en la base de datos PostgreSQL.
"""

import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import DATABASE_URL
from app.modules.expert_system.models.game import Game
from app.modules.expert_system.services.catalog_store import CatalogStore


def parse_game_data(game_json: dict) -> dict:
    """
    Parsea los datos del JSON del catálogo al formato del modelo Game.

    Args:
        game_json: Diccionario con datos del juego desde NDJSON

    Returns:
        Diccionario con datos formateados para Game model
    """
    # Extraer ESRB rating
    esrb_rating = None
    if game_json.get("esrb_rating"):
        esrb_rating = game_json["esrb_rating"].get("name")

    return {
        "id": game_json.get("id"),
        "slug": game_json.get("slug", f"game-{game_json.get('id')}"),
        "name": game_json.get("name", "Unknown Game"),
        "released": game_json.get("released"),
        "tba": game_json.get("tba", False),
        "background_image": game_json.get("background_image"),
        "rating": game_json.get("rating", 0.0),
        "rating_top": game_json.get("rating_top", 0),
        "ratings_count": game_json.get("ratings_count", 0),
        "metacritic": game_json.get("metacritic"),
        "playtime": game_json.get("playtime", 0),
        "genres_json": game_json.get("genres", []),
        "platforms_json": game_json.get("platforms", []),
        "parent_platforms_json": game_json.get("parent_platforms", []),
        "tags_json": game_json.get("tags", []),
        "stores_json": game_json.get("stores", []),
        "ratings_json": game_json.get("ratings", []),
        "esrb_rating": esrb_rating,
        "reviews_count": game_json.get("reviews_count", 0),
        "reviews_text_count": game_json.get("reviews_text_count", 0),
        "added": game_json.get("added", 0),
        "suggestions_count": game_json.get("suggestions_count", 0),
        "updated": game_json.get("updated"),
        "saturated_color": game_json.get("saturated_color"),
        "dominant_color": game_json.get("dominant_color"),
    }


def main():
    print("=" * 70)
    print("POBLAR TABLA GAMES DESDE NDJSON")
    print("=" * 70)

    NDJSON_PATH = "app_data/catalog_games.ndjson"

    # Crear conexión a BD
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Verificar si ya hay datos
        existing_count = db.query(Game).count()

        if existing_count > 0:
            print(f"\n⚠️  La tabla 'games' ya tiene {existing_count} registros.")
            response = input("¿Deseas eliminarlos y recargar? [y/N]: ")

            if response.lower() == 'y':
                print("\n🗑️  Eliminando registros existentes...")
                db.query(Game).delete()
                db.commit()
                print("✅ Registros eliminados")
            else:
                print("❌ Operación cancelada")
                return

        # Cargar desde NDJSON
        print(f"\n📖 Leyendo juegos desde {NDJSON_PATH}...")
        catalog_store = CatalogStore(NDJSON_PATH)

        games_data = []
        count = 0

        for game_json in catalog_store.iter_ndjson(NDJSON_PATH):
            try:
                game_data = parse_game_data(game_json)
                games_data.append(game_data)
                count += 1

                # Imprimir progreso cada 100 juegos
                if count % 100 == 0:
                    print(f"   Procesados: {count} juegos...")

            except Exception as e:
                print(f"   ⚠️  Error procesando juego ID {game_json.get('id')}: {e}")
                continue

        print(f"\n✅ Total de juegos procesados: {count}")

        if count == 0:
            print("❌ No se encontraron juegos para cargar")
            return

        # Insertar en base de datos por lotes (bulk insert)
        print("\n💾 Insertando en base de datos...")
        BATCH_SIZE = 500

        for i in range(0, len(games_data), BATCH_SIZE):
            batch = games_data[i:i + BATCH_SIZE]
            db.bulk_insert_mappings(Game, batch)
            db.commit()
            print(f"   Insertados: {min(i + BATCH_SIZE, len(games_data))} / {len(games_data)}")

        print("\n✅ Todos los juegos insertados exitosamente")

        # Verificar inserción
        final_count = db.query(Game).count()
        print(f"\n🔍 Verificación: {final_count} juegos en la tabla 'games'")

        # Mostrar estadísticas
        print("\n📊 Estadísticas del catálogo:")
        print(f"   - Total juegos: {final_count}")

        top_rated = db.query(Game).filter(Game.rating > 0).order_by(Game.rating.desc()).limit(5).all()
        if top_rated:
            print("\n🏆 Top 5 juegos mejor valorados:")
            for game in top_rated:
                print(f"   - {game.name} ({game.rating}/5.0)")

        genres_count = db.query(Game).filter(Game.genres_json.isnot(None)).count()
        print(f"\n   - Juegos con géneros: {genres_count}")

        with_metacritic = db.query(Game).filter(Game.metacritic.isnot(None)).count()
        print(f"   - Juegos con Metacritic score: {with_metacritic}")

        with_esrb = db.query(Game).filter(Game.esrb_rating.isnot(None)).count()
        print(f"   - Juegos con rating ESRB: {with_esrb}")

        print("\n" + "=" * 70)
        print("✅ PROCESO COMPLETADO")
        print("=" * 70)
        print("\nAhora el sistema experto puede recomendar juegos con información completa!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    main()
