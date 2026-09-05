"""Call before TinyToT cache rebuild so sidecar beliefs become knowledge."""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

def before_reload():
    try:
        from .content import KNOWLEDGE_DIR
        from .sidecar import distill_into_knowledge, memory_dir, tiny_root
        return distill_into_knowledge(KNOWLEDGE_DIR, memory_dir(), tiny_root())
    except Exception as exc:
        logger.warning("sidecar distill skipped: %s", exc)
        return None
