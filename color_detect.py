import cv2
import numpy as np
from sklearn.cluster import KMeans

def detect_color(image_path):
    image = cv2.imread(image_path)

    if image is None:
        print("Image not found! Check file name.")
        return None

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pixels = image.reshape((-1, 3))

    kmeans = KMeans(n_clusters=3)
    kmeans.fit(pixels)

    dominant_color = kmeans.cluster_centers_[0]
    return dominant_color

def get_color_name(rgb):
    r, g, b = rgb
    
    if r > 150 and g < 100 and b < 100:
        return "red"
    elif b > 150 and r < 100:
        return "blue"
    elif g > 150:
        return "green"
    elif r > 200 and g > 200 and b > 200:
        return "white"
    else:
        return "black"
    
def detect_color_name(image_path):
    color_rgb = detect_color(image_path)
    if color_rgb is not None:
        color_name = get_color_name(color_rgb)
        return color_name
    return "unknown"

color_match = {
    "blue": ["black", "white", "grey"],
    "red": ["black", "white"],
    "white": ["black", "blue", "pink"],
    "black": ["white", "grey", "lavender"],
    "green": ["white", "beige"]
}

if __name__ == "__main__":
    color_rgb = detect_color("test.jpg")
    color_name = get_color_name(color_rgb)
    print("Detected Color:", color_name)
    print("Recommended matches:", color_match.get(color_name, []))

# 👇 VERY IMPORTANT — THIS CALLS THE FUNCTION
if __name__ == "__main__":
    color = detect_color("test.jpg")

    if color is not None:
        print("Dominant RGB Color:", color)