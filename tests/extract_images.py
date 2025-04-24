import sqlite3
import os
from PIL import Image
from io import BytesIO

def extract_images():
    """Extract image thumbnails from the database and save them to disk."""
    
    # Connect to the database
    db_path = 'output/db.libsql'
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create output directory if it doesn't exist
    output_dir = 'extracted_images'
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    # Get all photo messages
    cursor.execute("""
    SELECT SourceMessageID, ContentType, ContentData 
    FROM chat_messages 
    WHERE ContentType='photo' AND ContentData IS NOT NULL
    """)
    
    results = cursor.fetchall()
    print(f"Found {len(results)} images in the database")
    
    # Save each thumbnail
    for msg_id, content_type, content_data in results:
        # Create a file path
        file_path = os.path.join(output_dir, f"message_{msg_id}.jpg")
        
        # Save the binary data to a file
        try:
            # Open as an image to verify it's valid
            img = Image.open(BytesIO(content_data))
            
            # Save to file
            with open(file_path, 'wb') as f:
                f.write(content_data)
            print(f"Saved {content_type} for message {msg_id} to {file_path}")
        except Exception as e:
            print(f"Error saving message {msg_id}: {e}")
    
    # Also check for other media types
    cursor.execute("""
    SELECT ContentType, COUNT(*) 
    FROM chat_messages 
    WHERE ContentData IS NOT NULL
    GROUP BY ContentType
    """)
    
    content_types = cursor.fetchall()
    print("\nMedia types with data:")
    for content_type, count in content_types:
        print(f"  {content_type}: {count} items")
    
    conn.close()
    print("\nExtraction complete!")

if __name__ == "__main__":
    extract_images() 