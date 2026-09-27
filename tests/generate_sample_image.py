#!/usr/bin/env python3
"""
Generate sample test images (PNG, JPEG) for testing the image processing pipeline.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_sample_image(filename: str, width: int = 1200, height: int = 800, color: tuple = (41, 128, 185)):
    os.makedirs('tests/sample-images', exist_ok=True)
    img = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(img)

    # Draw gradient lines and shapes
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=(color[0] + 20, color[1] + 20, color[2] + 20), width=2)

    # Draw text
    draw.rectangle([width//4, height//4, 3*width//4, 3*height//4], outline=(255, 255, 255), width=4)
    draw.text((width//3, height//2 - 20), f"Test Asset: {filename}", fill=(255, 255, 255))
    draw.text((width//3, height//2 + 20), f"Dimensions: {width}x{height}", fill=(240, 240, 240))

    filepath = os.path.join('tests/sample-images', filename)
    img.save(filepath, quality=90)
    print(f"Created sample image: {filepath} ({os.path.getsize(filepath)} bytes)")

if __name__ == '__main__':
    create_sample_image('sample-landscape.jpg', 1600, 900, (41, 128, 185))
    create_sample_image('sample-portrait.png', 800, 1200, (39, 174, 96))
    create_sample_image('sample-square.jpg', 1000, 1000, (142, 68, 173))
