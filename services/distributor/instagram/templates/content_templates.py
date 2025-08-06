"""
Standardized Content Templates for Aquascaping Instagram Posts
Provides pre-defined templates for different types of aquascaping content with Bulgarian and English variations.
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from ..api.instagram_client import InstagramPost, MediaType
from ..scheduler.content_scheduler import PostType
from ..utils.hashtag_optimizer import ContentCategory


class Language(Enum):
    ENGLISH = "en"
    BULGARIAN = "bg"
    BILINGUAL = "bilingual"


class CallToActionType(Enum):
    ENGAGEMENT = "engagement"  # Like, comment, share
    EDUCATIONAL = "educational"  # Learn more, try this
    COMMUNITY = "community"  # Tag a friend, share experience
    BRAND = "brand"  # Visit website, follow
    QUESTION = "question"  # Ask for opinions


@dataclass
class ContentTemplate:
    """Template for generating Instagram posts"""
    id: str
    name: str
    post_type: PostType
    language: Language
    caption_template: str
    hashtag_categories: List[str]
    call_to_action: CallToActionType
    media_requirements: Dict[str, any]
    variables: List[str]  # Variables that need to be filled
    performance_score: float = 0.0
    usage_count: int = 0


class AquascapingContentTemplates:
    """
    Collection of standardized content templates for aquascaping posts.
    """
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.placeholders = self._initialize_placeholders()
    
    def _initialize_templates(self) -> Dict[str, ContentTemplate]:
        """Initialize all content templates"""
        
        templates = {}
        
        # Educational Carousel Templates
        templates.update(self._create_educational_templates())
        
        # Showcase Templates
        templates.update(self._create_showcase_templates())
        
        # Tutorial Templates
        templates.update(self._create_tutorial_templates())
        
        # Plant Spotlight Templates
        templates.update(self._create_plant_spotlight_templates())
        
        # Fish Spotlight Templates
        templates.update(self._create_fish_spotlight_templates())
        
        # Community Templates
        templates.update(self._create_community_templates())
        
        # Behind the Scenes Templates
        templates.update(self._create_behind_scenes_templates())
        
        # Partnership Templates
        templates.update(self._create_partnership_templates())
        
        return templates
    
    def _create_educational_templates(self) -> Dict[str, ContentTemplate]:
        """Create educational content templates"""
        
        templates = {}
        
        # English Educational Templates
        templates["edu_beginner_guide_en"] = ContentTemplate(
            id="edu_beginner_guide_en",
            name="Beginner's Guide - English",
            post_type=PostType.EDUCATIONAL,
            language=Language.ENGLISH,
            caption_template="""🌱 {title} - A Beginner's Guide

{introduction}

Here's what you need to know:

✅ {tip_1}
✅ {tip_2}
✅ {tip_3}
✅ {tip_4}

💡 Pro tip: {pro_tip}

{question_cta}

Share this with someone starting their aquascaping journey! 

#AquaScene #BeginnerFriendly""",
            hashtag_categories=["educational", "beginner", "aquascaping", "international"],
            call_to_action=CallToActionType.EDUCATIONAL,
            media_requirements={"type": "carousel", "min_images": 3, "max_images": 8},
            variables=["title", "introduction", "tip_1", "tip_2", "tip_3", "tip_4", "pro_tip", "question_cta"]
        )
        
        # Bulgarian Educational Templates
        templates["edu_beginner_guide_bg"] = ContentTemplate(
            id="edu_beginner_guide_bg",
            name="Ръководство за начинаещи - Български",
            post_type=PostType.EDUCATIONAL,
            language=Language.BULGARIAN,
            caption_template="""🌱 {title} - Ръководство за начинаещи

{introduction}

Ето какво трябва да знаете:

✅ {tip_1}
✅ {tip_2}
✅ {tip_3}
✅ {tip_4}

💡 Професионален съвет: {pro_tip}

{question_cta}

Споделете с някой, който започва своето пътешествие в акваскейпинга! 

#AquaScene #ЗаНачинаещи""",
            hashtag_categories=["educational", "beginner", "aquascaping", "bulgarian"],
            call_to_action=CallToActionType.EDUCATIONAL,
            media_requirements={"type": "carousel", "min_images": 3, "max_images": 8},
            variables=["title", "introduction", "tip_1", "tip_2", "tip_3", "tip_4", "pro_tip", "question_cta"]
        )
        
        return templates
    
    def _create_showcase_templates(self) -> Dict[str, ContentTemplate]:
        """Create showcase content templates"""
        
        templates = {}
        
        # English Showcase Templates
        templates["showcase_transformation_en"] = ContentTemplate(
            id="showcase_transformation_en",
            name="Aquascape Transformation - English",
            post_type=PostType.SHOWCASE,
            language=Language.ENGLISH,
            caption_template="""✨ {tank_size} Aquascape Transformation ✨

{description}

🌿 Featured Plants:
{plant_list}

🐟 Fish Community:
{fish_list}

⚙️ Equipment Used:
{equipment_list}

{transformation_story}

What do you think of this transformation? Let me know in the comments! 👇

#AquascapeTransformation #PlantedTank""",
            hashtag_categories=["showcase", "transformation", "aquascaping", "international"],
            call_to_action=CallToActionType.ENGAGEMENT,
            media_requirements={"type": "single_image", "before_after": True},
            variables=["tank_size", "description", "plant_list", "fish_list", "equipment_list", "transformation_story"]
        )
        
        # Bulgarian Showcase Templates
        templates["showcase_transformation_bg"] = ContentTemplate(
            id="showcase_transformation_bg",
            name="Трансформация на акваскейп - Български",
            post_type=PostType.SHOWCASE,
            language=Language.BULGARIAN,
            caption_template="""✨ Трансформация на {tank_size} акваскейп ✨

{description}

🌿 Представени растения:
{plant_list}

🐟 Рибна общност:
{fish_list}

⚙️ Използвано оборудване:
{equipment_list}

{transformation_story}

Какво мислите за тази трансформация? Споделете в коментарите! 👇

#ТрансформацияНаАкваскейп #РастителенАквариум""",
            hashtag_categories=["showcase", "transformation", "aquascaping", "bulgarian"],
            call_to_action=CallToActionType.ENGAGEMENT,
            media_requirements={"type": "single_image", "before_after": True},
            variables=["tank_size", "description", "plant_list", "fish_list", "equipment_list", "transformation_story"]
        )
        
        return templates
    
    def _create_tutorial_templates(self) -> Dict[str, ContentTemplate]:
        """Create tutorial content templates"""
        
        templates = {}
        
        # Step-by-step Tutorial Template (English)
        templates["tutorial_step_by_step_en"] = ContentTemplate(
            id="tutorial_step_by_step_en",
            name="Step-by-Step Tutorial - English",
            post_type=PostType.TUTORIAL,
            language=Language.ENGLISH,
            caption_template="""📋 How to: {tutorial_title}

{introduction}

Step-by-step process:

1️⃣ {step_1}
2️⃣ {step_2}
3️⃣ {step_3}
4️⃣ {step_4}
5️⃣ {step_5}

⚠️ Important Notes:
• {important_note_1}
• {important_note_2}

💡 {additional_tip}

Have you tried this technique? Share your results below! 

Save this post for later reference 📌

#HowTo #AquascapingTutorial""",
            hashtag_categories=["tutorial", "howto", "educational", "international"],
            call_to_action=CallToActionType.EDUCATIONAL,
            media_requirements={"type": "carousel", "min_images": 5, "max_images": 10},
            variables=["tutorial_title", "introduction", "step_1", "step_2", "step_3", "step_4", "step_5", 
                      "important_note_1", "important_note_2", "additional_tip"]
        )
        
        # Bulgarian Tutorial Template
        templates["tutorial_step_by_step_bg"] = ContentTemplate(
            id="tutorial_step_by_step_bg",
            name="Стъпка по стъпка урок - Български",
            post_type=PostType.TUTORIAL,
            language=Language.BULGARIAN,
            caption_template="""📋 Как да: {tutorial_title}

{introduction}

Процес стъпка по стъпка:

1️⃣ {step_1}
2️⃣ {step_2}
3️⃣ {step_3}
4️⃣ {step_4}
5️⃣ {step_5}

⚠️ Важни бележки:
• {important_note_1}
• {important_note_2}

💡 {additional_tip}

Пробвали ли сте тази техника? Споделете резултатите си по-долу! 

Запазете тази публикация за по-късно 📌

#КакДа #УрокПоАкваскейпинг""",
            hashtag_categories=["tutorial", "howto", "educational", "bulgarian"],
            call_to_action=CallToActionType.EDUCATIONAL,
            media_requirements={"type": "carousel", "min_images": 5, "max_images": 10},
            variables=["tutorial_title", "introduction", "step_1", "step_2", "step_3", "step_4", "step_5", 
                      "important_note_1", "important_note_2", "additional_tip"]
        )
        
        return templates
    
    def _create_plant_spotlight_templates(self) -> Dict[str, ContentTemplate]:
        """Create plant spotlight templates"""
        
        templates = {}
        
        # English Plant Spotlight
        templates["plant_spotlight_en"] = ContentTemplate(
            id="plant_spotlight_en",
            name="Plant Spotlight - English",
            post_type=PostType.SHOWCASE,
            language=Language.ENGLISH,
            caption_template="""🌿 Plant Spotlight: {plant_name}

{plant_description}

📊 Care Requirements:
💡 Lighting: {lighting_requirement}
🌡️ Temperature: {temperature_range}
📏 Size: {plant_size}
⭐ Difficulty: {difficulty_level}
💨 CO₂: {co2_requirement}

🔬 Scientific Name: {scientific_name}

💡 Pro Tips:
• {tip_1}
• {tip_2}
• {tip_3}

{personal_experience}

Do you have this plant in your aquascape? Share your experience! 

#PlantSpotlight #AquariumPlants""",
            hashtag_categories=["plants", "spotlight", "aquascaping", "international"],
            call_to_action=CallToActionType.COMMUNITY,
            media_requirements={"type": "single_image", "focus": "plant_closeup"},
            variables=["plant_name", "plant_description", "lighting_requirement", "temperature_range", 
                      "plant_size", "difficulty_level", "co2_requirement", "scientific_name",
                      "tip_1", "tip_2", "tip_3", "personal_experience"]
        )
        
        # Bulgarian Plant Spotlight
        templates["plant_spotlight_bg"] = ContentTemplate(
            id="plant_spotlight_bg",
            name="Акцент върху растението - Български",
            post_type=PostType.SHOWCASE,
            language=Language.BULGARIAN,
            caption_template="""🌿 Акцент върху растението: {plant_name}

{plant_description}

📊 Изисквания за отглеждане:
💡 Осветление: {lighting_requirement}
🌡️ Температура: {temperature_range}
📏 Размер: {plant_size}
⭐ Трудност: {difficulty_level}
💨 CO₂: {co2_requirement}

🔬 Научно име: {scientific_name}

💡 Професионални съвети:
• {tip_1}
• {tip_2}
• {tip_3}

{personal_experience}

Имате ли това растение в акваскейпа си? Споделете опита си! 

#АкцентВърхуРастението #АквариумниРастения""",
            hashtag_categories=["plants", "spotlight", "aquascaping", "bulgarian"],
            call_to_action=CallToActionType.COMMUNITY,
            media_requirements={"type": "single_image", "focus": "plant_closeup"},
            variables=["plant_name", "plant_description", "lighting_requirement", "temperature_range", 
                      "plant_size", "difficulty_level", "co2_requirement", "scientific_name",
                      "tip_1", "tip_2", "tip_3", "personal_experience"]
        )
        
        return templates
    
    def _create_fish_spotlight_templates(self) -> Dict[str, ContentTemplate]:
        """Create fish spotlight templates"""
        
        templates = {}
        
        templates["fish_spotlight_en"] = ContentTemplate(
            id="fish_spotlight_en",
            name="Fish Spotlight - English",
            post_type=PostType.SHOWCASE,
            language=Language.ENGLISH,
            caption_template="""🐟 Fish Spotlight: {fish_name}

{fish_description}

📊 Care Information:
🌡️ Temperature: {temperature_range}
📐 Tank Size: {minimum_tank_size}
🍽️ Diet: {diet_type}
👥 Social: {social_behavior}
⭐ Care Level: {care_difficulty}

🎨 Perfect for aquascapes because:
• {aquascape_benefit_1}
• {aquascape_benefit_2}
• {aquascape_benefit_3}

🤝 Best Tank Mates:
{compatible_species}

{care_tips}

Who else loves keeping {fish_name}? Share your photos! 📸

#FishSpotlight #AquascapeFish""",
            hashtag_categories=["fish", "spotlight", "aquascaping", "international"],
            call_to_action=CallToActionType.COMMUNITY,
            media_requirements={"type": "single_image", "focus": "fish_portrait"},
            variables=["fish_name", "fish_description", "temperature_range", "minimum_tank_size",
                      "diet_type", "social_behavior", "care_difficulty", "aquascape_benefit_1",
                      "aquascape_benefit_2", "aquascape_benefit_3", "compatible_species", "care_tips"]
        )
        
        return templates
    
    def _create_community_templates(self) -> Dict[str, ContentTemplate]:
        """Create community engagement templates"""
        
        templates = {}
        
        templates["community_showcase_en"] = ContentTemplate(
            id="community_showcase_en",
            name="Community Showcase - English",
            post_type=PostType.COMMUNITY,
            language=Language.ENGLISH,
            caption_template="""🌟 Community Showcase 🌟

Featured Aquascaper: @{featured_user}

{showcase_description}

What we love about this setup:
✨ {highlight_1}
✨ {highlight_2}
✨ {highlight_3}

Tank Details:
📏 Size: {tank_specifications}
🌿 Plants: {plant_highlights}
🐟 Fish: {fish_highlights}

{inspiration_message}

Want to be featured? Tag us in your aquascape photos! 

Congratulations @{featured_user}! 🎉

#CommunitySpotlight #AquascapeFeature""",
            hashtag_categories=["community", "feature", "showcase", "international"],
            call_to_action=CallToActionType.COMMUNITY,
            media_requirements={"type": "single_image", "credit_required": True},
            variables=["featured_user", "showcase_description", "highlight_1", "highlight_2", "highlight_3",
                      "tank_specifications", "plant_highlights", "fish_highlights", "inspiration_message"]
        )
        
        return templates
    
    def _create_behind_scenes_templates(self) -> Dict[str, ContentTemplate]:
        """Create behind-the-scenes templates"""
        
        templates = {}
        
        templates["behind_scenes_en"] = ContentTemplate(
            id="behind_scenes_en",
            name="Behind the Scenes - English",
            post_type=PostType.BEHIND_SCENES,
            language=Language.ENGLISH,
            caption_template="""🎬 Behind the Scenes: {activity_title}

{activity_description}

Today's process:
🔧 {process_step_1}
🔧 {process_step_2}
🔧 {process_step_3}

💭 What I learned:
{lesson_learned}

🤔 Challenges faced:
{challenge_description}

💡 Next steps:
{next_steps}

{personal_reflection}

What would you like to see more behind-the-scenes content about? 

#BehindTheScenes #AquascapeLife""",
            hashtag_categories=["behind_scenes", "process", "personal", "international"],
            call_to_action=CallToActionType.QUESTION,
            media_requirements={"type": "carousel", "candid_photos": True},
            variables=["activity_title", "activity_description", "process_step_1", "process_step_2",
                      "process_step_3", "lesson_learned", "challenge_description", "next_steps", "personal_reflection"]
        )
        
        return templates
    
    def _create_partnership_templates(self) -> Dict[str, ContentTemplate]:
        """Create partnership content templates"""
        
        templates = {}
        
        templates["partnership_product_en"] = ContentTemplate(
            id="partnership_product_en",
            name="Partnership Product Feature - English",
            post_type=PostType.PARTNERSHIP,
            language=Language.ENGLISH,
            caption_template="""🤝 Partnership Feature: {product_name}

{product_introduction}

Why we're excited about this collaboration:
✅ {partnership_reason_1}
✅ {partnership_reason_2}
✅ {partnership_reason_3}

📦 Product Highlights:
• {feature_1}
• {feature_2}
• {feature_3}

🔍 Our Experience:
{personal_experience}

💰 Special Offer:
{special_offer_details}

Thank you @{partner_brand} for this amazing collaboration! 

{call_to_action_text}

#Partnership #AquascapeGear
""",
            hashtag_categories=["partnership", "collaboration", "products", "international"],
            call_to_action=CallToActionType.BRAND,
            media_requirements={"type": "carousel", "product_focus": True, "partnership_disclosure": True},
            variables=["product_name", "product_introduction", "partnership_reason_1", "partnership_reason_2",
                      "partnership_reason_3", "feature_1", "feature_2", "feature_3", "personal_experience",
                      "special_offer_details", "partner_brand", "call_to_action_text"]
        )
        
        return templates
    
    def _initialize_placeholders(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize placeholder content for templates"""
        
        return {
            "call_to_actions": {
                "engagement": {
                    "en": [
                        "What do you think? Let me know in the comments! 👇",
                        "Share your thoughts below! 💬",
                        "Double tap if you love this setup! ❤️",
                        "Tag someone who would love this! 👆"
                    ],
                    "bg": [
                        "Какво мислите? Споделете в коментарите! 👇",
                        "Споделете мнението си по-долу! 💬",
                        "Двойно докоснете, ако харесвате тази настройка! ❤️",
                        "Отбележете някой, който би харесал това! 👆"
                    ]
                },
                "educational": {
                    "en": [
                        "Save this post for future reference! 📌",
                        "Try this technique and let us know how it goes! 🌱",
                        "Which tip was most helpful? Comment below! 💡",
                        "Share this with someone who's learning aquascaping! 📚"
                    ],
                    "bg": [
                        "Запазете тази публикация за бъдеща справка! 📌",
                        "Опитайте тази техника и ни кажете как върви! 🌱",
                        "Кой съвет беше най-полезен? Коментирайте по-долу! 💡",
                        "Споделете това с някой, който учи акваскейпинг! 📚"
                    ]
                },
                "community": {
                    "en": [
                        "Tag a fellow aquascaper! 👥",
                        "Share your setup in the comments! 📸",
                        "What's your experience with this? 🤔",
                        "Join the conversation below! 💬"
                    ],
                    "bg": [
                        "Отбележете колега акваскейпър! 👥",
                        "Споделете вашата настройка в коментарите! 📸",
                        "Какъв е вашият опит с това? 🤔",
                        "Присъединете се към разговора по-долу! 💬"
                    ]
                }
            },
            "questions": {
                "en": [
                    "What's your biggest aquascaping challenge?",
                    "Which plant is your favorite for beginners?",
                    "How long have you been aquascaping?",
                    "What would you like to learn next?",
                    "Share your best aquascaping tip!",
                    "What's your dream aquascape setup?"
                ],
                "bg": [
                    "Какво е най-голямото ви предизвикателство в акваскейпинга?",
                    "Кое растение е любимото ви за начинаещи?",
                    "От колко време се занимавате с акваскейпинг?",
                    "Какво бихте искали да научите следващо?",
                    "Споделете най-добрия си съвет за акваскейпинг!",
                    "Каква е мечтаната ви акваскейп настройка?"
                ]
            }
        }
    
    def get_template(self, template_id: str) -> Optional[ContentTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def get_templates_by_type(self, post_type: PostType) -> List[ContentTemplate]:
        """Get all templates for a specific post type"""
        return [template for template in self.templates.values() 
                if template.post_type == post_type]
    
    def get_templates_by_language(self, language: Language) -> List[ContentTemplate]:
        """Get all templates for a specific language"""
        return [template for template in self.templates.values() 
                if template.language == language]
    
    def fill_template(self, template_id: str, variables: Dict[str, str], 
                     auto_fill_missing: bool = True) -> Optional[str]:
        """
        Fill template with provided variables.
        Auto-fills missing variables with placeholders if enabled.
        """
        
        template = self.get_template(template_id)
        if not template:
            return None
        
        caption = template.caption_template
        
        # Fill provided variables
        for var_name, var_value in variables.items():
            placeholder = "{" + var_name + "}"
            caption = caption.replace(placeholder, str(var_value))
        
        # Auto-fill missing variables if enabled
        if auto_fill_missing:
            caption = self._auto_fill_missing_variables(caption, template)
        
        return caption
    
    def _auto_fill_missing_variables(self, caption: str, template: ContentTemplate) -> str:
        """Auto-fill missing template variables with appropriate placeholders"""
        
        import re
        
        # Find remaining placeholders
        placeholders = re.findall(r'\{(\w+)\}', caption)
        
        for placeholder in placeholders:
            if placeholder == "question_cta":
                # Fill with random question
                questions = self.placeholders["questions"][template.language.value]
                question = random.choice(questions)
                caption = caption.replace(f"{{{placeholder}}}", question)
            
            elif "cta" in placeholder or "call_to_action" in placeholder:
                # Fill with appropriate call to action
                cta_type = template.call_to_action.value
                language = template.language.value
                
                if cta_type in self.placeholders["call_to_actions"] and language in self.placeholders["call_to_actions"][cta_type]:
                    cta = random.choice(self.placeholders["call_to_actions"][cta_type][language])
                    caption = caption.replace(f"{{{placeholder}}}", cta)
                else:
                    caption = caption.replace(f"{{{placeholder}}}", "")
            
            else:
                # Replace with placeholder text
                caption = caption.replace(f"{{{placeholder}}}", f"[{placeholder.upper()}]")
        
        return caption
    
    def generate_post_from_template(self, template_id: str, variables: Dict[str, str],
                                  media_url: str = None, media_urls: List[str] = None) -> Optional[InstagramPost]:
        """Generate complete Instagram post from template"""
        
        template = self.get_template(template_id)
        if not template:
            return None
        
        # Fill caption template
        caption = self.fill_template(template_id, variables)
        if not caption:
            return None
        
        # Determine media type based on template requirements
        media_reqs = template.media_requirements
        
        if media_reqs.get("type") == "carousel":
            media_type = MediaType.CAROUSEL_ALBUM
            if not media_urls or len(media_urls) < media_reqs.get("min_images", 2):
                return None
        else:
            media_type = MediaType.IMAGE
            if not media_url:
                return None
        
        # Generate hashtags (would integrate with hashtag optimizer)
        hashtags = self._generate_template_hashtags(template)
        
        return InstagramPost(
            caption=caption,
            media_type=media_type,
            media_url=media_url,
            media_urls=media_urls,
            hashtags=hashtags
        )
    
    def _generate_template_hashtags(self, template: ContentTemplate) -> List[str]:
        """Generate hashtags based on template categories"""
        
        # Basic hashtag mapping - would integrate with hashtag optimizer
        hashtag_mapping = {
            "educational": ["educational", "tips", "howto", "learning"],
            "beginner": ["beginner", "newbie", "starter", "beginnerfriendly"],
            "aquascaping": ["aquascaping", "aquascape", "plantedtank", "aquarium"],
            "showcase": ["showcase", "featured", "beautiful", "stunning"],
            "plants": ["aquariumplants", "plantspotlight", "aquaticplants"],
            "fish": ["aquariumfish", "fishkeeping", "tropical"],
            "community": ["community", "aquascapecommunity", "sharing"],
            "international": ["nature", "peaceful", "zen", "green"],
            "bulgarian": ["аквариум", "растения", "акваскейп", "природа"],
            "partnership": ["collaboration", "partnership", "sponsored"]
        }
        
        hashtags = []
        for category in template.hashtag_categories:
            if category in hashtag_mapping:
                hashtags.extend(hashtag_mapping[category])
        
        # Add template-specific hashtags
        hashtags.append("aquascene")
        if template.language == Language.BULGARIAN:
            hashtags.append("акваскейнбг")
        
        return hashtags[:25]  # Limit to 25 hashtags
    
    def get_template_suggestions(self, post_type: PostType, language: Language) -> List[str]:
        """Get template suggestions for given criteria"""
        
        matching_templates = [
            template for template in self.templates.values()
            if template.post_type == post_type and 
               (template.language == language or template.language == Language.BILINGUAL)
        ]
        
        # Sort by performance score and usage count
        matching_templates.sort(key=lambda t: (t.performance_score, -t.usage_count), reverse=True)
        
        return [template.id for template in matching_templates]


# Usage example
if __name__ == "__main__":
    
    # Initialize template system
    templates = AquascapingContentTemplates()
    
    # Get all educational templates
    educational_templates = templates.get_templates_by_type(PostType.EDUCATIONAL)
    print(f"Educational templates: {len(educational_templates)}")
    
    # Fill a template
    variables = {
        "title": "Lighting Setup",
        "introduction": "Proper lighting is crucial for plant growth in aquascapes.",
        "tip_1": "Use full spectrum LED lights",
        "tip_2": "Maintain 8-10 hours of lighting daily",
        "tip_3": "Adjust intensity based on plant requirements",
        "tip_4": "Consider CO2 supplementation with high light",
        "pro_tip": "Start with lower intensity and gradually increase"
    }
    
    filled_caption = templates.fill_template("edu_beginner_guide_en", variables)
    print("Filled template:")
    print(filled_caption)
    
    # Generate complete post
    post = templates.generate_post_from_template(
        "edu_beginner_guide_en",
        variables,
        media_urls=["https://example.com/img1.jpg", "https://example.com/img2.jpg", "https://example.com/img3.jpg"]
    )
    
    if post:
        print(f"\nGenerated post:")
        print(f"Caption length: {len(post.caption)}")
        print(f"Media type: {post.media_type}")
        print(f"Hashtags: {len(post.hashtags) if post.hashtags else 0}")