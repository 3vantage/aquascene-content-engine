"""
Aquascaping Knowledge Base Package

Provides specialized knowledge and context for aquascaping content generation:
- Plant database and care information
- Equipment recommendations and specifications
- Technique guides and best practices
- Brand and product knowledge
- Common problems and solutions
"""

from .aquascaping_kb import AquascapingKnowledgeBase
from .plant_database import PlantDatabase
from .technique_guide import TechniqueGuide
from .product_knowledge import ProductKnowledge

__all__ = [
    "AquascapingKnowledgeBase",
    "PlantDatabase",
    "TechniqueGuide", 
    "ProductKnowledge"
]