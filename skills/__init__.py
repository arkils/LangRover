"""Skills package for LangRover.

Provides the extensible skill system:

- ``Skill``         — abstract base class all skills must implement
- ``SkillContext``  — runtime snapshot passed to ``Skill.execute()``
- ``SkillRegistry`` — holds registered skills; converts them to LangChain tools
- ``get_default_skills`` — returns the built-in starter set of skills
"""

from skills.base import Skill, SkillContext
from skills.registry import SkillRegistry
from skills.builtin import get_default_skills

__all__ = [
    "Skill",
    "SkillContext",
    "SkillRegistry",
    "get_default_skills",
]
