"""
Visual Template Generator for Instagram Posts
Creates branded templates for different aquascaping content types using Pillow.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import requests
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import textwrap
import os
import json
from pathlib import Path


class TemplateType(Enum):
    EDUCATIONAL_CAROUSEL = "educational_carousel"
    BEFORE_AFTER = "before_after"
    PLANT_SPOTLIGHT = "plant_spotlight"
    FISH_SPOTLIGHT = "fish_spotlight"
    TUTORIAL_STEP = "tutorial_step"
    COMMUNITY_FEATURE = "community_feature"
    BEHIND_SCENES = "behind_scenes"
    PARTNERSHIP = "partnership"
    QUOTE_CARD = "quote_card"
    TIPS_CARD = "tips_card"


@dataclass
class BrandColors:
    """Brand color palette for AquaScene"""
    primary: str = "#2E8B57"  # Sea Green
    secondary: str = "#20B2AA"  # Light Sea Green
    accent: str = "#FFD700"  # Gold
    text_dark: str = "#1C3A3A"  # Dark Teal
    text_light: str = "#FFFFFF"  # White
    background: str = "#F0F8F8"  # Light Cyan
    overlay: str = "#000000"  # Black for overlays


@dataclass
class TemplateConfig:
    """Configuration for template generation"""
    width: int = 1080
    height: int = 1080
    margin: int = 60
    brand_colors: BrandColors = None
    font_sizes: Dict[str, int] = None
    
    def __post_init__(self):
        if self.brand_colors is None:
            self.brand_colors = BrandColors()
        
        if self.font_sizes is None:
            self.font_sizes = {
                'title': 48,
                'subtitle': 36,
                'body': 28,
                'caption': 24,
                'small': 20
            }


class FontManager:
    """Manages font loading and fallbacks"""
    
    def __init__(self):
        self.fonts = {}
        self.font_paths = self._get_font_paths()
    
    def _get_font_paths(self) -> Dict[str, str]:
        """Get available system font paths"""
        font_paths = {
            'regular': None,
            'bold': None,
            'italic': None
        }
        
        # Common font locations
        common_fonts = [
            # macOS
            '/System/Library/Fonts/Arial.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
            # Linux
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            # Windows
            'C:/Windows/Fonts/arial.ttf',
        ]
        
        for font_path in common_fonts:
            if os.path.exists(font_path):
                font_paths['regular'] = font_path
                break
        
        return font_paths
    
    def get_font(self, size: int, style: str = 'regular') -> ImageFont.ImageFont:
        """Get font with specified size and style"""
        font_key = f"{style}_{size}"
        
        if font_key not in self.fonts:
            font_path = self.font_paths.get(style) or self.font_paths.get('regular')
            
            try:
                if font_path and os.path.exists(font_path):
                    self.fonts[font_key] = ImageFont.truetype(font_path, size)
                else:
                    # Fallback to default font
                    self.fonts[font_key] = ImageFont.load_default()
            except Exception:
                self.fonts[font_key] = ImageFont.load_default()
        
        return self.fonts[font_key]


class VisualTemplateGenerator:
    """
    Main class for generating Instagram visual templates.
    """
    
    def __init__(self, config: TemplateConfig = None):
        self.config = config or TemplateConfig()
        self.font_manager = FontManager()
        self.brand_colors = self.config.brand_colors
    
    def create_educational_carousel(self, content: Dict) -> List[Image.Image]:
        """
        Create educational carousel slides.
        Expected content format:
        {
            'title': str,
            'slides': [
                {'title': str, 'content': str, 'image_url': str (optional)},
                ...
            ]
        }
        """
        slides = []
        
        # Title slide
        title_slide = self._create_title_slide(
            content['title'],
            subtitle="Educational Series",
            template_type=TemplateType.EDUCATIONAL_CAROUSEL
        )
        slides.append(title_slide)
        
        # Content slides
        for i, slide_content in enumerate(content['slides'], 1):
            slide = self._create_content_slide(
                title=slide_content['title'],
                content=slide_content['content'],
                slide_number=f"{i}/{len(content['slides'])}",
                image_url=slide_content.get('image_url'),
                template_type=TemplateType.EDUCATIONAL_CAROUSEL
            )
            slides.append(slide)
        
        return slides
    
    def create_before_after(self, before_image_url: str, after_image_url: str, 
                           title: str, description: str = None) -> Image.Image:
        """Create before/after comparison template"""
        
        # Create base canvas
        canvas = Image.new('RGB', (self.config.width, self.config.height), 
                          self.brand_colors.background)
        draw = ImageDraw.Draw(canvas)
        
        # Download and process images
        before_img = self._download_and_resize_image(before_image_url, (400, 400))
        after_img = self._download_and_resize_image(after_image_url, (400, 400))
        
        # Position images side by side with labels
        y_offset = 200
        
        # Before image
        before_x = 100
        canvas.paste(before_img, (before_x, y_offset))
        
        # "BEFORE" label
        before_font = self.font_manager.get_font(self.config.font_sizes['caption'], 'bold')
        draw.text((before_x + 200, y_offset - 40), "BEFORE", 
                 fill=self.brand_colors.text_dark, font=before_font, anchor="mm")
        
        # After image
        after_x = 580
        canvas.paste(after_img, (after_x, y_offset))
        
        # "AFTER" label
        draw.text((after_x + 200, y_offset - 40), "AFTER", 
                 fill=self.brand_colors.primary, font=before_font, anchor="mm")
        
        # Add arrow between images
        arrow_y = y_offset + 200
        draw.polygon([(520, arrow_y), (560, arrow_y - 20), (560, arrow_y + 20)], 
                    fill=self.brand_colors.accent)
        
        # Add title
        title_font = self.font_manager.get_font(self.config.font_sizes['title'], 'bold')
        self._draw_wrapped_text(draw, title, (self.config.width // 2, 100), 
                               title_font, self.brand_colors.text_dark, 
                               max_width=self.config.width - 120, align='center')
        
        # Add description if provided
        if description:
            desc_font = self.font_manager.get_font(self.config.font_sizes['body'])
            self._draw_wrapped_text(draw, description, (self.config.width // 2, 700), 
                                   desc_font, self.brand_colors.text_dark,
                                   max_width=self.config.width - 120, align='center')
        
        # Add branding
        self._add_branding(canvas, draw)
        
        return canvas
    
    def create_plant_spotlight(self, plant_data: Dict) -> Image.Image:
        """
        Create plant spotlight template.
        Expected format:
        {
            'name': str,
            'scientific_name': str,
            'difficulty': str,
            'lighting': str,
            'co2': str,
            'image_url': str,
            'description': str
        }
        """
        canvas = Image.new('RGB', (self.config.width, self.config.height), 
                          self.brand_colors.background)
        draw = ImageDraw.Draw(canvas)
        
        # Add plant image
        if plant_data.get('image_url'):
            plant_img = self._download_and_resize_image(plant_data['image_url'], (500, 400))
            # Apply subtle rounded corners
            plant_img = self._add_rounded_corners(plant_img, 20)
            canvas.paste(plant_img, (290, 150), plant_img)
        
        # Title section
        title_font = self.font_manager.get_font(self.config.font_sizes['title'], 'bold')
        subtitle_font = self.font_manager.get_font(self.config.font_sizes['subtitle'])
        
        # Plant name
        draw.text((540, 80), plant_data['name'], fill=self.brand_colors.primary, 
                 font=title_font, anchor="mm")
        
        # Scientific name
        draw.text((540, 120), plant_data['scientific_name'], 
                 fill=self.brand_colors.text_dark, font=subtitle_font, anchor="mm")
        
        # Care requirements section
        care_y = 600
        care_font = self.font_manager.get_font(self.config.font_sizes['body'])
        
        requirements = [
            f"💡 Lighting: {plant_data.get('lighting', 'Medium')}",
            f"🌿 Difficulty: {plant_data.get('difficulty', 'Medium')}",
            f"💨 CO2: {plant_data.get('co2', 'Optional')}"
        ]
        
        for i, req in enumerate(requirements):
            draw.text((120, care_y + (i * 40)), req, fill=self.brand_colors.text_dark, 
                     font=care_font)
        
        # Description
        if plant_data.get('description'):
            desc_font = self.font_manager.get_font(self.config.font_sizes['body'])
            self._draw_wrapped_text(draw, plant_data['description'], 
                                   (540, 850), desc_font, self.brand_colors.text_dark,
                                   max_width=800, align='center')
        
        # Add decorative elements
        self._add_plant_decorations(canvas, draw)
        self._add_branding(canvas, draw)
        
        return canvas
    
    def create_tutorial_step(self, step_data: Dict) -> Image.Image:
        """
        Create tutorial step template.
        Expected format:
        {
            'step_number': int,
            'total_steps': int,
            'title': str,
            'instruction': str,
            'image_url': str (optional),
            'tips': List[str] (optional)
        }
        """
        canvas = Image.new('RGB', (self.config.width, self.config.height), 
                          self.brand_colors.background)
        draw = ImageDraw.Draw(canvas)
        
        # Step number circle
        step_circle_center = (150, 150)
        step_circle_radius = 60
        
        # Draw circle background
        draw.ellipse([
            step_circle_center[0] - step_circle_radius,
            step_circle_center[1] - step_circle_radius,
            step_circle_center[0] + step_circle_radius,
            step_circle_center[1] + step_circle_radius
        ], fill=self.brand_colors.primary)
        
        # Step number text
        step_font = self.font_manager.get_font(48, 'bold')
        draw.text(step_circle_center, str(step_data['step_number']), 
                 fill=self.brand_colors.text_light, font=step_font, anchor="mm")
        
        # Progress indicator
        progress_width = 300
        progress_x = 250
        progress_y = 180
        
        # Background bar
        draw.rectangle([progress_x, progress_y, progress_x + progress_width, progress_y + 8], 
                      fill=self.brand_colors.secondary)
        
        # Progress bar
        progress_fill = (step_data['step_number'] / step_data['total_steps']) * progress_width
        draw.rectangle([progress_x, progress_y, progress_x + progress_fill, progress_y + 8], 
                      fill=self.brand_colors.accent)
        
        # Step title
        title_font = self.font_manager.get_font(self.config.font_sizes['title'], 'bold')
        self._draw_wrapped_text(draw, step_data['title'], (540, 80), 
                               title_font, self.brand_colors.text_dark,
                               max_width=700, align='center')
        
        # Main instruction
        instruction_font = self.font_manager.get_font(self.config.font_sizes['body'])
        self._draw_wrapped_text(draw, step_data['instruction'], (540, 300), 
                               instruction_font, self.brand_colors.text_dark,
                               max_width=800, align='center')
        
        # Add image if provided
        if step_data.get('image_url'):
            step_img = self._download_and_resize_image(step_data['image_url'], (400, 300))
            step_img = self._add_rounded_corners(step_img, 15)
            canvas.paste(step_img, (340, 450), step_img)
        
        # Add tips if provided
        if step_data.get('tips'):
            tips_y = 800
            tips_font = self.font_manager.get_font(self.config.font_sizes['caption'])
            
            draw.text((120, tips_y), "💡 Tips:", fill=self.brand_colors.accent, 
                     font=tips_font)
            
            for i, tip in enumerate(step_data['tips'][:3]):  # Max 3 tips
                draw.text((120, tips_y + 30 + (i * 25)), f"• {tip}", 
                         fill=self.brand_colors.text_dark, font=tips_font)
        
        self._add_branding(canvas, draw)
        return canvas
    
    def create_quote_card(self, quote: str, author: str = None, 
                         background_image_url: str = None) -> Image.Image:
        """Create inspirational quote card"""
        canvas = Image.new('RGB', (self.config.width, self.config.height), 
                          self.brand_colors.background)
        
        # Add background image if provided
        if background_image_url:
            bg_img = self._download_and_resize_image(background_image_url, 
                                                   (self.config.width, self.config.height))
            # Apply overlay for text readability
            bg_img = self._apply_overlay(bg_img, 0.6)
            canvas.paste(bg_img, (0, 0))
        
        draw = ImageDraw.Draw(canvas)
        
        # Quote text
        quote_font = self.font_manager.get_font(self.config.font_sizes['subtitle'], 'italic')
        quote_color = self.brand_colors.text_light if background_image_url else self.brand_colors.text_dark
        
        # Add quotation marks
        quote_with_marks = f'"{quote}"'
        self._draw_wrapped_text(draw, quote_with_marks, (540, 400), 
                               quote_font, quote_color, max_width=800, align='center')
        
        # Author
        if author:
            author_font = self.font_manager.get_font(self.config.font_sizes['body'])
            draw.text((540, 600), f"— {author}", fill=quote_color, 
                     font=author_font, anchor="mm")
        
        self._add_branding(canvas, draw, light_version=bool(background_image_url))
        return canvas
    
    def _create_title_slide(self, title: str, subtitle: str = None, 
                           template_type: TemplateType = None) -> Image.Image:
        """Create a title slide for carousel posts"""
        canvas = Image.new('RGB', (self.config.width, self.config.height), 
                          self.brand_colors.primary)
        draw = ImageDraw.Draw(canvas)
        
        # Title
        title_font = self.font_manager.get_font(self.config.font_sizes['title'], 'bold')
        self._draw_wrapped_text(draw, title, (540, 400), title_font, 
                               self.brand_colors.text_light, max_width=800, align='center')
        
        # Subtitle
        if subtitle:
            subtitle_font = self.font_manager.get_font(self.config.font_sizes['subtitle'])
            draw.text((540, 500), subtitle, fill=self.brand_colors.accent, 
                     font=subtitle_font, anchor="mm")
        
        # Add decorative elements
        self._add_decorative_shapes(canvas, draw)
        self._add_branding(canvas, draw, light_version=True)
        
        return canvas
    
    def _create_content_slide(self, title: str, content: str, slide_number: str = None,
                             image_url: str = None, template_type: TemplateType = None) -> Image.Image:
        """Create a content slide for carousel posts"""
        canvas = Image.new('RGB', (self.config.width, self.config.height), 
                          self.brand_colors.background)
        draw = ImageDraw.Draw(canvas)
        
        # Slide number
        if slide_number:
            number_font = self.font_manager.get_font(self.config.font_sizes['small'])
            draw.text((self.config.width - 60, 60), slide_number, 
                     fill=self.brand_colors.primary, font=number_font, anchor="rm")
        
        # Title
        title_font = self.font_manager.get_font(self.config.font_sizes['subtitle'], 'bold')
        self._draw_wrapped_text(draw, title, (540, 150), title_font, 
                               self.brand_colors.primary, max_width=800, align='center')
        
        # Content
        content_font = self.font_manager.get_font(self.config.font_sizes['body'])
        content_y = 250
        
        if image_url:
            # If image provided, split layout
            img = self._download_and_resize_image(image_url, (400, 300))
            img = self._add_rounded_corners(img, 15)
            canvas.paste(img, (340, 500), img)
            content_max_width = 700
        else:
            content_max_width = 800
        
        self._draw_wrapped_text(draw, content, (540, content_y), content_font, 
                               self.brand_colors.text_dark, max_width=content_max_width, 
                               align='center')
        
        self._add_branding(canvas, draw)
        return canvas
    
    def _download_and_resize_image(self, url: str, size: Tuple[int, int]) -> Image.Image:
        """Download and resize image from URL"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            img = Image.open(io.BytesIO(response.content))
            img = img.convert('RGB')
            
            # Resize maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Create canvas and center image
            canvas = Image.new('RGB', size, (255, 255, 255))
            offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
            canvas.paste(img, offset)
            
            return canvas
            
        except Exception as e:
            # Return placeholder image
            placeholder = Image.new('RGB', size, self.brand_colors.secondary)
            draw = ImageDraw.Draw(placeholder)
            font = self.font_manager.get_font(24)
            draw.text((size[0]//2, size[1]//2), "Image\nUnavailable", 
                     fill=self.brand_colors.text_light, font=font, anchor="mm")
            return placeholder
    
    def _add_rounded_corners(self, img: Image.Image, radius: int) -> Image.Image:
        """Add rounded corners to image"""
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + img.size, radius, fill=255)
        
        result = Image.new('RGBA', img.size, (0, 0, 0, 0))
        result.paste(img, (0, 0))
        result.putalpha(mask)
        
        return result
    
    def _apply_overlay(self, img: Image.Image, opacity: float) -> Image.Image:
        """Apply dark overlay to image"""
        overlay = Image.new('RGBA', img.size, (0, 0, 0, int(255 * opacity)))
        img = img.convert('RGBA')
        return Image.alpha_composite(img, overlay).convert('RGB')
    
    def _draw_wrapped_text(self, draw: ImageDraw.Draw, text: str, position: Tuple[int, int],
                          font: ImageFont.ImageFont, fill: str, max_width: int, 
                          align: str = 'left') -> int:
        """Draw wrapped text and return final y position"""
        lines = textwrap.wrap(text, width=max_width // (font.size // 2))
        
        y_offset = position[1]
        line_height = font.size + 10
        
        # Adjust starting position for center alignment
        if align == 'center':
            y_offset -= (len(lines) * line_height) // 2
        
        for line in lines:
            if align == 'center':
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                x_pos = position[0] - line_width // 2
            else:
                x_pos = position[0]
            
            draw.text((x_pos, y_offset), line, fill=fill, font=font)
            y_offset += line_height
        
        return y_offset
    
    def _add_branding(self, canvas: Image.Image, draw: ImageDraw.Draw, 
                     light_version: bool = False):
        """Add AquaScene branding to template"""
        brand_color = self.brand_colors.text_light if light_version else self.brand_colors.primary
        
        # Logo/brand text
        brand_font = self.font_manager.get_font(self.config.font_sizes['caption'], 'bold')
        draw.text((60, self.config.height - 80), "AquaScene", 
                 fill=brand_color, font=brand_font)
        
        # Website
        website_font = self.font_manager.get_font(self.config.font_sizes['small'])
        draw.text((60, self.config.height - 50), "aquascene.bg", 
                 fill=brand_color, font=website_font)
    
    def _add_decorative_shapes(self, canvas: Image.Image, draw: ImageDraw.Draw):
        """Add decorative geometric shapes"""
        # Corner triangles
        triangle_size = 100
        
        # Top right
        draw.polygon([
            (self.config.width - triangle_size, 0),
            (self.config.width, 0),
            (self.config.width, triangle_size)
        ], fill=self.brand_colors.accent)
        
        # Bottom left
        draw.polygon([
            (0, self.config.height - triangle_size),
            (0, self.config.height),
            (triangle_size, self.config.height)
        ], fill=self.brand_colors.secondary)
    
    def _add_plant_decorations(self, canvas: Image.Image, draw: ImageDraw.Draw):
        """Add plant-themed decorative elements"""
        # Simple leaf shapes
        leaf_color = self.brand_colors.secondary
        
        # Small decorative leaves
        for i in range(3):
            x = 80 + (i * 30)
            y = 300 + (i * 20)
            draw.ellipse([x, y, x + 20, y + 40], fill=leaf_color)


# Usage example
if __name__ == "__main__":
    generator = VisualTemplateGenerator()
    
    # Test educational carousel
    educational_content = {
        'title': 'Aquascaping Basics for Beginners',
        'slides': [
            {
                'title': 'Choose Your Tank Size',
                'content': 'Start with at least 10 gallons for your first aquascape. Larger tanks are more stable and forgiving for beginners.',
            },
            {
                'title': 'Lighting is Key',
                'content': 'Proper lighting is essential for plant growth. LED fixtures provide excellent control and energy efficiency.',
            },
            {
                'title': 'Substrate Selection',
                'content': 'Use nutrient-rich aquascaping substrate. Add a layer of gravel or sand for the perfect foundation.',
            }
        ]
    }
    
    slides = generator.create_educational_carousel(educational_content)
    
    # Save slides
    for i, slide in enumerate(slides):
        slide.save(f'educational_slide_{i}.jpg', 'JPEG', quality=95)