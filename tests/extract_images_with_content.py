import sqlite3
import os
from PIL import Image
from io import BytesIO
import shutil
import json

def extract_images_with_content():
    """Extract image thumbnails from the database and save them to disk with their associated message content."""
    
    # Connect to the database
    db_path = 'output/db.libsql'
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create output directory if it doesn't exist
    output_dir = 'extracted_images_with_content'
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    # Get all photo messages with their content
    cursor.execute("""
    SELECT SourceMessageID, SenderID, ContentType, Content, ContentData, MessageDate
    FROM chat_messages 
    WHERE ContentType='photo' AND ContentData IS NOT NULL
    ORDER BY MessageDate DESC
    """)
    
    results = cursor.fetchall()
    print(f"Found {len(results)} images in the database")
    
    # Create a JSON file to store the image metadata
    metadata = []
    
    # Save each thumbnail
    for msg_id, sender_id, content_type, content, content_data, message_date in results:
        # Create a file path
        file_path = os.path.join(output_dir, f"message_{msg_id}.jpg")
        
        # Save the binary data to a file
        try:
            # Open as an image to verify it's valid
            img = Image.open(BytesIO(content_data))
            dimensions = f"{img.width}x{img.height}"
            
            # Save to file
            with open(file_path, 'wb') as f:
                f.write(content_data)
            
            # Add metadata
            metadata.append({
                'message_id': msg_id,
                'sender_id': sender_id,
                'content_type': content_type,
                'content': content[:100] + "..." if content and len(content) > 100 else content,
                'message_date': message_date,
                'image_path': file_path,
                'dimensions': dimensions,
                'size_bytes': len(content_data)
            })
            
            print(f"Saved {content_type} for message {msg_id} to {file_path}")
        except Exception as e:
            print(f"Error saving message {msg_id}: {e}")
    
    # Save metadata to JSON file
    metadata_path = os.path.join(output_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Saved metadata to {metadata_path}")
    
    # Create a simple HTML viewer
    html_path = os.path.join(output_dir, 'gallery.html')
    with open(html_path, 'w') as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Extracted Images Gallery</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        h1 { color: #333; }
        .gallery { display: flex; flex-wrap: wrap; gap: 20px; }
        .image-card { 
            border: 1px solid #ddd; 
            padding: 15px; 
            width: 300px; 
            background-color: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .image-container { height: 150px; display: flex; justify-content: center; align-items: center; }
        img { max-width: 100%; max-height: 150px; }
        .image-meta { margin-top: 10px; }
        .content { margin-top: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }
        .date { color: #666; font-size: 0.8em; }
    </style>
</head>
<body>
    <h1>Extracted Images from Telegram Chats</h1>
    <div class="gallery">
""")
        
        # Add each image to the gallery
        for item in metadata:
            img_filename = os.path.basename(item['image_path'])
            f.write(f"""
        <div class="image-card">
            <div class="image-container">
                <img src="{img_filename}" alt="Message {item['message_id']}">
            </div>
            <div class="image-meta">
                <strong>ID:</strong> {item['message_id']}<br>
                <strong>Size:</strong> {item['dimensions']} ({item['size_bytes']} bytes)<br>
                <strong>Date:</strong> <span class="date">{item['message_date']}</span>
            </div>
            <div class="content">
                {item['content'] or 'No caption'}
            </div>
        </div>
""")
        
        f.write("""
    </div>
</body>
</html>
""")
    
    print(f"Created HTML gallery at {html_path}")
    print("\nExtraction complete!")

if __name__ == "__main__":
    extract_images_with_content() 