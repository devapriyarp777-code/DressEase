import os
import uuid
import shutil
from flask import Flask, render_template, request, redirect, url_for
from ai_engine import generate_outfit, map_event_to_style, find_match_from_wardrobe, load_wardrobe
from werkzeug.utils import secure_filename
from predict import predict_cloth
from color_detect import detect_color_name
# Keeping ML imports if user still wants manual upload logic later,
# but using only predefined reqs right now.

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@app.route("/")
def index():
    # Redirect root to generator
    return redirect(url_for("generator"))

@app.route("/generator", methods=["GET"])
def generator():
    """Renders the AI Outfit Generator selection form."""
    return render_template("generator.html")

@app.route("/generate", methods=["POST"])
def generate():
    """Handles the form submission and passes it to the AI engine."""
    mood = request.form.get("mood")
    occasion = request.form.get("occasion")
    
    top, bottom = generate_outfit(mood, occasion)
    
    return render_template("generator.html", top=top, bottom=bottom, search_mood=mood, search_occasion=occasion)

@app.route("/match", methods=["GET"])
def match():
    """Renders the image upload form for finding a match."""
    return render_template("match.html")

@app.route("/find_match", methods=["POST"])
def find_match_route():
    """Handles the image upload, runs ML models, and returns an AI recommended match."""
    if "image" not in request.files:
        return redirect(url_for("match"))
        
    file = request.files["image"]
    
    if file.filename == "":
        return redirect(url_for("match"))
        
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        
        # Run ML Models
        detected_type = predict_cloth(filepath)
        detected_color = detect_color_name(filepath)
        
        # Get AI Match
        matched_item = find_match_from_wardrobe(detected_type, detected_color)
        
        # Render results natively side-by-side
        return render_template(
            "match.html",
            uploaded_image=f"uploads/{filename}",
            detected_type=detected_type,
            detected_color=detected_color,
            matched_item=matched_item
        )
    
    return redirect(url_for("match"))

from calendar_engine import get_all_events, add_event
import calendar
import datetime

@app.route("/calendar")
def view_calendar():
    """Displays a dynamic monthly calendar layout with events."""
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    
    # get a matrix of days. calendar.monthcalendar(year, month) returns a list of weeks.
    # Each week is a list of 7 days (Monday=0 ... Sunday=6). 
    # The user requested (Sun-Sat), so we will adjust it down below.
    calendar.setfirstweekday(calendar.SUNDAY)
    month_days = calendar.monthcalendar(year, month)
    
    events = get_all_events()
    month_name = calendar.month_name[month]
    
    return render_template(
        "calendar.html", 
        month_days=month_days, 
        current_month=month, 
        current_year=year,
        month_name=month_name,
        events=events
    )

@app.route("/add_event", methods=["POST"])
def add_event_route():
    """POST route to add a new event to the calendar."""
    date_str = request.form.get("date")
    title = request.form.get("title")
    description = request.form.get("description")
    
    if date_str and title:
        add_event(date_str, title, description)
        
    return redirect(url_for("view_calendar"))

@app.route("/event/<date>")
def view_event(date):
    """Specific route to view an event and automatically generate an outfit."""
    now = datetime.datetime.now()
    try:
        dt = datetime.datetime.strptime(date, "%Y-%m-%d")
        year = dt.year
        month = dt.month
    except ValueError:
        year = now.year
        month = now.month
        
    calendar.setfirstweekday(calendar.SUNDAY)
    month_days = calendar.monthcalendar(year, month)
    
    events = get_all_events()
    month_name = calendar.month_name[month]
    
    event = events.get(date)
    active_event = None
    
    if event:
        mood, occasion, color_hint = map_event_to_style(event["title"], event.get("description", ""))
        top, bottom = generate_outfit(mood, occasion, color_hint)
        
        active_event = {
            "date": date,
            "title": event["title"],
            "description": event["description"],
            "mood": mood,
            "occasion": occasion,
            "top": top,
            "bottom": bottom
        }
    else:
        return redirect(url_for("view_calendar"))
        
    return render_template(
        "calendar.html", 
        month_days=month_days, 
        current_month=month, 
        current_year=year,
        month_name=month_name,
        events=events,
        active_event=active_event
    )

@app.route("/upload_wardrobe", methods=["POST"])
def upload_wardrobe():
    """Handles uploading a new wardrobe item, auto-tags it with ML, and saves it."""
    if "wardrobe_image" not in request.files:
        return redirect(url_for("my_wardrobe"))
        
    file = request.files["wardrobe_image"]
    
    if file.filename == "":
        return redirect(url_for("my_wardrobe"))
        
    if file:
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(temp_path)
        
        # Run ML Models
        detected_type = predict_cloth(temp_path)
        detected_color = detect_color_name(temp_path)
        
        # Determine new filename systematically
        ext = os.path.splitext(filename)[1].lower()
        if not ext:
            ext = ".jpg"
        unique_id = str(uuid.uuid4())[:8]
        new_filename = f"{detected_type}_{detected_color}_{unique_id}{ext}"
        
        # Move to static/wardrobe directory
        wardrobe_dir = os.path.join(app.root_path, "static", "wardrobe")
        os.makedirs(wardrobe_dir, exist_ok=True)
        final_path = os.path.join(wardrobe_dir, new_filename)
        
        shutil.move(temp_path, final_path)
        
        return redirect(url_for("my_wardrobe"))
        
    return redirect(url_for("my_wardrobe"))

@app.route("/wardrobe")
def my_wardrobe():
    """Dynamically loads and displays all wardrobe items from static/wardrobe directory."""
    items = load_wardrobe()
    images = [item["image"] for item in items]
    return render_template("wardrobe.html", images=images)

@app.route("/liked")
def liked():
    """Placeholder view for liked outfits in a structured grid layout."""
    # Dummy data structure to hold "liked" combinations before DB implementation
    liked_outfits = [
        {"top": "wardrobe/shirt_blue.jpg", "bottom": "wardrobe/pant_black.jpg"},
        {"top": "wardrobe/kurthi_red.jpg", "bottom": "wardrobe/pant_grey.jpg"}
    ]
    return render_template("liked.html", liked_outfits=liked_outfits)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))