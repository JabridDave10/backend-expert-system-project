# 🎮 Setup del Catálogo de Juegos

Esta guía te explica cómo configurar completamente el catálogo de juegos en el sistema experto, desde la carga de datos hasta la generación automática de reglas.

---

## 📋 Requisitos Previos

- Docker y Docker Compose instalados y corriendo
- Contenedor `backend-expert-system-project` activo
- Archivo `app_data/catalog_games.ndjson` con tus juegos

Para verificar que Docker está corriendo:
```bash
docker ps
```

Deberías ver los contenedores:
- `backend-expert-system-project` (Backend FastAPI)
- `backend-expert-system-project-db-1` (PostgreSQL)
- `backend-expert-system-project-pgadmin-1` (PgAdmin)

---

## 🚀 Setup Completo - Desde Cero

### **Paso 1: Verificar Catálogo de Juegos**

Asegúrate de que existe el archivo con tus juegos:

```bash
# Verificar que existe el archivo
dir app_data\catalog_games.ndjson
```

Este archivo debe contener juegos en formato NDJSON (un objeto JSON por línea):
```json
{"id": 58781, "name": "The Elder Scrolls VI", "rating": 4.86, "genres": [...], ...}
{"id": 3328, "name": "The Witcher 3", "rating": 4.66, "genres": [...], ...}
```

📊 **Actualmente tienes**: 1600 juegos en el catálogo

---

### **Paso 2: Crear Tabla `games` en Base de Datos**

Este paso crea la tabla PostgreSQL que almacenará todos los juegos:

```bash
echo y | docker exec -i backend-expert-system-project python migrate_games_table.py
```

**¿Qué hace este comando?**
- Crea la tabla `games` con 26 columnas (id, name, rating, genres, platforms, etc.)
- Si la tabla ya existe, pregunta si deseas recrearla
- `echo y` responde automáticamente "sí" para recrearla

**Salida esperada:**
```
======================================================================
MIGRACIÓN: Crear Tabla Games
======================================================================
✅ Tabla 'games' creada exitosamente
✅ Tabla 'games' verificada con 26 columnas
```

---

### **Paso 3: Cargar Juegos a la Base de Datos**

Este paso lee el archivo NDJSON e inserta todos los juegos en PostgreSQL:

```bash
echo y | docker exec -i backend-expert-system-project python populate_games_table.py
```

**¿Qué hace este comando?**
- Lee `app_data/catalog_games.ndjson` línea por línea
- Parsea la información de cada juego (nombre, géneros, plataformas, rating, etc.)
- Inserta los juegos en la BD por lotes de 500
- Si ya hay datos, pregunta si deseas eliminarlos y recargar

**Salida esperada:**
```
======================================================================
POBLAR TABLA GAMES DESDE NDJSON
======================================================================
📖 Leyendo juegos desde app_data/catalog_games.ndjson...
   Procesados: 100 juegos...
   Procesados: 200 juegos...
   ...
✅ Total de juegos procesados: 1600
💾 Insertando en base de datos...
✅ Todos los juegos insertados exitosamente
🔍 Verificación: 1600 juegos en la tabla 'games'

🏆 Top 5 juegos mejor valorados:
   - The Elder Scrolls VI (4.86/5.0)
   - Super Robot Taisen: Original Generation (4.83/5.0)
   ...
```

⏱️ **Tiempo estimado**: 10-30 segundos dependiendo de la cantidad de juegos

---

### **Paso 4: Generar Reglas desde el Catálogo**

Este paso analiza los juegos y genera automáticamente reglas inteligentes para el sistema experto:

```bash
docker exec -i backend-expert-system-project python populate_rules_from_catalog.py
```

**¿Qué hace este comando?**
- Analiza cada juego del catálogo NDJSON
- Genera reglas complejas con 2-3 condiciones:
  - **Género + Calidad**: "Si usuario quiere RPG y calidad → Recomendar Witcher 3"
  - **Edad + Calidad**: "Si usuario menor 13 años y calidad → Recomendar Minecraft"
  - **Multijugador + Género**: "Si quiere multijugador y shooter → Recomendar CSGO"
  - **Presupuesto + Género**: "Si presupuesto bajo y indie → Recomendar Stardew Valley"
  - **Plataforma**: "Si solo tiene PC → Recomendar juegos de PC"
- Crea reglas únicas con IDs para evitar duplicados
- Asigna prioridades y especificidad a cada regla

**Salida esperada:**
```
======================================================================
GENERACIÓN DE REGLAS DESDE CATÁLOGO
======================================================================
📖 Analizando juegos desde app_data/catalog_games.ndjson...
   Analizados: 100 juegos...
   Analizados: 200 juegos...
   ...
✅ Análisis completado: 1600 juegos

📝 Generando reglas desde análisis...
✅ Reglas generadas: 187 reglas

💾 Guardando reglas en base de datos...
✅ Todas las reglas insertadas: 187 reglas

📊 Estadísticas:
   - Total de reglas: 187
   - Categorías: genre_match, multiplayer_match, age_appropriate, budget_filter, etc.
```

⏱️ **Tiempo estimado**: 5-15 segundos

🎯 **Cantidad esperada**: 150-250 reglas complejas

---

### **Paso 5: Reiniciar Servidor FastAPI**

Para que el servidor cargue todos los cambios en los modelos y la base de datos:

```bash
docker restart backend-expert-system-project
```

**Salida esperada:**
```
backend-expert-system-project
```

⏱️ **Esperar**: 5-10 segundos para que el servidor arranque completamente

---

### **Paso 6: Verificar que Todo Funciona**

#### **Opción A: Verificar con curl (CMD/PowerShell)**

```bash
curl -X POST "http://localhost:8000/api/expert-system/infer" ^
  -H "Content-Type: application/json" ^
  -d "{\"initial_facts\": [{\"entity\": \"user\", \"attribute\": \"prefers_genre\", \"value\": \"RPG\"}, {\"entity\": \"user\", \"attribute\": \"wants_quality\", \"value\": true}], \"goal\": \"recommend_game\", \"max_iterations\": 50}"
```

#### **Opción B: Usar archivo JSON**

Crea un archivo `test_recommendation.json`:
```json
{
  "initial_facts": [
    {"entity": "user", "attribute": "prefers_genre", "value": "RPG"},
    {"entity": "user", "attribute": "wants_quality", "value": true},
    {"entity": "user", "attribute": "prefers_multiplayer", "value": false},
    {"entity": "user", "attribute": "min_age", "value": 18}
  ],
  "goal": "recommend_game",
  "max_iterations": 50,
  "conflict_strategy": "combined"
}
```

Luego ejecuta:
```bash
curl -X POST "http://localhost:8000/api/expert-system/infer" ^
  -H "Content-Type: application/json" ^
  -d @test_recommendation.json
```

#### **Opción C: Usar Swagger UI (Recomendado)**

1. Abre tu navegador en: [http://localhost:8000/docs](http://localhost:8000/docs)
2. Busca el endpoint `POST /api/expert-system/infer`
3. Click en "Try it out"
4. Pega el JSON de ejemplo
5. Click en "Execute"

---

## ✅ Respuesta Esperada

Si todo está bien configurado, deberías recibir algo como:

```json
{
  "session_id": 42,
  "success": true,
  "status": "completed",
  "goal": "recommend_game",
  "iterations": 3,
  "execution_time": 0.142,
  "conclusions": [
    {
      "type": "recommendation",
      "game_id": 3328,
      "confidence": 0.96,
      "reason": "Recommended based on RPG genre and quality preference"
    }
  ],
  "recommendations": [
    {
      "id": 89,
      "session_id": 42,
      "game_id": 3328,
      "game_title": "The Witcher 3: Wild Hunt",
      "confidence": 0.96,
      "rank": 1,
      "justification": "Recommended based on RPG genre and quality preference | Géneros: RPG, Action | Rating: 4.66/5.0 | Plataformas: PC, PlayStation, Xbox | Lanzamiento: 2015-05-18",
      "reasons": {
        "rule_reason": "Recommended based on RPG genre and quality preference",
        "genres": ["RPG", "Action"],
        "platforms": ["PC", "PlayStation 4", "Xbox One"],
        "rating": 4.66,
        "metacritic": 92,
        "image_url": "https://media.rawg.io/media/games/618/...",
        "released": "2015-05-18",
        "playtime": 46,
        "esrb_rating": "Mature 17+"
      }
    }
  ],
  "explanation": {
    "summary": "Inference completed successfully in 3 iterations...",
    "reasoning_chain": [...],
    "conclusions_explanation": [...],
    "confidence_breakdown": [...]
  }
}
```

🎯 **Nota importante**: Ahora las recomendaciones incluyen:
- ✅ **Nombre del juego** (game_title)
- ✅ **Géneros** completos
- ✅ **Plataformas** disponibles
- ✅ **Rating** y Metacritic
- ✅ **Imagen** del juego
- ✅ **Fecha de lanzamiento**
- ✅ **Clasificación ESRB**

---

## 🔧 Comandos de Utilidad

### Ver logs del servidor
```bash
docker logs backend-expert-system-project --tail 50 -f
```

### Verificar cantidad de juegos en BD
```bash
docker exec -i backend-expert-system-project python -c "from app.core.database import SessionLocal; from app.modules.expert_system.models.game import Game; db = SessionLocal(); print(f'Juegos en BD: {db.query(Game).count()}'); db.close()"
```

### Verificar cantidad de reglas en BD
```bash
docker exec -i backend-expert-system-project python -c "from app.core.database import SessionLocal; from app.modules.expert_system.models.rule import Rule; db = SessionLocal(); print(f'Reglas en BD: {db.query(Rule).count()}'); db.close()"
```

### Acceder a la base de datos con PgAdmin
1. Abre: [http://localhost:8080](http://localhost:8080)
2. Usuario: `admin@admin.com`
3. Password: `admin`
4. Conectar al servidor PostgreSQL:
   - Host: `db`
   - Port: `5432`
   - Database: `expert_db`
   - Username: `admin`
   - Password: `admin`

---

## 🆘 Solución de Problemas

### Error: "could not translate host name 'db'"
**Causa**: Los comandos se están ejecutando fuera de Docker.

**Solución**: Usar `docker exec` para ejecutar comandos dentro del contenedor:
```bash
docker exec -i backend-expert-system-project python migrate_games_table.py
```

### Error: "Table 'games' already exists"
**Causa**: La tabla ya fue creada previamente.

**Solución**: Responder `y` cuando el script pregunte si deseas recrearla:
```bash
echo y | docker exec -i backend-expert-system-project python migrate_games_table.py
```

### Error: "Game {id} not found in database"
**Causa**: Las reglas referencian juegos que no están en la tabla `games`.

**Solución**: Asegúrate de ejecutar `populate_games_table.py` ANTES de `populate_rules_from_catalog.py`.

### No se retorna el nombre del juego
**Causa**: El servidor no ha recargado los cambios.

**Solución**: Reiniciar el contenedor:
```bash
docker restart backend-expert-system-project
```

### Muy pocas reglas generadas
**Causa**: El catálogo tiene pocos juegos o no tienen la información necesaria (géneros, tags, etc.).

**Solución**: Verifica que tus juegos en el NDJSON tengan campos completos como `genres`, `tags`, `esrb_rating`, etc.

---

## 🔄 Actualizar Solo el Catálogo (Sin Perder Datos)

Si ya tienes todo configurado y solo quieres agregar más juegos:

```bash
# 1. Agregar nuevos juegos a catalog_games.ndjson

# 2. Ejecutar populate (decir N cuando pregunte si borrar)
docker exec -i backend-expert-system-project python populate_games_table.py

# 3. Regenerar reglas
docker exec -i backend-expert-system-project python populate_rules_from_catalog.py

# 4. Reiniciar servidor
docker restart backend-expert-system-project
```

---

## 📊 Resumen de Archivos Importantes

| Archivo | Descripción |
|---------|-------------|
| `app_data/catalog_games.ndjson` | Catálogo de juegos (1600 juegos) |
| `migrate_games_table.py` | Script para crear tabla `games` |
| `populate_games_table.py` | Script para cargar juegos a BD |
| `populate_rules_from_catalog.py` | Script para generar reglas automáticamente |
| `app/modules/expert_system/models/game.py` | Modelo SQLAlchemy de Game |
| `app/modules/expert_system/services/inference_service.py` | Servicio que consulta BD para recomendaciones |

---

## 🎉 ¡Listo!

Ahora tu sistema experto está completamente configurado con:

✅ **1600 juegos** en la base de datos
✅ **~187 reglas inteligentes** generadas automáticamente
✅ **Recomendaciones completas** con nombre, géneros, rating, plataformas
✅ **Motor de inferencia** funcionando con forward chaining
✅ **Explicabilidad** completa del razonamiento

**Para usar el sistema:** Envía tus preferencias (género, edad, presupuesto, etc.) al endpoint `/api/expert-system/infer` y recibirás recomendaciones personalizadas con información completa de cada juego.

---

**¿Preguntas?** Revisa el archivo principal [EXPERT_SYSTEM_README.md](EXPERT_SYSTEM_README.md) para documentación completa de la arquitectura y API.
