cloth_type = predict_cloth("test.jpg")
color_name = detect_color_name("test.jpg")
match = color_match[color_name]

print(f"This is a {color_name} {cloth_type}")
print("You can match it with:", match)
