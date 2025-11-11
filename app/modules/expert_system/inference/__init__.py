"""Inference Engine Components - Motor de Inferencia del Sistema Experto"""

from app.modules.expert_system.inference.working_memory import WorkingMemory
from app.modules.expert_system.inference.pattern_matcher import PatternMatcher
from app.modules.expert_system.inference.conflict_resolver import ConflictResolver
from app.modules.expert_system.inference.inference_engine import InferenceEngine
from app.modules.expert_system.inference.explanation_module import ExplanationModule

__all__ = [
    "WorkingMemory",
    "PatternMatcher",
    "ConflictResolver",
    "InferenceEngine",
    "ExplanationModule",
]
