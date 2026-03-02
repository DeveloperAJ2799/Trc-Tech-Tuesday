import os
import textwrap
import requests
import urllib3
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
TEMPLATE_PATH = "Frame 2241.png"
OUTPUT_PATH = "latest_story.jpg"

FONT_BOLD_PATH = "clash-display-font/ClashDisplay-Bold.otf"
FONT_MEDIUM_PATH = "clash-display-font/ClashDisplay-Medium.otf"

def create_instagram_story(title: str, summary: str, source: str, output_path: str = OUTPUT_PATH, image_url: str = None):
    """Fills your custom template with tech news data, including right-aligned formatting."""
    
    if not os.path.exists(TEMPLATE_PATH):
        print(f"Error: Template not found at {TEMPLATE_PATH}. Please provide the template file.")
        return None

    # Load Template
    img = Image.open(TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Load Fonts
    try:
        font_title = ImageFont.truetype(FONT_BOLD_PATH, 90)
        font_summary = ImageFont.truetype(FONT_MEDIUM_PATH, 55)
    except IOError:
        print("Warning: Custom font not found. Using default fonts.")
        font_title = font_summary = ImageFont.load_default()

    YELLOW = (255, 232, 0)
    WHITE = (255, 255, 255)

    # 1. Draw Title (Left-aligned, Top)
    title_upper = title.upper()
    title_lines = textwrap.wrap(title_upper, width=16) 
    y_title = 320
    x_title = 80
    for line in title_lines:
        draw.text((x_title, y_title), line, fill=YELLOW, font=font_title)
        y_title += 95

    # 2. Draw Image (Middle)
    y_img_bottom = y_title + 80
    if image_url:
        try:
            print(f"Fetching news image: {image_url}")
            response = requests.get(image_url, timeout=10, verify=False)
            if response.status_code == 200:
                news_img = Image.open(BytesIO(response.content)).convert("RGBA")
                
                # Resize and crop to fit 920x600 centered
                target_w, target_h = 920, 600
                news_img_ratio = news_img.width / news_img.height
                target_ratio = target_w / target_h
                
                if news_img_ratio > target_ratio:
                    new_w = int(target_h * news_img_ratio)
                    news_img = news_img.resize((new_w, target_h), Image.Resampling.LANCZOS)
                    left = (new_w - target_w) // 2
                    news_img = news_img.crop((left, 0, left + target_w, target_h))
                else:
                    new_h = int(target_w / news_img_ratio)
                    news_img = news_img.resize((target_w, new_h), Image.Resampling.LANCZOS)
                    top = (new_h - target_h) // 2
                    news_img = news_img.crop((0, top, target_w, top + target_h))

                img_x = (width - target_w) // 2
                img_y = y_title + 60
                
                # Round corners a bit for polish
                mask = Image.new("L", (target_w, target_h), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle((0, 0, target_w, target_h), radius=30, fill=255)
                
                img.paste(news_img, (img_x, img_y), mask)
                y_img_bottom = img_y + target_h + 80
        except Exception as e:
            print(f"Warning: Failed to load image from URL: {e}")

    # 3. Draw Summary (Right-aligned, Bottom)
    summary_lines = textwrap.wrap(summary, width=32)
    line_spacing = 65
    
    # Calculate bottom position to be anchored above the lower boundary
    total_summary_height = len(summary_lines) * line_spacing
    y_summary = max(y_img_bottom + 50, height - total_summary_height - 300)
    
    right_margin = width - 80
    for line in summary_lines:
        # Get bounding box for the line to calculate its width
        bbox = draw.textbbox((0, 0), line, font=font_summary)
        line_width = bbox[2] - bbox[0]
        x_line = right_margin - line_width # Shift left by the width of the line to right-align
        
        draw.text((x_line, y_summary), line, fill=WHITE, font=font_summary)
        y_summary += line_spacing

    # Save final image
    img.save(output_path, "JPEG", quality=95)
    print(f"Generated story using template: {output_path}")
    return output_path