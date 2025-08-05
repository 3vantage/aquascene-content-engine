"""
Aquascaping Knowledge Base

Central repository of aquascaping knowledge including plants, techniques,
equipment, and best practices for content generation.
"""

import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiofiles
import structlog

logger = structlog.get_logger()


class DifficultyLevel(Enum):
    """Plant and technique difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AquascapeStyle(Enum):
    """Aquascaping styles and layouts"""
    NATURE = "nature"
    DUTCH = "dutch"
    IWAGUMI = "iwagumi"
    JUNGLE = "jungle"
    BIOTOPE = "biotope"
    PALUDARIUM = "paludarium"


@dataclass
class Plant:
    """Aquatic plant information"""
    name: str
    scientific_name: str
    family: str
    difficulty: DifficultyLevel
    light_requirement: str  # low, medium, high
    co2_requirement: str    # none, low, medium, high
    growth_rate: str        # slow, medium, fast
    placement: str          # foreground, midground, background
    care_tips: List[str] = field(default_factory=list)
    compatible_with: List[str] = field(default_factory=list)
    common_issues: List[str] = field(default_factory=list)
    fertilizer_needs: Dict[str, str] = field(default_factory=dict)
    propagation: str = ""
    max_height: Optional[str] = None
    temperature_range: Optional[str] = None
    ph_range: Optional[str] = None


@dataclass
class Equipment:
    """Aquascaping equipment information"""
    name: str
    category: str  # lighting, filtration, substrate, etc.
    brand: str
    recommended_for: List[str] = field(default_factory=list)
    tank_sizes: List[str] = field(default_factory=list)
    price_range: Optional[str] = None
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    setup_tips: List[str] = field(default_factory=list)


@dataclass
class Technique:
    """Aquascaping technique information"""
    name: str
    category: str  # planting, trimming, layout, etc.
    difficulty: DifficultyLevel
    description: str
    steps: List[str] = field(default_factory=list)
    tools_needed: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)
    when_to_use: List[str] = field(default_factory=list)
    related_techniques: List[str] = field(default_factory=list)


@dataclass
class Problem:
    """Common aquascaping problems and solutions"""
    name: str
    category: str  # algae, plant health, water quality, etc.
    symptoms: List[str] = field(default_factory=list)
    causes: List[str] = field(default_factory=list)
    solutions: List[str] = field(default_factory=list)
    prevention: List[str] = field(default_factory=list)
    difficulty_to_fix: DifficultyLevel = DifficultyLevel.BEGINNER


class AquascapingKnowledgeBase:
    """Central aquascaping knowledge repository"""
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or "data/knowledge"
        
        # Knowledge repositories
        self.plants: Dict[str, Plant] = {}
        self.equipment: Dict[str, Equipment] = {}
        self.techniques: Dict[str, Technique] = {}
        self.problems: Dict[str, Problem] = {}
        
        # Indexes for fast lookup
        self.plant_by_difficulty: Dict[DifficultyLevel, List[str]] = {}
        self.plant_by_placement: Dict[str, List[str]] = {}
        self.equipment_by_category: Dict[str, List[str]] = {}
        self.techniques_by_category: Dict[str, List[str]] = {}
        
        # Topic mappings
        self.topic_keywords = self._build_topic_keywords()
        
        # Initialize with default knowledge
        self._initialize_default_knowledge()
    
    def _build_topic_keywords(self) -> Dict[str, List[str]]:
        """Build keyword mappings for topic recognition"""
        return {
            "plants": [
                "plant", "plants", "aquatic plant", "stem plant", "carpet plant",
                "moss", "fern", "anubias", "cryptocoryne", "rotala", "ludwigia",
                "hemianthus", "monte carlo", "dwarf hairgrass", "java moss"
            ],
            "lighting": [
                "light", "lighting", "led", "par", "spectrum", "photoperiod",
                "lumens", "watts", "full spectrum", "plant light"
            ],
            "co2": [
                "co2", "carbon dioxide", "co2 system", "diffuser", "bubble counter",
                "drop checker", "ph controller", "pressurized co2", "diy co2"
            ],
            "fertilizer": [
                "fertilizer", "nutrients", "macro", "micro", "npk", "iron",
                "potassium", "phosphate", "nitrate", "liquid fertilizer", "root tabs"
            ],
            "substrate": [
                "substrate", "soil", "sand", "gravel", "aquasoil", "ada soil",
                "inert substrate", "nutritious substrate", "root feeding"
            ],
            "filtration": [
                "filter", "filtration", "canister filter", "hob filter",
                "biological filtration", "mechanical filtration", "flow rate"
            ],
            "algae": [
                "algae", "green algae", "brown algae", "black beard algae",
                "hair algae", "blue green algae", "staghorn algae", "algae control"
            ],
            "maintenance": [
                "maintenance", "water change", "trimming", "pruning",
                "cleaning", "algae removal", "replanting", "aquascape maintenance"
            ],
            "layout": [
                "layout", "composition", "golden ratio", "focal point",
                "depth", "perspective", "hardscape", "driftwood", "rocks"
            ],
            "styles": [
                "nature aquarium", "dutch style", "iwagumi", "jungle style",
                "biotope", "paludarium", "aquascaping style"
            ]
        }
    
    def _initialize_default_knowledge(self) -> None:
        """Initialize with basic aquascaping knowledge"""
        # Add some basic plants
        self._add_default_plants()
        self._add_default_equipment()
        self._add_default_techniques()
        self._add_default_problems()
        
        # Build indexes
        self._build_indexes()
    
    def _add_default_plants(self) -> None:
        """Add default plant knowledge"""
        default_plants = [
            Plant(
                name="Monte Carlo",
                scientific_name="Micranthemum tweediei",
                family="Linderniaceae",
                difficulty=DifficultyLevel.INTERMEDIATE,
                light_requirement="medium-high",
                co2_requirement="medium",
                growth_rate="medium",
                placement="foreground",
                care_tips=[
                    "Requires regular trimming to maintain carpet",
                    "Benefits from CO2 injection",
                    "Needs good flow and light penetration"
                ],
                compatible_with=["Rotala rotundifolia", "Anubias nana", "Java moss"],
                common_issues=["Melting when first planted", "Slow to establish carpet"],
                fertilizer_needs={"macro": "medium", "micro": "high"},
                propagation="runners and replanting trimmings",
                max_height="3-5 cm",
                temperature_range="20-28°C",
                ph_range="6.0-7.5"
            ),
            Plant(
                name="Anubias Nana",
                scientific_name="Anubias barteri var. nana",
                family="Araceae",
                difficulty=DifficultyLevel.BEGINNER,
                light_requirement="low-medium",
                co2_requirement="none",
                growth_rate="slow",
                placement="midground",
                care_tips=[
                    "Don't bury the rhizome in substrate",
                    "Attach to hardscape for best results",
                    "Very hardy and low maintenance"
                ],
                compatible_with=["Java moss", "Cryptocoryne", "Java fern"],
                common_issues=["Algae growth on leaves in high light"],
                fertilizer_needs={"macro": "low", "micro": "low"},
                propagation="rhizome division",
                max_height="10-15 cm",
                temperature_range="22-28°C",
                ph_range="6.0-8.0"
            ),
            Plant(
                name="Rotala Rotundifolia",
                scientific_name="Rotala rotundifolia",
                family="Lythraceae",
                difficulty=DifficultyLevel.INTERMEDIATE,
                light_requirement="medium-high",
                co2_requirement="medium",
                growth_rate="fast",
                placement="background",
                care_tips=[
                    "Regular trimming promotes bushy growth",
                    "Plant in groups for best visual impact",
                    "Colors better under high light and CO2"
                ],
                compatible_with=["Monte Carlo", "Cryptocoryne wendtii", "Anubias"],
                common_issues=["Leggy growth in low light", "Rapid growth requires frequent trimming"],
                fertilizer_needs={"macro": "high", "micro": "medium"},
                propagation="stem cuttings",
                max_height="20-50 cm",
                temperature_range="20-28°C",
                ph_range="5.5-7.5"
            )
        ]
        
        for plant in default_plants:
            self.plants[plant.name.lower()] = plant
    
    def _add_default_equipment(self) -> None:
        """Add default equipment knowledge"""
        default_equipment = [
            Equipment(
                name="Chihiros WRGB 2",
                category="lighting",
                brand="Chihiros",
                recommended_for=["planted tanks", "high-tech setups"],
                tank_sizes=["60cm", "90cm", "120cm"],
                price_range="mid-range",
                pros=[
                    "Full spectrum LED",
                    "App control with wireless controller",
                    "Good PAR values for plant growth",
                    "Sunrise/sunset simulation"
                ],
                cons=[
                    "Can be expensive",
                    "May need dimming for low-light plants"
                ],
                alternatives=["Fluval Plant 3.0", "Nicrew ClassicLED"],
                setup_tips=[
                    "Mount 20-30cm above water surface",
                    "Start with 50% intensity and adjust gradually",
                    "Use 6-8 hour photoperiod initially"
                ]
            ),
            Equipment(
                name="ADA Aqua Soil Amazonia",
                category="substrate",
                brand="ADA",
                recommended_for=["high-tech planted tanks", "soft water setups"],
                tank_sizes=["all sizes"],
                price_range="premium",
                pros=[
                    "Lowers pH and softens water",
                    "Rich in nutrients for plant growth",
                    "Creates natural aquatic environment",
                    "Long-lasting nutrient supply"
                ],
                cons=[
                    "Expensive compared to alternatives",
                    "Can cause ammonia spike initially",
                    "Requires careful washing"
                ],
                alternatives=["Fluval Stratum", "Seachem Flourite", "Tropica Aquarium Soil"],
                setup_tips=[
                    "Don't rinse before use",
                    "Add slowly to avoid cloudiness",
                    "Consider using powder type for small tanks"
                ]
            )
        ]
        
        for equipment in default_equipment:
            self.equipment[equipment.name.lower()] = equipment
    
    def _add_default_techniques(self) -> None:
        """Add default technique knowledge"""
        default_techniques = [
            Technique(
                name="Carpet Plant Dry Start",
                category="planting",
                difficulty=DifficultyLevel.INTERMEDIATE,
                description="Method to establish carpet plants before flooding the tank",
                steps=[
                    "Set up substrate and hardscape",
                    "Plant carpet plants in moist substrate",
                    "Cover tank with plastic wrap",
                    "Maintain high humidity for 4-6 weeks",
                    "Gradually flood the tank"
                ],
                tools_needed=["plastic wrap", "spray bottle", "tweezers"],
                best_practices=[
                    "Keep substrate consistently moist but not waterlogged",
                    "Provide adequate lighting during dry start",
                    "Flood slowly to prevent uprooting"
                ],
                common_mistakes=[
                    "Flooding too early",
                    "Allowing substrate to dry out",
                    "Not providing enough light"
                ],
                when_to_use=[
                    "Establishing difficult carpet plants",
                    "Creating dense carpet coverage",
                    "Reducing algae issues in startup"
                ]
            ),
            Technique(
                name="Dutch Style Trimming",
                category="maintenance",
                difficulty=DifficultyLevel.ADVANCED,
                description="Precise trimming technique for Dutch-style aquascapes",
                steps=[
                    "Plan the trimming session",
                    "Trim background plants first",
                    "Create terraced height differences",
                    "Maintain plant groups and streets",
                    "Remove all trimmed material"
                ],
                tools_needed=["sharp scissors", "tweezers", "algae scraper"],
                best_practices=[
                    "Trim regularly to maintain shape",
                    "Create flowing lines between plant groups",
                    "Maintain color contrast between species"
                ],
                common_mistakes=[
                    "Trimming too infrequently",
                    "Not maintaining proper proportions",
                    "Mixing incompatible growth rates"
                ],
                when_to_use=[
                    "Dutch-style aquascapes",
                    "High-maintenance planted tanks",
                    "Competition aquascapes"
                ]
            )
        ]
        
        for technique in default_techniques:
            self.techniques[technique.name.lower()] = technique
    
    def _add_default_problems(self) -> None:
        """Add default problem knowledge"""
        default_problems = [
            Problem(
                name="Green Dust Algae",
                category="algae",
                symptoms=[
                    "Fine green dust coating on glass and leaves",
                    "Makes water appear cloudy green",
                    "Easily wiped off surfaces"
                ],
                causes=[
                    "Imbalance between light and CO2",
                    "Low CO2 levels with high light",
                    "Nutrient deficiency",
                    "Poor circulation"
                ],
                solutions=[
                    "Increase CO2 levels",
                    "Reduce lighting period temporarily",
                    "Improve water circulation",
                    "Check and adjust fertilizer dosing"
                ],
                prevention=[
                    "Maintain consistent CO2 levels",
                    "Balance light with CO2 and nutrients",
                    "Regular water changes",
                    "Don't overstock the tank"
                ],
                difficulty_to_fix=DifficultyLevel.INTERMEDIATE
            ),
            Problem(
                name="Plant Melting",
                category="plant health",
                symptoms=[
                    "Leaves turning brown or transparent",
                    "Leaves disintegrating",
                    "Stems becoming soft and mushy",
                    "Sudden decline in plant health"
                ],
                causes=[
                    "Transition shock from new environment",
                    "Sudden parameter changes",
                    "Insufficient lighting or CO2",
                    "Root damage during planting"
                ],
                solutions=[
                    "Remove affected leaves immediately",
                    "Maintain stable water parameters",
                    "Ensure adequate lighting and CO2",
                    "Be patient - new growth often appears"
                ],
                prevention=[
                    "Acclimate plants gradually",
                    "Maintain stable conditions",
                    "Handle plants carefully during planting",
                    "Quarantine new plants if possible"
                ],
                difficulty_to_fix=DifficultyLevel.BEGINNER
            )
        ]
        
        for problem in default_problems:
            self.problems[problem.name.lower()] = problem
    
    def _build_indexes(self) -> None:
        """Build search indexes for fast lookup"""
        # Plant indexes
        for name, plant in self.plants.items():
            # By difficulty
            if plant.difficulty not in self.plant_by_difficulty:
                self.plant_by_difficulty[plant.difficulty] = []
            self.plant_by_difficulty[plant.difficulty].append(name)
            
            # By placement
            if plant.placement not in self.plant_by_placement:
                self.plant_by_placement[plant.placement] = []
            self.plant_by_placement[plant.placement].append(name)
        
        # Equipment indexes
        for name, equipment in self.equipment.items():
            if equipment.category not in self.equipment_by_category:
                self.equipment_by_category[equipment.category] = []
            self.equipment_by_category[equipment.category].append(name)
        
        # Technique indexes
        for name, technique in self.techniques.items():
            if technique.category not in self.techniques_by_category:
                self.techniques_by_category[technique.category] = []
            self.techniques_by_category[technique.category].append(name)
    
    async def get_context_for_topic(self, topic: str) -> str:
        """Get relevant knowledge context for a topic"""
        topic_lower = topic.lower()
        relevant_context = []
        
        # Identify topic categories
        matching_categories = self._identify_topic_categories(topic_lower)
        
        # Gather relevant information
        for category in matching_categories:
            if category == "plants":
                plant_info = self._get_plant_context(topic_lower)
                if plant_info:
                    relevant_context.append(f"PLANT INFORMATION:\n{plant_info}")
            
            elif category == "equipment":
                equipment_info = self._get_equipment_context(topic_lower)
                if equipment_info:
                    relevant_context.append(f"EQUIPMENT INFORMATION:\n{equipment_info}")
            
            elif category in ["lighting", "co2", "fertilizer", "substrate", "filtration"]:
                specific_equipment = self._get_category_equipment_context(category)
                if specific_equipment:
                    relevant_context.append(f"{category.upper()} EQUIPMENT:\n{specific_equipment}")
            
            elif category in ["maintenance", "layout", "styles"]:
                technique_info = self._get_technique_context(category)
                if technique_info:
                    relevant_context.append(f"TECHNIQUE INFORMATION:\n{technique_info}")
            
            elif category == "algae":
                problem_info = self._get_problem_context("algae")
                if problem_info:
                    relevant_context.append(f"ALGAE PROBLEMS & SOLUTIONS:\n{problem_info}")
        
        # Add general aquascaping principles if no specific matches
        if not relevant_context:
            relevant_context.append(self._get_general_principles())
        
        return "\n\n".join(relevant_context)
    
    def _identify_topic_categories(self, topic: str) -> List[str]:
        """Identify which categories a topic relates to"""
        matching_categories = []
        
        for category, keywords in self.topic_keywords.items():
            if any(keyword in topic for keyword in keywords):
                matching_categories.append(category)
        
        return matching_categories
    
    def _get_plant_context(self, topic: str) -> str:
        """Get plant-specific context"""
        context_parts = []
        
        # Look for specific plants mentioned
        for plant_name, plant in self.plants.items():
            if plant_name in topic or plant.scientific_name.lower() in topic:
                context_parts.append(self._format_plant_info(plant))
        
        # If no specific plants, provide general plant info based on keywords
        if not context_parts:
            if "carpet" in topic or "foreground" in topic:
                foreground_plants = self.plant_by_placement.get("foreground", [])
                for plant_name in foreground_plants[:2]:  # Limit to 2 examples
                    plant = self.plants[plant_name]
                    context_parts.append(self._format_plant_info(plant))
            
            elif "background" in topic:
                background_plants = self.plant_by_placement.get("background", [])
                for plant_name in background_plants[:2]:
                    plant = self.plants[plant_name]
                    context_parts.append(self._format_plant_info(plant))
        
        return "\n\n".join(context_parts)
    
    def _format_plant_info(self, plant: Plant) -> str:
        """Format plant information for context"""
        info = f"{plant.name} ({plant.scientific_name}):\n"
        info += f"- Difficulty: {plant.difficulty.value}\n"
        info += f"- Light: {plant.light_requirement}, CO2: {plant.co2_requirement}\n"
        info += f"- Growth rate: {plant.growth_rate}, Placement: {plant.placement}\n"
        
        if plant.care_tips:
            info += f"- Care tips: {'; '.join(plant.care_tips[:3])}\n"
        
        if plant.common_issues:
            info += f"- Common issues: {'; '.join(plant.common_issues)}\n"
        
        return info
    
    def _get_equipment_context(self, topic: str) -> str:
        """Get equipment-specific context"""
        context_parts = []
        
        # Look for specific equipment mentioned
        for equipment_name, equipment in self.equipment.items():
            if equipment_name in topic or equipment.brand.lower() in topic:
                context_parts.append(self._format_equipment_info(equipment))
        
        return "\n\n".join(context_parts)
    
    def _get_category_equipment_context(self, category: str) -> str:
        """Get equipment context for a specific category"""
        context_parts = []
        equipment_names = self.equipment_by_category.get(category, [])
        
        for equipment_name in equipment_names[:3]:  # Limit to 3 examples
            equipment = self.equipment[equipment_name]
            context_parts.append(self._format_equipment_info(equipment))
        
        return "\n\n".join(context_parts)
    
    def _format_equipment_info(self, equipment: Equipment) -> str:
        """Format equipment information for context"""
        info = f"{equipment.name} ({equipment.brand}):\n"
        info += f"- Category: {equipment.category}\n"
        
        if equipment.pros:
            info += f"- Pros: {'; '.join(equipment.pros[:3])}\n"
        
        if equipment.cons:
            info += f"- Cons: {'; '.join(equipment.cons[:2])}\n"
        
        if equipment.setup_tips:
            info += f"- Setup tips: {'; '.join(equipment.setup_tips[:2])}\n"
        
        return info
    
    def _get_technique_context(self, category: str) -> str:
        """Get technique context for a category"""
        context_parts = []
        technique_names = self.techniques_by_category.get(category, [])
        
        for technique_name in technique_names[:2]:  # Limit to 2 examples
            technique = self.techniques[technique_name]
            context_parts.append(self._format_technique_info(technique))
        
        return "\n\n".join(context_parts)
    
    def _format_technique_info(self, technique: Technique) -> str:
        """Format technique information for context"""
        info = f"{technique.name}:\n"
        info += f"- Difficulty: {technique.difficulty.value}\n"
        info += f"- Description: {technique.description}\n"
        
        if technique.best_practices:
            info += f"- Best practices: {'; '.join(technique.best_practices[:3])}\n"
        
        if technique.common_mistakes:
            info += f"- Common mistakes: {'; '.join(technique.common_mistakes[:2])}\n"
        
        return info
    
    def _get_problem_context(self, category: str) -> str:
        """Get problem and solution context for a category"""
        context_parts = []
        
        for problem_name, problem in self.problems.items():
            if problem.category == category:
                context_parts.append(self._format_problem_info(problem))
        
        return "\n\n".join(context_parts)
    
    def _format_problem_info(self, problem: Problem) -> str:
        """Format problem information for context"""
        info = f"{problem.name}:\n"
        
        if problem.symptoms:
            info += f"- Symptoms: {'; '.join(problem.symptoms[:3])}\n"
        
        if problem.causes:
            info += f"- Causes: {'; '.join(problem.causes[:3])}\n"
        
        if problem.solutions:
            info += f"- Solutions: {'; '.join(problem.solutions[:3])}\n"
        
        return info
    
    def _get_general_principles(self) -> str:
        """Get general aquascaping principles"""
        return """GENERAL AQUASCAPING PRINCIPLES:
- Balance light, CO2, and nutrients for healthy plant growth
- Start with easy plants and gradually add more demanding species
- Regular maintenance is key to long-term success
- Patience is essential - aquascapes take time to mature
- Focus on plant health over appearance in the first few weeks
- Water changes are crucial for nutrient balance and algae prevention
- Proper plant placement enhances both aesthetics and growth"""
    
    async def add_plant(self, plant: Plant) -> None:
        """Add a new plant to the knowledge base"""
        self.plants[plant.name.lower()] = plant
        self._build_indexes()
        logger.info(f"Added plant: {plant.name}")
    
    async def add_equipment(self, equipment: Equipment) -> None:
        """Add new equipment to the knowledge base"""
        self.equipment[equipment.name.lower()] = equipment
        self._build_indexes()
        logger.info(f"Added equipment: {equipment.name}")
    
    async def add_technique(self, technique: Technique) -> None:
        """Add new technique to the knowledge base"""
        self.techniques[technique.name.lower()] = technique
        self._build_indexes()
        logger.info(f"Added technique: {technique.name}")
    
    async def add_problem(self, problem: Problem) -> None:
        """Add new problem to the knowledge base"""
        self.problems[problem.name.lower()] = problem
        logger.info(f"Added problem: {problem.name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            "total_plants": len(self.plants),
            "total_equipment": len(self.equipment),
            "total_techniques": len(self.techniques),
            "total_problems": len(self.problems),
            "plant_difficulty_distribution": {
                difficulty.value: len(plants) 
                for difficulty, plants in self.plant_by_difficulty.items()
            },
            "equipment_categories": list(self.equipment_by_category.keys()),
            "technique_categories": list(self.techniques_by_category.keys())
        }