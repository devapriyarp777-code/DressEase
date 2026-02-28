import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image

# Load model once globally
try:
    model = tf.keras.models.load_model("cloth_classifier.h5")
except:
    model = None
    print("Warning: cloth_classifier.h5 could not be loaded")

def predict_cloth(img_path):
    if model is None:
        return "unknown"
        
    try:
        # Load image
        img = image.load_img(img_path, target_size=(224,224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0

        # Predict
        prediction = model.predict(img_array)

        # IMPORTANT: write class names in SAME ORDER as training folders
        class_names = ['dress', 'jacket', 'kurthi', 'pant', 'shirt']
        
        predicted_class = class_names[np.argmax(prediction)]
        print(f"Prediction for {img_path}: {predicted_class}")
        return predicted_class
    except Exception as e:
        print(f"Error predicting cloth for {img_path}: {e}")
        return "unknown"

if __name__ == "__main__":
    # CHANGE this to your test image path
    test_img = "test.jpg"
    print(f"Testing prediction on {test_img}")
    result = predict_cloth(test_img)
    print(f"Final Predicted Class: {result}")
