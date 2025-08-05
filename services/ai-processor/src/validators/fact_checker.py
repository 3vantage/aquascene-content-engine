"""
Fact Checker

Validates factual accuracy of aquascaping content against
the knowledge base and established best practices.
"""

import re
from typing import Dict, List, Optional, Any, Set
import structlog

from ..knowledge.aquascaping_kb import AquascapingKnowledgeBase

logger = structlog.get_logger()


class FactChecker:
    """Validates factual accuracy of aquascaping content"""
    
    def __init__(self, knowledge_base: AquascapingKnowledgeBase):
        self.knowledge_base = knowledge_base
        
        # Common factual patterns to check
        self.fact_patterns = {
            "plant_care": [
                (r"(\w+)\s+(?:requires?|needs?)\s+(low|medium|high)\s+light", self._check_light_requirement),
                (r"(\w+)\s+(?:requires?|needs?)\s+co2", self._check_co2_requirement),
                (r"(\w+)\s+grows?\s+(slow|medium|fast)", self._check_growth_rate),
                (r"(\w+)\s+is\s+(?:a\s+)?(beginner|intermediate|advanced|expert)", self._check_difficulty)
            ],
            "water_parameters": [
                (r"ph\s+(?:of\s+|should\s+be\s+)?(\d+\.?\d*)\s*-?\s*(\d+\.?\d*)?", self._check_ph_range),
                (r"temperature\s+(?:of\s+)?(\d+)\s*-?\s*(\d+)?\s*°?[cf]", self._check_temperature_range)
            ],
            "equipment": [
                (r"(\w+)\s+light\s+(?:is\s+)?(?:good|suitable|recommended)\s+for", self._check_lighting_recommendation),
                (r"(\w+)\s+substrate\s+(?:is\s+)?(?:good|suitable|recommended)", self._check_substrate_recommendation)
            ]
        }
        
        # Known facts and misconceptions
        self.factual_corrections = {
            "anubias rhizome buried": {
                "error": "anubias rhizome should not be buried",
                "correction": "anubias rhizome should be attached to hardscape, not buried in substrate"
            },
            "co2 for anubias": {
                "error": "anubias requires co2",
                "correction": "anubias does not require co2 injection"
            },
            "high light anubias": {
                "error": "anubias needs high light",
                "correction": "anubias prefers low to medium light"
            }
        }
    
    async def check_facts(self, content: str, topic: str) -> Dict[str, Any]:
        """Check factual accuracy of content"""
        
        result = {
            "accuracy_score": 0.8,  # Start with good score
            "issues": [],
            "suggestions": [],
            "verified_facts": [],
            "questionable_claims": []
        }
        
        content_lower = content.lower()
        
        # Check for common misconceptions
        misconception_issues = self._check_misconceptions(content_lower)
        result["issues"].extend(misconception_issues)
        
        # Check plant-specific facts
        plant_accuracy = await self._check_plant_facts(content_lower)
        result["accuracy_score"] = (result["accuracy_score"] + plant_accuracy["score"]) / 2
        result["issues"].extend(plant_accuracy["issues"])
        result["verified_facts"].extend(plant_accuracy["verified_facts"])
        
        # Check equipment facts
        equipment_accuracy = await self._check_equipment_facts(content_lower)
        result["accuracy_score"] = (result["accuracy_score"] + equipment_accuracy["score"]) / 2
        result["issues"].extend(equipment_accuracy["issues"])
        
        # Check water parameter claims
        parameter_accuracy = self._check_water_parameters(content_lower)
        result["accuracy_score"] = (result["accuracy_score"] + parameter_accuracy["score"]) / 2
        result["issues"].extend(parameter_accuracy["issues"])
        
        # Generate suggestions based on issues
        if result["issues"]:
            result["suggestions"] = self._generate_fact_suggestions(result["issues"])
        
        # Adjust score based on number of issues
        if len(result["issues"]) > 3:
            result["accuracy_score"] *= 0.7
        elif len(result["issues"]) > 1:
            result["accuracy_score"] *= 0.85
        
        return result
    
    def _check_misconceptions(self, content: str) -> List[str]:
        """Check for common aquascaping misconceptions"""
        issues = []
        
        # Check each known misconception
        for misconception_key, misconception_data in self.factual_corrections.items():
            error_pattern = misconception_data["error"]
            
            # Simple keyword-based checking
            if misconception_key == "anubias rhizome buried":
                if re.search(r"bury.*anubias.*rhizome|anubias.*rhizome.*buried", content):
                    issues.append(f"Factual error: {misconception_data['correction']}")
            
            elif misconception_key == "co2 for anubias":
                if re.search(r"anubias.*(?:requires?|needs?|must have).*co2", content):
                    issues.append(f"Factual error: {misconception_data['correction']}")
            
            elif misconception_key == "high light anubias":
                if re.search(r"anubias.*(?:needs?|requires?).*high.*light", content):
                    issues.append(f"Factual error: {misconception_data['correction']}")
        
        return issues
    
    async def _check_plant_facts(self, content: str) -> Dict[str, Any]:
        """Check plant-specific factual claims"""
        result = {
            "score": 0.8,
            "issues": [],
            "verified_facts": []
        }
        
        # Check facts for plants mentioned in content
        for plant_name, plant in self.knowledge_base.plants.items():
            if plant_name in content or plant.scientific_name.lower() in content:
                
                # Check light requirements
                if "light" in content:
                    light_patterns = [
                        rf"{plant_name}.*(?:requires?|needs?).*low.*light",
                        rf"{plant_name}.*(?:requires?|needs?).*medium.*light", 
                        rf"{plant_name}.*(?:requires?|needs?).*high.*light"
                    ]
                    
                    for i, pattern in enumerate(light_patterns):
                        if re.search(pattern, content):
                            claimed_light = ["low", "medium", "high"][i]
                            actual_light = plant.light_requirement
                            
                            if claimed_light in actual_light:
                                result["verified_facts"].append(
                                    f"Correct: {plant.name} light requirement"
                                )
                            else:
                                result["issues"].append(
                                    f"Incorrect light requirement for {plant.name}: "
                                    f"claimed {claimed_light}, actual {actual_light}"
                                )
                                result["score"] -= 0.1
                
                # Check CO2 requirements
                if "co2" in content:
                    if plant.co2_requirement == "none":
                        if re.search(rf"{plant_name}.*(?:requires?|needs?).*co2", content):
                            result["issues"].append(
                                f"Incorrect: {plant.name} does not require CO2"
                            )
                            result["score"] -= 0.15
                        else:
                            result["verified_facts"].append(
                                f"Correct: {plant.name} CO2 requirement"
                            )
                
                # Check difficulty level
                difficulty_patterns = [
                    rf"{plant_name}.*(?:is|are).*beginner",
                    rf"{plant_name}.*(?:is|are).*intermediate",
                    rf"{plant_name}.*(?:is|are).*advanced"
                ]
                
                for i, pattern in enumerate(difficulty_patterns):
                    if re.search(pattern, content):
                        claimed_difficulty = ["beginner", "intermediate", "advanced"][i]
                        actual_difficulty = plant.difficulty.value
                        
                        if claimed_difficulty == actual_difficulty:
                            result["verified_facts"].append(
                                f"Correct: {plant.name} difficulty level"
                            )
                        else:
                            result["issues"].append(
                                f"Incorrect difficulty for {plant.name}: "
                                f"claimed {claimed_difficulty}, actual {actual_difficulty}"
                            )
                            result["score"] -= 0.1
        
        return result
    
    async def _check_equipment_facts(self, content: str) -> Dict[str, Any]:
        """Check equipment-related factual claims"""
        result = {
            "score": 0.8,
            "issues": []
        }
        
        # Check equipment recommendations
        for equipment_name, equipment in self.knowledge_base.equipment.items():
            if equipment_name in content:
                
                # Check if claimed benefits match known pros
                if equipment.pros:
                    for pro in equipment.pros:
                        if pro.lower() in content:
                            # Positive verification - equipment benefit mentioned correctly
                            continue
                
                # Check for claims that contradict known cons
                if equipment.cons:
                    for con in equipment.cons:
                        # Look for claims that contradict known limitations
                        opposite_claim = self._get_opposite_claim(con)
                        if opposite_claim and opposite_claim in content:
                            result["issues"].append(
                                f"Questionable claim about {equipment.name}: "
                                f"content claims {opposite_claim} but known issue is {con}"
                            )
                            result["score"] -= 0.1
        
        return result
    
    def _check_water_parameters(self, content: str) -> Dict[str, Any]:
        """Check water parameter claims"""
        result = {
            "score": 0.8,
            "issues": []
        }
        
        # Check pH claims
        ph_matches = re.findall(r"ph\s+(?:of\s+)?(\d+\.?\d*)\s*-?\s*(\d+\.?\d*)?", content)
        for match in ph_matches:
            ph_low = float(match[0])
            ph_high = float(match[1]) if match[1] else ph_low
            
            # Check for reasonable pH ranges
            if ph_low < 4.0 or ph_high > 9.0:
                result["issues"].append(
                    f"Unusual pH range: {ph_low}-{ph_high}. "
                    "Most aquatic plants prefer pH 6.0-8.0"
                )
                result["score"] -= 0.1
            
            if ph_low > ph_high:
                result["issues"].append("Invalid pH range: minimum higher than maximum")
                result["score"] -= 0.15
        
        # Check temperature claims
        temp_matches = re.findall(
            r"temperature\s+(?:of\s+)?(\d+)\s*-?\s*(\d+)?\s*°?[cf]", 
            content
        )
        for match in temp_matches:
            temp_low = int(match[0])
            temp_high = int(match[1]) if match[1] else temp_low
            
            # Assume Celsius if reasonable range, Fahrenheit otherwise
            if temp_low > 50:  # Likely Fahrenheit
                # Convert to Celsius for validation
                temp_low_c = (temp_low - 32) * 5/9
                temp_high_c = (temp_high - 32) * 5/9 if temp_high != temp_low else temp_low_c
            else:
                temp_low_c = temp_low
                temp_high_c = temp_high
            
            # Check for reasonable temperature ranges (most tropical aquariums)
            if temp_low_c < 18 or temp_high_c > 32:
                result["issues"].append(
                    f"Unusual temperature range: {temp_low}-{temp_high}. "
                    "Most tropical aquariums are 22-28°C (72-82°F)"
                )
                result["score"] -= 0.1
        
        return result
    
    def _get_opposite_claim(self, con: str) -> Optional[str]:
        """Get opposite claim for a known limitation"""
        # Simple mapping of cons to opposite claims
        opposites = {
            "expensive": "cheap",
            "difficult to maintain": "easy to maintain",
            "requires high light": "works in low light",
            "needs co2": "doesn't need co2"
        }
        
        for con_key, opposite in opposites.items():
            if con_key in con.lower():
                return opposite
        
        return None
    
    def _check_light_requirement(self, plant_name: str, requirement: str) -> bool:
        """Check if plant light requirement claim is accurate"""
        plant = self.knowledge_base.plants.get(plant_name.lower())
        if plant:
            return requirement.lower() in plant.light_requirement.lower()
        return True  # Benefit of doubt if plant not in database
    
    def _check_co2_requirement(self, plant_name: str, needs_co2: bool) -> bool:
        """Check if plant CO2 requirement claim is accurate"""
        plant = self.knowledge_base.plants.get(plant_name.lower())
        if plant:
            if needs_co2:
                return plant.co2_requirement != "none"
            else:
                return plant.co2_requirement == "none"
        return True
    
    def _check_growth_rate(self, plant_name: str, growth_rate: str) -> bool:
        """Check if plant growth rate claim is accurate"""
        plant = self.knowledge_base.plants.get(plant_name.lower())
        if plant:
            return growth_rate.lower() == plant.growth_rate.lower()
        return True
    
    def _check_difficulty(self, plant_name: str, difficulty: str) -> bool:
        """Check if plant difficulty claim is accurate"""
        plant = self.knowledge_base.plants.get(plant_name.lower())
        if plant:
            return difficulty.lower() == plant.difficulty.value.lower()
        return True
    
    def _check_ph_range(self, ph_low: str, ph_high: Optional[str]) -> bool:
        """Check if pH range is reasonable"""
        try:
            low = float(ph_low)
            high = float(ph_high) if ph_high else low
            
            # Most aquatic plants do well in pH 6.0-8.0
            return 4.0 <= low <= 9.0 and 4.0 <= high <= 9.0 and low <= high
        except ValueError:
            return False
    
    def _check_temperature_range(self, temp_low: str, temp_high: Optional[str]) -> bool:
        """Check if temperature range is reasonable"""
        try:
            low = int(temp_low)
            high = int(temp_high) if temp_high else low
            
            # Check both Celsius and Fahrenheit ranges
            if low <= 40:  # Likely Celsius
                return 15 <= low <= 35 and 15 <= high <= 35 and low <= high
            else:  # Likely Fahrenheit
                return 60 <= low <= 95 and 60 <= high <= 95 and low <= high
        except ValueError:
            return False
    
    def _check_lighting_recommendation(self, light_name: str) -> bool:
        """Check if lighting recommendation is reasonable"""
        # This would be expanded with actual lighting database
        known_good_lights = ["chihiros", "fluval", "nicrew", "finnex", "current"]
        return any(brand in light_name.lower() for brand in known_good_lights)
    
    def _check_substrate_recommendation(self, substrate_name: str) -> bool:
        """Check if substrate recommendation is reasonable"""
        # This would be expanded with actual substrate database
        known_substrates = ["ada", "fluval", "seachem", "tropica", "aquasoil"]
        return any(brand in substrate_name.lower() for brand in known_substrates)
    
    def _generate_fact_suggestions(self, issues: List[str]) -> List[str]:
        """Generate suggestions based on factual issues found"""
        suggestions = []
        
        if any("light" in issue.lower() for issue in issues):
            suggestions.append("Verify plant light requirements against reliable sources")
        
        if any("co2" in issue.lower() for issue in issues):
            suggestions.append("Double-check CO2 requirements for mentioned plants")
        
        if any("ph" in issue.lower() or "temperature" in issue.lower() for issue in issues):
            suggestions.append("Verify water parameter ranges are appropriate for mentioned species")
        
        if any("difficulty" in issue.lower() for issue in issues):
            suggestions.append("Confirm plant difficulty ratings match established classifications")
        
        if len(issues) > 2:
            suggestions.append("Consider reviewing content with aquascaping expert for accuracy")
        
        return suggestions