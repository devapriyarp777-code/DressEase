import random
import os

type_pair_rules = {
    "shirt": ["pant"],
    "kurthi": ["pant"],
    "pant": ["shirt", "kurthi"],
    "jacket": ["dress", "pant"], # pant included to be safe, but dress is primary
    "dress": ["jacket"],
    "top": ["pant"]
}

color_match = {
    "black": ["white", "red", "grey", "blue"],
    "white": ["black", "blue", "grey"],
    "blue": ["black", "grey", "white"],
    "red": ["black", "white"],
    "grey": ["blue", "black", "white"],
    "yellow": ["black", "white"],
    "lavender": ["black", "white"],
    "green": ["white", "black"]
}

# Keep track of last generated pair to avoid consecutive duplicates
last_generated_pair = {"top": None, "bottom": None}

def extract_metadata_from_filename(filename):
    """Dynamically extracts type, color, and implicitly assigns mood/occasion."""
    # Example: 'shirt_blue.jpg'
    basename = os.path.splitext(filename)[0].lower()
    parts = basename.split('_')
    
    item_type = parts[0] if len(parts) > 0 else "unknown"
    item_color = parts[1] if len(parts) > 1 else "unknown"
    
    # Implicit assignment for mood and occasion so filtering still works natively
    mood = "chill"
    occasion = "casual"
    
    if item_color in ["black", "white"]:
        mood = "confident"
        occasion = "formal"
    elif item_color in ["red", "lavender", "yellow"]:
        mood = "happy"
        occasion = "party"
        
    return {
        "image": f"wardrobe/{filename}",
        "type": item_type,
        "color": item_color,
        "mood": mood,
        "occasion": occasion
    }

def load_wardrobe():
    """Scans static/wardrobe directory and dynamically returns the wardrobe list."""
    wardrobe_list = []
    # Assumes ai_engine.py is in the root alongside app.py and static/
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "wardrobe")
    
    if os.path.exists(base_dir):
        extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
        for f in os.listdir(base_dir):
            if f.lower().endswith(extensions):
                wardrobe_list.append(extract_metadata_from_filename(f))
                
    return wardrobe_list

def score_match(ref_color, target_color):
    """
    Scores the color compatibility:
    +2 for directly compatible color
    +1 for neutral matching (black/white/grey)
    0 for no logical match or identical clashes
    """
    if ref_color == target_color:
        return 0 # Avoid monochrome clashes unless strictly unavoidable
        
    explicit_matches = color_match.get(ref_color, [])
    if target_color in explicit_matches:
        return 2
        
    if target_color in ["black", "white", "grey"]:
        return 1
        
    return 0

def generate_outfit(mood, occasion, color_hint=None):
    """Generates an outfit based on mood, occasion, color hints, and strict rules."""
    global last_generated_pair
    wardrobe = load_wardrobe()
    if not wardrobe:
        return None, None
        
    # Split wardrobe into generic tops and bottoms for initial filtering
    tops = [w for w in wardrobe if w["type"] in ["shirt", "kurthi", "dress", "jacket", "top"]]
    bottoms = [w for w in wardrobe if w["type"] in ["pant"]]
    
    # If no natural tops or bottoms exist, the generator cannot work properly
    if not tops or not bottoms:
         # Try to randomly pick two different things as an extreme fallback
         if len(wardrobe) >= 2:
             return wardrobe[0], wardrobe[1]
         return None, None
         
    # Filter by constraints
    filtered_tops = [t for t in tops if t["mood"] == mood and t["occasion"] == occasion]
    filtered_bottoms = [b for b in bottoms if b["mood"] == mood and b["occasion"] == occasion]
    
    if not filtered_tops: filtered_tops = [t for t in tops if t["occasion"] == occasion] or tops
    if not filtered_bottoms: filtered_bottoms = [b for b in bottoms if b["occasion"] == occasion] or bottoms
    
    # Apply color hint specifically to force priority
    if color_hint:
        hint_tops = [t for t in filtered_tops if t["color"] == color_hint]
        if hint_tops: filtered_tops = hint_tops
        hint_bottoms = [b for b in filtered_bottoms if b["color"] == color_hint]
        if hint_bottoms: filtered_bottoms = hint_bottoms

    # Score all valid matching combinations based on type rules
    scored_combinations = []
    
    for t in filtered_tops:
        compatible_bottom_types = type_pair_rules.get(t["type"], [])
        valid_bottoms = [b for b in filtered_bottoms if b["type"] in compatible_bottom_types]
        
        for b in valid_bottoms:
            # Score them based on color correlation
            score = score_match(t["color"], b["color"])
            
            # Avoid consecutive repeats
            if last_generated_pair["top"] == t["image"] and last_generated_pair["bottom"] == b["image"]:
                score -= 5 # heavily penalize the exact same outfit we just showed
                
            scored_combinations.append({"top": t, "bottom": b, "score": score})
            
    if not scored_combinations:
        # Extreme fallback if strict rules break entirely
        t = random.choice(filtered_tops)
        b = random.choice(filtered_bottoms)
        last_generated_pair = {"top": t["image"], "bottom": b["image"]}
        return t, b
        
    # Sort and pick the best score
    scored_combinations.sort(key=lambda x: x["score"], reverse=True)
    best_score = scored_combinations[0]["score"]
    
    # Collect all combos with the best score and randomly shuffle to prevent identical returns
    best_options = [c for c in scored_combinations if c["score"] == best_score]
    choice = random.choice(best_options)
    
    last_generated_pair = {"top": choice["top"]["image"], "bottom": choice["bottom"]["image"]}
    return choice["top"], choice["bottom"]

def find_match_from_wardrobe(cloth_type, color):
    """
    Given an uploaded cloth type and color, scans the dynamic wardrobe using
    strict type rules and intelligent color scoring to return the best match.
    """
    wardrobe = load_wardrobe()
    if not wardrobe:
        return None
        
    # Strict Type Pairing Rule Check
    compatible_target_types = type_pair_rules.get(cloth_type, [])
    
    # If the ML model outputs something random that has no rules, default to pant
    if not compatible_target_types:
        compatible_target_types = ["pant"]
        
    valid_candidates = [item for item in wardrobe if item["type"] in compatible_target_types]
    
    # Safety Check
    if not valid_candidates:
        # Fallback to opposite general class if strict logic leads to no results
        is_top = cloth_type in ["shirt", "kurthi", "dress", "top", "jacket"]
        backup_type = "bottom" if is_top else "top"
        valid_candidates = [item for item in wardrobe if 
                            (backup_type == "bottom" and item["type"] == "pant") or 
                            (backup_type == "top" and item["type"] in ["shirt", "kurthi", "dress"])]
                            
    if not valid_candidates:
        return None # Entire wardrobe empty or unusable
        
    # Score candidates intelligently
    scored_candidates = []
    for cand in valid_candidates:
        # DO NOT return the same image (if uploaded from wardrobe) - technically impossible since upload is external, 
        # but to satisfy "Never return same image" rule logically:
        if cand["type"] == cloth_type and cand["color"] == color:
            continue # skip identical clones
            
        score = score_match(color, cand["color"])
        scored_candidates.append({"item": cand, "score": score})
        
    if not scored_candidates:
         return random.choice(valid_candidates)
         
    # Select best scoring candidate, randomize if multiple tied
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    best_score = scored_candidates[0]["score"]
    best_options = [c["item"] for c in scored_candidates if c["score"] == best_score]
    
    return random.choice(best_options)

def map_event_to_style(event_title, event_desc=""):
    """Maps an event title to a corresponding mood, occasion, and an optional color hint based on keywords."""
    text_lower = (event_title + " " + event_desc).lower()
    
    colors = ["red", "blue", "white", "black", "grey", "yellow", "lavender", "green", "brown"]
    color_hint = next((c for c in colors if c in text_lower), None)
    
    if "date" in text_lower:
        return "happy", "party", color_hint
    elif "meeting" in text_lower or "office" in text_lower:
        return "confident", "formal", color_hint
    elif "party" in text_lower:
        return "happy", "party", color_hint
    elif "casual" in text_lower:
        return "chill", "casual", color_hint
        
    return "chill", "casual", color_hint