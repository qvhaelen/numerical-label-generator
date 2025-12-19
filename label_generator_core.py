import os
import random
import csv
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np
import matplotlib.font_manager as fm
import colorsys
import io
from PIL import ImageChops


def encode_scientific_notation(text):
    """
    Convert Unicode superscript notation to plain-text representation
    Example: "1.23 × 10⁻³" → "1.23 × 10^{-3}"
    """
    superscript_map = {
        '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
        '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
        '⁻': '-', '⁺': '+'
    }
    
    # Convert superscript characters to normal digits
    converted = []
    for char in text:
        converted.append(superscript_map.get(char, char))
    
    # Check if scientific notation exists
    plain_text = ''.join(converted)
    if " × 10" in plain_text:
        return plain_text.replace(" × 10", " × 10^{") + "}"
    return plain_text


def apply_gamma_distortion(image, gamma=random.uniform(1.8, 2.4)):
    """Apply gamma correction to an image in a memory-safe way"""
    # Convert to numpy array while keeping the image in memory
    if image.mode == 'RGBA':
        # Preserve alpha channel
        r, g, b, a = image.split()
        rgb_image = Image.merge('RGB', (r, g, b))
        arr = np.array(rgb_image) / 255.0
        arr = np.power(arr, gamma)
        arr = (arr * 255).astype(np.uint8)
        distorted = Image.fromarray(arr).convert('RGB')
        r, g, b = distorted.split()
        return Image.merge('RGBA', (r, g, b, a))
    else:
        # For RGB or other modes
        arr = np.array(image.copy()) / 255.0  # Use copy() to ensure data stays in memory
        arr = np.power(arr, gamma)
        return Image.fromarray((arr * 255).astype(np.uint8))


class RealismEnhancer:
    def __init__(self, settings):
        self.settings = settings
    

    def apply_mode_aware(self, image, is_transparent=False):
        """Apply realism effects with mode awareness"""
        # Work on a copy to avoid closed file issues
        img = image.copy()
        intensity = self.settings.realism_intensity
        
        # Store original mode
        original_mode = img.mode
        
        # For transparent images, handle alpha channel carefully
        if is_transparent and original_mode == 'RGBA':
            # Separate alpha channel
            r, g, b, a = img.split()
            rgb_image = Image.merge('RGB', (r, g, b))
            
            # Apply effects to RGB only
            if random.random() < intensity:
                rgb_image = self.apply_realistic_scaling(rgb_image)
            if random.random() < intensity:
                rgb_image = self.add_jpeg_artifacts(rgb_image)
            if random.random() < intensity/2:
                rgb_image = self.apply_subpixel_shift(rgb_image)
            if random.random() < intensity:
                rgb_image = self.apply_gamma_distortion(rgb_image)
            if random.random() < intensity:
                rgb_image = self.add_complex_background(rgb_image)
            if random.random() < intensity/3:
                rgb_image = self.apply_font_rendering_variation(rgb_image)
            
            # Merge back with original alpha
            r2, g2, b2 = rgb_image.split()
            return Image.merge('RGBA', (r2, g2, b2, a))
        else:
            # Apply normally for RGB images
            return self.apply(img) 





    
    def apply(self, image):
        #if  image.mode == 'RGBA':
        #    return image
        # Work on a copy to avoid closed file issues
        img = image.copy()
        intensity = self.settings.realism_intensity
        
        if random.random() < intensity:
            img = self.apply_realistic_scaling(img)
        if random.random() < intensity:
            img = self.add_jpeg_artifacts(img)
        if random.random() < intensity/2:
            img = self.apply_subpixel_shift(img)
        if random.random() < intensity:
            img = self.apply_gamma_distortion(img)
        if random.random() < intensity:
            img = self.add_complex_background(img)
        if random.random() < intensity/3:
            img = self.apply_font_rendering_variation(img)
        return img

    def apply_realistic_scaling(self, image):
        # Scale range based on intensity
        min_scale = max(0.5, 1.0 - self.settings.realism_intensity/2)
        max_scale = min(2.0, 1.0 + self.settings.realism_intensity)
        
        scale_factor = random.uniform(min_scale, max_scale)
        new_size = (int(image.width * scale_factor), 
                    int(image.height * scale_factor))
        
        methods = [
            Image.Resampling.NEAREST,
            Image.Resampling.BILINEAR,
            Image.Resampling.BICUBIC
        ]
        method = random.choice(methods)
        
        return image.resize(new_size, method)

    def add_jpeg_artifacts(self, image):
        # Quality range based on intensity (lower quality = more artifacts)
        min_quality = max(20, 90 - int(self.settings.realism_intensity * 50))
        max_quality = 90
        quality = random.randint(min_quality, max_quality)
        
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=quality)
        buffer.seek(0)
        return Image.open(buffer).convert(image.mode)
        
    def apply_subpixel_shift(self, image):
        shift = random.randint(-1, 1)
        if image.mode in ['RGB', 'RGBA']:
            r, g, b, *a = image.split()
            channels = [
                ImageChops.offset(ch, shift, 0) 
                for ch in (r, g, b)
            ]
            if a:
                channels.append(a[0])
            return Image.merge(image.mode, channels)
        return image
        
    def apply_gamma_distortion(self, image):
        min_gamma = max(1.5, 2.4 - self.settings.realism_intensity)
        max_gamma = min(3.0, 2.4 + self.settings.realism_intensity)
        gamma = random.uniform(min_gamma, max_gamma)
        return apply_gamma_distortion(image, gamma)

    def add_complex_background(self, image):
        # Background complexity based on intensity
        complexity = int(self.settings.realism_intensity * 5)
        
        bg = Image.new('RGB', image.size, "#FFFFFF")
        draw = ImageDraw.Draw(bg)
        
        # Add grid lines - more lines with higher complexity
        grid_size = 40 - (complexity * 6)
        if grid_size < 5:
            grid_size = 5
            
        for i in range(0, image.width, grid_size):
            draw.line([(i, 0), (i, image.height)], fill="#EEEEEE")
        for i in range(0, image.height, grid_size):
            draw.line([(0, i), (image.width, i)], fill="#EEEEEE")
        
        # Add noise for higher complexity levels
        if complexity > 2:
            for _ in range(complexity * 10):
                x = random.randint(0, image.width-1)
                y = random.randint(0, image.height-1)
                draw.point((x, y), fill="#DDDDDD")
        
        # Composite label over background
        if image.mode == 'RGBA':
            bg.paste(image, (0, 0), image)
        else:
            bg.paste(image, (0, 0))
        return bg

    def apply_font_rendering_variation(self, image):
        # Kernel size based on intensity
        max_kernel = min(5, int(1 + self.settings.realism_intensity * 4))
        kernel_size = random.choice([1, max_kernel])
        
        operation = random.choice(['dilate', 'erode'])
        if operation == 'dilate':
            return image.filter(ImageFilter.MaxFilter(kernel_size))
        else:
            return image.filter(ImageFilter.MinFilter(kernel_size))


class LabelGeneratorSettings:
    """Encapsulates all configurable settings for label generation"""
    def __init__(self):
        # Initialize with default values
        self.num_labels = 2000
        self.output_format = 'png'
        self.output_dir = './test_labels-5-270'
        self.vintage_intensity = 0.7
        self.texture_file = 'old_paper.png'
        self.customized_size_resolution = True
       
        # Resolution customization parameters
        self.min_width = 200
        self.max_width = 400
        self.min_height = 100
        self.max_height = 200
        self.min_dpi = 50
        self.max_dpi = 100
        self.fixed_dpi = 150
      
        self.add_realism = True  # Set to False to disable realism effects
        self.realism_intensity = 0.7  # Controls all realism effects
  
        # Text content parameters
        self.label_text_options = [
            "0.5", "1.0", "2.7", "3.0", "11", "23", 
            "10,000", "25,000", "50,000", "100,000", "customize"
        ]
        self.scientific_notation_prob = 0.35
        # Units configuration
        self.available_units = [
            "", "  mg", "  mL", "  μg", "  μL", "  %", "  ppm", "  kelvin", "  M", 
            " mM", " nM", " seconds", "  minutes", " hours", "  days", " (s)", 
            "  (h)", " Celsius", "  Fahrenheit", "  Rankine", "meter", "liter", 
            "(kg/L)", " m", " cm"
        ]
        self.units = self.available_units[:]  # By default, all units are selected
        self.unit_separator = ["  ", " ", " --- "]
        
        # Font and styling parameters
        self.base_font_size = 24
        self.font_size_variation = 6
        self.font_families = self.get_safe_fonts()
        self.font_weights = ["normal", "bold", "italic"]
        self.text_colors = ["#000000", "#333333", "#555555", "#777777"]
        self.min_background_brightness = 0.8  # 0-1.0 (higher = lighter)
        self.transparent_bg_prob = 0
        
        # Rotation parameters
        self.rotation_allowed = False
        self.rotation_angle_allowed = ['0','30', '45','60', '90', '315','270', 'customize']
        self.custom_angle_step = 5
        
        # Vintage effect parameters
        self.vintage_effect_prob = 0.7
        self.noise_intensity = 0.1
        self.blur_intensity = 0.5
        
        # Padding settings
        self.min_text_padding = 20  # Minimum padding around text
        
        # Clipping settings
        self.allow_clipping = False
        self.clipping_probability = 0.1
        
        # Initialize calculated properties
        self.update_calculated_properties()

    def update_calculated_properties(self):
        """Update calculated properties based on current settings"""
        # Adjust image size based on font size
        max_font_size = self.base_font_size + self.font_size_variation
        
        # Set fixed or variable dimensions
        if self.customized_size_resolution:
            self.image_width = random.randint(self.min_width, self.max_width)
            self.image_height = random.randint(self.min_height, self.max_height)
        else:
            # Fixed dimensions based on font size
            self.image_width = max(150, int(max_font_size * 8))
            self.image_height = max(60, int(max_font_size * 3))
            
    def get_safe_fonts(self):
        """Get list of safe fonts that can render basic text"""
        system_fonts = fm.findSystemFonts()
        safe_fonts = []
        for fpath in system_fonts:
            try:
                font = fm.get_font(fpath)
                if font.style.find('Regular') != -1 and font.variant.find('normal') != -1:
                    safe_fonts.append(font.name)
            except:
                continue
        return list(set(safe_fonts)) + ['DejaVu Sans', 'Arial', 'Verdana', 'Times New Roman']
    
    def generate_light_background(self):
        """Generate a light background color with guaranteed brightness"""
        # Generate random color in HSV space
        h = random.random()
        s = random.uniform(0.0, 0.3)  # Low saturation = pastel
        v = random.uniform(self.min_background_brightness, 1.0)
        
        # Convert to RGB
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        
        return f"#{r:02x}{g:02x}{b:02x}"


class LabelGenerator:
    """Handles the generation of label images based on settings"""
    def __init__(self, settings):
        self.settings = settings
        self.settings.update_calculated_properties()
        self.metadata = []
        
    def to_superscript(self, num):
        """Convert numbers to Unicode superscript characters"""
        superscript_map = {
            '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
            '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
            '-': '⁻', '+': '⁺'
        }
        return ''.join(superscript_map.get(char, char) for char in str(num))

    def generate_label_text(self):
        """Generate label text with proper scientific notation"""
        base_text = random.choice(self.settings.label_text_options)
        
        if base_text == "customize":
            base_text = str(round(random.uniform(1, 60), 4))
            
        # Apply scientific notation with probability
        if random.random() < self.settings.scientific_notation_prob and ',' in base_text:
            try:
                value = float(base_text.replace(',', ''))
                exponent = int(np.floor(np.log10(value)))
                coefficient = value / (10 ** exponent)
                
                # Format coefficient with random precision
                dec_places = random.randint(1, 3)
                coef_str = format(coefficient, f'.{dec_places}f').rstrip('0').rstrip('.')
                
                # Create proper superscript
                exp_str = self.to_superscript(exponent)
                base_text = f"{coef_str} × 10{exp_str}"
            except:
                pass  # Fallback to original text if conversion fails
        elif random.random() < self.settings.scientific_notation_prob:
            value = round(random.uniform(1, 60), 3)
            exp_str = random.randint(-14, 14)
            if random.uniform(1, 2) < 1.5:
                base_text = str(value) + "E" + str(exp_str)
            else:
                base_text = str(value) + "e" + str(exp_str)
                
        # Add units - FIXED: Check if units list is not empty
        if random.random() > 0.3 and self.settings.units:  # 70% chance to add units if units exist
            separator = random.choice(self.settings.unit_separator)
            unit = random.choice(self.settings.units)
            return base_text + separator + unit
        return base_text

    def determine_rotation_angle(self):
        """Determine rotation angle based on settings"""
        if not self.settings.rotation_allowed:
            return 0
        
        angle_type = random.choice(self.settings.rotation_angle_allowed)
        
        if angle_type == 'customize':
            # Generate custom angle (multiple of step between 0-90)
            angle = random.randrange(5, 80, self.settings.custom_angle_step)
            # Avoid duplicating preset angles
            while angle in [0, 45, 90]:
                angle = random.randrange(5, 80, self.settings.custom_angle_step)
            return angle
        else:
            return int(angle_type)

    def apply_vintage_effects(self, image, intensity=0.7):
        """Apply vintage effects to label images"""
        try:
            if random.random() < 0.8:
                image = image.filter(ImageFilter.GaussianBlur(
                    radius=self.settings.blur_intensity * intensity
                ))
            
            if random.random() < 0.6:
                try:
                    texture = Image.open(self.settings.texture_file).convert('L')
                    texture = texture.resize(image.size)
                    image = Image.blend(image.convert('RGB'), texture.convert('RGB'), 0.1)
                except:
                    pass
            
            if random.random() < 0.7:
                sepia_filter = (
                    0.393 + 0.1*intensity, 0.769, 0.189, 0,
                    0.349, 0.686 + 0.1*intensity, 0.168, 0,
                    0.272, 0.534, 0.131 + 0.1*intensity, 0
                )
                image = image.convert('RGB', matrix=sepia_filter)
            
            if random.random() < 0.5:
                arr = np.array(image).astype(np.float32)
                noise = np.random.normal(0, 20*intensity, arr.shape)
                noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
                image = Image.fromarray(noisy)
            
            enhancer = ImageEnhance.Brightness(image)
            return enhancer.enhance(1 - 0.2*intensity)
        
        except Exception as e:
            print(f"Error applying vintage effects: {str(e)}")
            return image
    
    

    def create_label_image(self, label_idx):
        """Create a single label image with metadata - FIXED VERSION"""
        # Generate text content
        label_text = self.generate_label_text()
    
        # Determine rotation angle
        rotation_angle = self.determine_rotation_angle()
    
        # Select random font properties
        font_family = random.choice(self.settings.font_families)
        font_size = self.settings.base_font_size + random.randint(
            -self.settings.font_size_variation, 
            self.settings.font_size_variation
        )
        font_weight = random.choice(self.settings.font_weights)
        text_color = random.choice(self.settings.text_colors)
    
        # Always generate a background color (needed for rotation, JPG conversion, etc.)
        generated_bg_color = self.settings.generate_light_background()
    
        # Determine if we use transparent background
        use_transparent_bg = random.random() < self.settings.transparent_bg_prob
    
        # Create temporary image for text measurement
        # ALWAYS use RGB for measurement to avoid alpha channel issues
        temp_img = Image.new('RGB', (100, 100), generated_bg_color)
        draw = ImageDraw.Draw(temp_img)
    
        try:
            font = ImageFont.truetype(font_family, font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
    
        # Get text bounding box
        try:
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            # Fallback for older Pillow versions
            _, _, text_width, text_height = draw.textbbox((0, 0), label_text, font=font)
            bbox = (0, 0, text_width, text_height)
    
        # Calculate canvas size with padding
        padding = self.settings.min_text_padding
        canvas_width = text_width + 2 * padding
        canvas_height = text_height + 2 * padding
    
        # Create canvas - MODE CONSISTENCY FIX
        if use_transparent_bg:
            # RGBA mode for transparent background
            canvas = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        else:
            # RGB mode for colored background
            canvas = Image.new('RGB', (canvas_width, canvas_height), generated_bg_color)
    
        if self.settings.customized_size_resolution:
            # Determine target dimensions
            target_width = self.settings.image_width
            target_height = self.settings.image_height
        
            # Resize canvas while maintaining aspect ratio
            canvas_aspect = canvas.width / canvas.height
            target_aspect = target_width / target_height
        
            if canvas_aspect > target_aspect:
                # Canvas is wider than target
                new_height = int(target_width / canvas_aspect)
                new_size = (target_width, new_height)
            else:
                # Canvas is taller than target
                new_width = int(target_height * canvas_aspect)
                new_size = (new_width, target_height)
        
            # Resize with high-quality Lanczos filtering
            # Convert to RGBA temporarily for resizing if needed
            if use_transparent_bg and canvas.mode != 'RGBA':
                canvas = canvas.convert('RGBA')
            canvas = canvas.resize(new_size, Image.Resampling.LANCZOS)
    
        # Create drawing context
        draw = ImageDraw.Draw(canvas)
    
        # Calculate text position (centered with padding)
        x = padding - bbox[0]  # Adjust for left bearing
        y = padding - bbox[1]  # Adjust for top bearing
    
        # Draw text directly on canvas
        # Convert text_color to RGBA tuple if needed for transparent background
        if use_transparent_bg:
            # Ensure text color is in RGBA format
            if text_color.startswith('#'):
                r = int(text_color[1:3], 16)
                g = int(text_color[3:5], 16)
                b = int(text_color[5:7], 16)
                text_color_tuple = (r, g, b, 255)  # Full opacity
            else:
                # Default to black if parsing fails
                text_color_tuple = (0, 0, 0, 255)
            draw.text((x, y), label_text, fill=text_color_tuple, font=font)
        else:
            # Use hex string for RGB mode
            draw.text((x, y), label_text, fill=text_color, font=font)
    
        # Apply rotation to the entire canvas - ROBUST FIX
        if rotation_angle != 0:
            # Calculate expansion size for rotation
            diagonal = int(np.sqrt(canvas_width**2 + canvas_height**2))
            expand_size = max(canvas_width, canvas_height, diagonal) + padding
        
            # Create expanded canvas with same mode as original
            if use_transparent_bg:
                expanded_canvas = Image.new('RGBA', (expand_size, expand_size), (0, 0, 0, 0))
            else:
                expanded_canvas = Image.new('RGB', (expand_size, expand_size), generated_bg_color)
        
            # Paste original canvas at center of expanded canvas
            paste_x = (expand_size - canvas_width) // 2
            paste_y = (expand_size - canvas_height) // 2
            expanded_canvas.paste(canvas, (paste_x, paste_y))
        
            # Define fillcolor for rotation - handle both modes
            if use_transparent_bg:
                fillcolor = (0, 0, 0, 0)  # Transparent for RGBA
            else:
                # Convert hex to RGB tuple
                if generated_bg_color.startswith('#'):
                    r = int(generated_bg_color[1:3], 16)
                    g = int(generated_bg_color[3:5], 16)
                    b = int(generated_bg_color[5:7], 16)
                    fillcolor = (r, g, b)
                else:
                    fillcolor = (255, 255, 255)  # Default to white
        
            # Rotate the expanded canvas
            expanded_canvas = expanded_canvas.rotate(
                rotation_angle, 
                expand=False,
                fillcolor=fillcolor
            )
        
            # Crop to content
            bbox = expanded_canvas.getbbox()
            if bbox:
                canvas = expanded_canvas.crop(bbox)
            else:
                canvas = expanded_canvas
    
        # Apply vintage effects - MODE-AWARE VERSION
        apply_vintage = random.random() < self.settings.vintage_effect_prob
        if apply_vintage:
            # Store original mode for transparent images
            original_mode = canvas.mode
        
            # If image is RGBA (transparent), convert to RGB for vintage effects
            # then convert back to RGBA with alpha channel
            if original_mode == 'RGBA':
                # Separate alpha channel
                r, g, b, a = canvas.split()
                rgb_canvas = Image.merge('RGB', (r, g, b))
            
                # Apply vintage effects to RGB version
                rgb_canvas = self.apply_vintage_effects(rgb_canvas, self.settings.vintage_intensity)
            
                # Merge back with original alpha
                r2, g2, b2 = rgb_canvas.split()
                canvas = Image.merge('RGBA', (r2, g2, b2, a))
            else:
                # Apply normally for RGB images
                canvas = self.apply_vintage_effects(canvas, self.settings.vintage_intensity)
  
        # Prepare metadata
        metadata = {
        "label_id": label_idx,
        "text": label_text,
        "rotation_angle": rotation_angle,
        "font_family": font_family,
        "font_size": font_size,
        "font_weight": font_weight,
        "text_color": text_color,
        "background": "transparent" if use_transparent_bg else generated_bg_color,
        "vintage_applied": apply_vintage,
        "vintage_intensity": self.settings.vintage_intensity if apply_vintage else 0
        }
    
        # Apply realism effects if enabled
        if self.settings.add_realism:
            realism = RealismEnhancer(self.settings)
            # Handle realism effects for both transparent and non-transparent backgrounds
            canvas = realism.apply_mode_aware(canvas.copy(), use_transparent_bg)
    
        return canvas, metadata

    
    
##########################################################################################################    
    
    
    def save_metadata(self):
        """Save metadata to both CSV and TXT files"""
        # CSV file (preserves Unicode)
        csv_path = os.path.join(self.settings.output_dir, "labels_metadata.csv")
        fieldnames = [
            "label_id", "image_filename", "text", "rotation_angle", "font_family", 
            "font_size", "font_weight", "text_color", "background",
            "vintage_applied", "vintage_intensity"
        ]
        
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:  # utf-8-sig for Excel
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.metadata)
        
        # TXT file (plain-text with encoded notation)
        txt_path = os.path.join(self.settings.output_dir, "labels_metadata.txt")
        with open(txt_path, 'w', encoding='utf-8') as txtfile:
            # Write header
            headers = "\t".join(fieldnames)
            txtfile.write(f"{headers}\n")
            
            # Write each row with scientific notation encoding
            for row in self.metadata:
                encoded_row = row.copy()
                encoded_row['text'] = encode_scientific_notation(row['text'])
                line = "\t".join(str(encoded_row[field]) for field in fieldnames)
                txtfile.write(f"{line}\n")
        
        return csv_path, txt_path

    def generate_all_labels(self):
        """Generate all labels and save with metadata"""
        os.makedirs(self.settings.output_dir, exist_ok=True)
        
        for i in range(self.settings.num_labels):
            label_idx = i + 1
            image, metadata = self.create_label_image(label_idx)
            
            # Determine DPI based on settings
            if self.settings.customized_size_resolution:
                dpi = random.randint(self.settings.min_dpi, self.settings.max_dpi)
            else:
                dpi = self.settings.fixed_dpi
            
            # Save image
            img_filename = f"label_270_{label_idx:03d}.{self.settings.output_format}"
            img_path = os.path.join(self.settings.output_dir, img_filename)
            
            # Set save parameters
            save_params = {}
            
            # Add DPI information for supported formats
            if self.settings.output_format.lower() in ['png', 'jpg', 'jpeg', 'tiff']:
                save_params['dpi'] = (dpi, dpi)
            
            # Convert to RGB if saving as JPG
            if self.settings.output_format.lower() in ['jpg', 'jpeg']:
                if image.mode in ['RGBA', 'LA']:
                    # Use specified background color for JPG conversion
                    bg_color = metadata['background']
                    if bg_color == "transparent":
                        bg_color = "#FFFFFF"  # Default to white for transparent
                    background = Image.new('RGB', image.size, bg_color)
                    background.paste(image, mask=image.split()[3] if image.mode == 'RGBA' else None)
                    image = background
                save_params['quality'] = 95    
                
            image.save(img_path, **save_params)
            
            # Add filename to metadata
            metadata["image_filename"] = img_filename
            self.metadata.append(metadata)
            
            print(f"Generated label: {img_filename}")
        
        # Save metadata
        csv_path, txt_path = self.save_metadata()
        print(f"Metadata saved to: {csv_path} and {txt_path}")
        print(f"Successfully generated {self.settings.num_labels} labels in '{self.settings.output_dir}'")


def main():
    """Entry point for command-line execution"""
    settings = LabelGeneratorSettings()
    
    # Customize settings here for CLI testing
    settings.num_labels = 10
    settings.output_dir = './test_labels_refactored'
    
    generator = LabelGenerator(settings)
    generator.generate_all_labels()


if __name__ == '__main__':
    main()
