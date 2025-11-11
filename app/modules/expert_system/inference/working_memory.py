"""
Working Memory - Memoria de Trabajo del Sistema Experto

La memoria de trabajo almacena el estado actual de los hechos durante una sesión de inferencia.
Permite agregar, consultar y modificar hechos dinámicamente.
"""

from typing import Dict, List, Optional, Tuple, Any
from app.modules.expert_system.models.fact import Fact


class WorkingMemory:
    """
    Memoria de trabajo que almacena hechos durante una sesión de inferencia.

    La memoria de trabajo usa una estructura de diccionario para acceso rápido:
    Key: (entity, attribute) -> Fact

    Ejemplo:
        wm = WorkingMemory()
        wm.add_fact(Fact(entity="user_1", attribute="age", value="25", value_type="int"))
        fact = wm.get_fact("user_1", "age")
        print(fact.get_typed_value())  # 25 (int)
    """

    def __init__(self, initial_facts: Optional[List[Fact]] = None):
        """
        Inicializa la memoria de trabajo.

        Args:
            initial_facts: Lista opcional de hechos iniciales
        """
        # Almacenamiento principal: (entity, attribute) -> Fact
        self.facts: Dict[Tuple[str, str], Fact] = {}

        # Índices adicionales para búsquedas eficientes
        self.facts_by_entity: Dict[str, List[Fact]] = {}  # entity -> List[Fact]
        self.facts_by_source: Dict[str, List[Fact]] = {}  # source -> List[Fact]

        # Carga hechos iniciales
        if initial_facts:
            for fact in initial_facts:
                self.add_fact(fact)

    def add_fact(self, fact: Fact) -> bool:
        """
        Agrega un hecho a la memoria de trabajo.

        Si ya existe un hecho con la misma (entity, attribute), lo sobrescribe
        solo si el nuevo hecho tiene mayor confianza.

        Args:
            fact: Hecho a agregar

        Returns:
            True si se agregó/actualizó, False si no
        """
        key = (fact.entity, fact.attribute)

        # Verificar si ya existe un hecho con la misma clave
        existing_fact = self.facts.get(key)

        if existing_fact:
            # Solo reemplazar si el nuevo hecho tiene mayor confianza
            if fact.confidence > existing_fact.confidence:
                self._remove_from_indexes(existing_fact)
                self._add_to_indexes(fact)
                self.facts[key] = fact
                return True
            return False
        else:
            # Agregar nuevo hecho
            self.facts[key] = fact
            self._add_to_indexes(fact)
            return True

    def add_facts(self, facts: List[Fact]) -> int:
        """
        Agrega múltiples hechos a la memoria de trabajo.

        Args:
            facts: Lista de hechos

        Returns:
            Número de hechos agregados/actualizados
        """
        count = 0
        for fact in facts:
            if self.add_fact(fact):
                count += 1
        return count

    def get_fact(self, entity: str, attribute: str) -> Optional[Fact]:
        """
        Obtiene un hecho específico por entidad y atributo.

        Args:
            entity: Entidad del hecho
            attribute: Atributo del hecho

        Returns:
            Fact si existe, None si no
        """
        key = (entity, attribute)
        return self.facts.get(key)

    def get_facts_by_entity(self, entity: str) -> List[Fact]:
        """
        Obtiene todos los hechos de una entidad.

        Args:
            entity: Entidad a buscar

        Returns:
            Lista de hechos
        """
        return self.facts_by_entity.get(entity, [])

    def get_facts_by_source(self, source: str) -> List[Fact]:
        """
        Obtiene todos los hechos de un origen específico.

        Args:
            source: Origen de los hechos (ej: "user_input", "inferred")

        Returns:
            Lista de hechos
        """
        return self.facts_by_source.get(source, [])

    def get_all_facts(self) -> List[Fact]:
        """
        Obtiene todos los hechos en la memoria de trabajo.

        Returns:
            Lista de todos los hechos
        """
        return list(self.facts.values())

    def fact_exists(self, entity: str, attribute: str, value: Any = None) -> bool:
        """
        Verifica si existe un hecho con la entidad y atributo dados.

        Args:
            entity: Entidad del hecho
            attribute: Atributo del hecho
            value: Valor opcional para verificar

        Returns:
            True si existe, False si no
        """
        fact = self.get_fact(entity, attribute)
        if not fact:
            return False

        if value is not None:
            # Convertir ambos valores a string para comparar
            return str(fact.get_typed_value()) == str(value)

        return True

    def remove_fact(self, entity: str, attribute: str) -> bool:
        """
        Elimina un hecho de la memoria de trabajo.

        Args:
            entity: Entidad del hecho
            attribute: Atributo del hecho

        Returns:
            True si se eliminó, False si no existía
        """
        key = (entity, attribute)
        fact = self.facts.get(key)

        if fact:
            self._remove_from_indexes(fact)
            del self.facts[key]
            return True

        return False

    def clear(self):
        """Limpia toda la memoria de trabajo."""
        self.facts.clear()
        self.facts_by_entity.clear()
        self.facts_by_source.clear()

    def count(self) -> int:
        """Retorna el número de hechos en la memoria de trabajo."""
        return len(self.facts)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la memoria de trabajo a diccionario.

        Returns:
            Diccionario con todos los hechos
        """
        return {
            "facts": [fact.to_dict() for fact in self.facts.values()],
            "count": len(self.facts),
        }

    def _add_to_indexes(self, fact: Fact):
        """Agrega el hecho a los índices secundarios."""
        # Índice por entidad
        if fact.entity not in self.facts_by_entity:
            self.facts_by_entity[fact.entity] = []
        self.facts_by_entity[fact.entity].append(fact)

        # Índice por fuente
        if fact.source not in self.facts_by_source:
            self.facts_by_source[fact.source] = []
        self.facts_by_source[fact.source].append(fact)

    def _remove_from_indexes(self, fact: Fact):
        """Elimina el hecho de los índices secundarios."""
        # Índice por entidad
        if fact.entity in self.facts_by_entity:
            self.facts_by_entity[fact.entity] = [
                f for f in self.facts_by_entity[fact.entity] if f != fact
            ]
            if not self.facts_by_entity[fact.entity]:
                del self.facts_by_entity[fact.entity]

        # Índice por fuente
        if fact.source in self.facts_by_source:
            self.facts_by_source[fact.source] = [
                f for f in self.facts_by_source[fact.source] if f != fact
            ]
            if not self.facts_by_source[fact.source]:
                del self.facts_by_source[fact.source]

    def __repr__(self):
        return f"<WorkingMemory(facts={self.count()})>"

    def __str__(self):
        facts_str = "\n".join([f"  - {fact}" for fact in self.facts.values()])
        return f"WorkingMemory ({self.count()} facts):\n{facts_str}"
