from PIL import Image
import math

def process_image(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    data = img.getdata()
    
    # The logo has black bars on the sides. Let's find the bounding box of the non-black area.
    # Actually, let's just find the bounding box of the orange pixels.
    orange = (217, 123, 63)
    cream = (245, 241, 232)
    
    new_data = []
    
    min_x, min_y, max_x, max_y = img.width, img.height, 0, 0
    
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img.getpixel((x, y))
            # If it's black (less than say 20,20,20), skip it later by cropping
            # Let's calculate how 'orange' a pixel is compared to 'cream'
            # We assume pixels are a blend of Orange and Cream.
            # Distance to cream
            dist_to_cream = math.sqrt((r - cream[0])**2 + (g - cream[1])**2 + (b - cream[2])**2)
            dist_to_orange = math.sqrt((r - orange[0])**2 + (g - orange[1])**2 + (b - orange[2])**2)
            
            if dist_to_cream < 5:
                # Pure cream -> fully transparent
                new_data.append((orange[0], orange[1], orange[2], 0))
            elif r < 50 and g < 50 and b < 50:
                # Black bars -> transparent
                new_data.append((0, 0, 0, 0))
            else:
                # Calculate alpha based on distance to cream
                # Max distance between cream and orange is ~ 205
                max_dist = math.sqrt((cream[0] - orange[0])**2 + (cream[1] - orange[1])**2 + (cream[2] - orange[2])**2)
                alpha = int(max(0, min(255, 255 * (1 - dist_to_cream / max_dist))))
                
                # We boost alpha a bit to keep it solid
                alpha = int(min(255, alpha * 1.5))
                
                new_data.append((orange[0], orange[1], orange[2], alpha))
                if alpha > 50:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                
    img.putdata(new_data)
    
    # Crop to the logo bounds with some padding
    padding = 20
    min_x = max(0, min_x - padding)
    min_y = max(0, min_y - padding)
    max_x = min(img.width, max_x + padding)
    max_y = min(img.height, max_y + padding)
    
    img = img.crop((min_x, min_y, max_x, max_y))
    img.save(output_path, "PNG")

process_image("../frontend/public/logo.png", "../frontend/public/logo.png")
process_image("../frontend/src/app/icon.png", "../frontend/src/app/icon.png")
