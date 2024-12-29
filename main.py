from instaloader import Instaloader, Post
from instagrapi import Client
import re
import os
import string
import shutil
import time
from pyrogram import Client as TgClient

# Initialize the Instagram client for downloading and uploading
L = Instaloader()
client = Client()

# Initialize the Telegram client
tg_client = TgClient("my_account", api_id=os.getenv("API_ID"), api_hash=os.getenv("API_HASH"))
tg_chat_id = os.getenv("CHAT_ID")  # Replace with your chat ID

def sanitize_filename(filename):
    # Remove invalid characters for Windows filenames
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in filename if c in valid_chars).strip()

def linkdownload(link):
    id_pattern = r"(/p/|/reel/)([a-zA-Z0-9_-]+)/"
    match = re.search(id_pattern, link)

    if match:
        id = match.group(2)
        post = Post.from_shortcode(L.context, id)
        print(f"{post} downloading...")

        # Save post caption
        caption = post.caption if post.caption else "No caption available"
        print(f"Post caption: {caption}")

        # Extract first line of caption and limit to 6 words
        first_line = caption.split('\n')[0]
        limited_caption = ' '.join(first_line.split()[:6])
        sanitized_caption = sanitize_filename(limited_caption)

        # Create 'downloads' directory if it doesn't exist
        os.makedirs("downloads", exist_ok=True)  # Ensure the directory exists

        # Download the post to the "downloads" folder
        L.download_post(post, target="downloads")

        # Check the 'downloads' folder to find the video
        files = os.listdir("downloads")
        
        # Find the .mp4 video file (the post's video file)
        video_files = [file for file in files if file.endswith('.mp4')]

        if video_files:
            video_path = os.path.join("downloads", video_files[0])  # Get the first video file found
            new_video_name = f"{sanitized_caption}.mp4"
            new_video_path = os.path.join("downloads", new_video_name)

            # Rename the video file
            os.rename(video_path, new_video_path)
            print(f"Downloaded video saved at: {new_video_path}")
            
            return new_video_path, sanitized_caption  # Return the video path and caption for upload
        else:
            return None, "Error: No video file found in the download folder."
    else:
        return None, "Invalid link! Please provide a valid Instagram post or reel link."

def upload_video(video_path, caption):
    # Log in to Instagram account for uploading
    client.login(os.getenv("INSTAGRAM_USERNAME"), os.getenv("INSTAGRAM_PASSWORD"))

    # Upload the video (this will automatically be treated as a Reel if the video meets the length and aspect ratio requirements)
    client.video_upload(video_path, caption)
    print(f"Reel uploaded successfully with caption: {caption}!")

    # Send Telegram notification
    tg_client.start()
    tg_client.send_message(tg_chat_id, f"Reel uploaded successfully with caption: {caption}!")
    tg_client.stop()

def clean_downloads_folder():
    # Remove all files in the "downloads" folder
    folder = "downloads"
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted {file_path}")
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)  # If there's any subdirectory, remove it

if __name__ == "__main__":
    print("Instagram Post Downloader and Uploader")

    with open("links.txt", "r") as file:
        links = file.readlines()

    for link in links:
        link = link.strip()
        if link:
            # Step 1: Download the video
            video_path, result = linkdownload(link)
            
            if video_path:
                print(f"Video downloaded and renamed: {video_path}")
                
                # Step 2: Upload the downloaded video with caption as filename
                upload_video(video_path, result)
                
                # Step 3: Clean up the downloads folder
                clean_downloads_folder()
                
                # Wait for 3 hours before processing the next link
                time.sleep(10800)
            else:
                print(result)

    print("All processes completed. Cleaning up downloads folder.")
    clean_downloads_folder()
