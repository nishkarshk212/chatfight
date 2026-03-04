from PIL import Image, ImageDraw, ImageFont
import os


async def generate_rank_card(user_data, xp, level, prestige=0):
    """Generate a rank card image for the user."""
    # Create image with dark background
    img = Image.new("RGB", (800, 300), "#1e1e2f")
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts, fallback to default if not available
    try:
        # Try common font paths
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:\\Windows\\Fonts\\arial.ttf"
        ]
        
        font_large = None
        font_medium = None
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font_large = ImageFont.truetype(font_path, 48)
                    font_medium = ImageFont.truetype(font_path, 32)
                    break
                except:
                    continue
        
        if font_large is None:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            
    except Exception as e:
        print(f"Font loading error: {e}")
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    # Get username
    username = user_data.get("username") or user_data.get("first_name") or "Unknown User"
    
    # Draw user info
    draw.text((50, 50), f"👤 {username}", fill="white", font=font_large)
    draw.text((50, 120), f"⭐ Level: {level}", fill="#00ffff", font=font_medium)  # Cyan
    draw.text((50, 170), f"✨ XP: {xp}", fill="#ffff00", font=font_medium)  # Yellow
    
    # Add prestige if applicable
    if prestige > 0:
        draw.text((50, 220), f"🎖 Prestige: {prestige}", fill="#ffd700", font=font_medium)  # Gold
    
    # Save image
    output_path = "rank_card.png"
    img.save(output_path)
    
    return output_path


async def generate_leaderboard_image(top_users):
    """Generate an image showing top users with medals."""
    # Create image
    img = Image.new("RGB", (600, 400 + len(top_users) * 50), "#2d2d3f")
    draw = ImageDraw.Draw(img)
    
    # Load font
    try:
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:\\Windows\\Fonts\\arial.ttf"
        ]
        
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, 28)
                    break
                except:
                    continue
        
        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Draw title
    draw.text((50, 30), "🏆 TOP RANKINGS 🏆", fill="#ffd700", font=font)  # Gold
    
    # Medals
    medals = ["🥇", "🥈", "🥉"]
    
    # Draw top users
    y_position = 100
    for i, user in enumerate(top_users):
        if i < 3:
            medal = medals[i]
        else:
            medal = f"{i+1}."
        
        username = user.get("username") or user.get("first_name") or "Unknown"
        level = user.get("level", 1)
        xp = user.get("xp", 0)
        
        draw.text((50, y_position), f"{medal} {username} - Lvl {level} ({xp} XP)", fill="white", font=font)
        y_position += 50
    
    # Save image
    output_path = "leaderboard.png"
    img.save(output_path)
    
    return output_path
