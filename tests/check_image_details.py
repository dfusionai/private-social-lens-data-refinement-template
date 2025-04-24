from PIL import Image
import os

def check_image_details():
    """Print details about the extracted images."""
    
    image_dir = "extracted_images"
    
    # Get all jpg files in the directory
    image_files = [f for f in os.listdir(image_dir) if f.endswith('.jpg')]
    
    print(f"Found {len(image_files)} images")
    print("\nImage details:")
    print("-" * 60)
    print(f"{'Filename':<25} {'Format':<10} {'Size':<15} {'Dimensions':<15}")
    print("-" * 60)
    
    # Sample the first 5 images
    for image_file in sorted(image_files)[:5]:
        file_path = os.path.join(image_dir, image_file)
        file_size = os.path.getsize(file_path)
        
        try:
            # Open the image and get its details
            with Image.open(file_path) as img:
                img_format = img.format
                img_dimensions = f"{img.width}x{img.height}"
                
                print(f"{image_file:<25} {img_format:<10} {file_size} bytes {img_dimensions:<15}")
        except Exception as e:
            print(f"{image_file:<25} ERROR: {str(e)}")
    
    print("-" * 60)
    print("... and more images")

if __name__ == "__main__":
    check_image_details() 