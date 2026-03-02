import os
from instagrapi import Client

def upload_story(image_path: str):
    """Uploads the generated image to Instagram Story."""
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    
    if not username or not password:
        print("Error: Instagram credentials not set in .env")
        return False
        
    try:
        print(f"Logging into Instagram as {username}...")
        cl = Client()
        cl.login(username, password)
        
        print(f"Uploading {image_path} to story...")
        cl.photo_upload_to_story(image_path, "Latest Tech News!")
        print("Upload successful!")
        return True
    except Exception as e:
        print(f"Failed to upload to Instagram: {e}")
        return False
