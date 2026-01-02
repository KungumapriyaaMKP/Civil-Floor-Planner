import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import re

# ----------------------------
# 1️⃣ Parse user input
# ----------------------------
def parse_prompt(prompt):
    prompt = prompt.lower()

    def extract_count(word):
        match = re.search(r"(\d+)\s*" + word, prompt)
        return int(match.group(1)) if match else 0

    layout = {
        "living_room": 1 if "living" in prompt or "hall" in prompt else 0,
        "bedrooms": extract_count("bedroom"),
        "bathrooms": extract_count("bathroom"),
        "kitchen": 1 if "kitchen" in prompt else 0,
        "garage": 1 if "garage" in prompt else 0
    }

    # Fallback if nothing detected
    if sum(layout.values()) == 0:
        layout = {
            "living_room": 1,
            "bedrooms": 1,
            "bathrooms": 1,
            "kitchen": 1,
            "garage": 0
        }

    return layout

# ----------------------------
# 2️⃣ Define objects per room
# ----------------------------
ROOM_OBJECTS = {
    "bedroom": [{"label": "Bed", "color": "#ffab91"}, {"label": "Wardrobe", "color": "#ffe082"}],
    "living_room": [{"label": "Sofa", "color": "#90caf9"}, {"label": "Table", "color": "#ffcc80"}],
    "kitchen": [{"label": "Fridge", "color": "#c5e1a5"}, {"label": "Stove", "color": "#f48fb1"}],
    "bathroom": [{"label": "Toilet", "color": "#b39ddb"}],
    "garage": [{"label": "Car", "color": "#90a4ae"}],
}

# ----------------------------
# 3️⃣ Room Placement Logic (x, y, width, height)
# ----------------------------
def compute_room_positions(layout):
    positions = {}
    start_x, start_y = 50, 50
    x, y = start_x, start_y

    # Living Room
    if layout["living_room"]:
        positions["living_room"] = (x, y, 300, 160)
        x += 320

    # Kitchen
    if layout["kitchen"]:
        positions["kitchen"] = (x, y, 200, 120)
        x = start_x
        y += 180

    # Bedrooms
    for i in range(layout["bedrooms"]):
        key = f"bedroom_{i+1}"
        positions[key] = (x, y, 180, 130)
        x += 200
        if x + 180 > 780:
            x = start_x
            y += 150

    # Bathrooms
    for i in range(layout["bathrooms"]):
        key = f"bathroom_{i+1}"
        positions[key] = (x, y, 140, 100)
        x += 160
        if x + 140 > 780:
            x = start_x
            y += 120

    # Garage
    if layout["garage"]:
        positions["garage"] = (x, y, 250, 150)

    return positions

# ----------------------------
# 4️⃣ Raw 2D Plan
# ----------------------------
def draw_raw_plan(layout, positions):
    img = Image.new("RGB", (800, 500), "white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.load_default()
    except:
        font = None

    for key, (x, y, w, h) in positions.items():
        draw.rectangle([x, y, x + w, y + h], outline="black", width=3)
        label = key.replace("_", " ").title()
        draw.text((x + 5, y + 5), label, fill="black", font=font)

    return img

# ----------------------------
# 5️⃣ 3D Plan with Objects
# ----------------------------
def draw_3d_plan(layout, positions):
    img = Image.new("RGB", (800, 500), "#f4f4f4")
    draw = ImageDraw.Draw(img)
    depth = 15

    try:
        font = ImageFont.load_default()
    except:
        font = None

    for key, (x, y, w, h) in positions.items():
        # Shadow (3D effect)
        draw.rectangle([x + depth, y + depth, x + w + depth, y + h + depth], fill="#cfcfcf")

        # Room color
        color = "#e3f2fd"  # default
        if "bedroom" in key:
            color = "#e8f5e9"
        elif "kitchen" in key:
            color = "#fff9c4"
        elif "bathroom" in key:
            color = "#fce4ec"
        elif "living_room" in key:
            color = "#e3f2fd"
        elif "garage" in key:
            color = "#d7ccc8"

        # Draw room
        draw.rectangle([x, y, x + w, y + h], fill=color, outline="black", width=3)

        # Label
        label = key.replace("_", " ").title()
        draw.text((x + 5, y + 5), label, fill="black", font=font)

        # Draw objects inside room
        room_type = "living_room" if "living" in key else key.split("_")[0]
        objects = ROOM_OBJECTS.get(room_type, [])
        for idx, obj in enumerate(objects):
            obj_w = w // 4
            obj_h = h // 4
            obj_x = x + 5 + (idx % 2) * (obj_w + 5)
            obj_y = y + 25 + (idx // 2) * (obj_h + 5)
            # Ensure objects are inside room
            if obj_x + obj_w > x + w:
                obj_x = x + w - obj_w - 5
            if obj_y + obj_h > y + h:
                obj_y = y + h - obj_h - 5
            draw.rectangle([obj_x, obj_y, obj_x + obj_w, obj_y + obj_h], fill=obj["color"])
            draw.text((obj_x + 2, obj_y + 2), obj["label"], fill="black", font=font)

    return img

# ----------------------------
# 6️⃣ Main pipeline
# ----------------------------
def generate_floor_plans(prompt):
    layout = parse_prompt(prompt)
    positions = compute_room_positions(layout)
    raw = draw_raw_plan(layout, positions)
    three_d = draw_3d_plan(layout, positions)
    return raw, three_d

# ----------------------------
# 7️⃣ Gradio UI
# ----------------------------
demo = gr.Interface(
    fn=generate_floor_plans,
    inputs=gr.Textbox(
        label="Describe your floor plan",
        placeholder="Example: 2 bedrooms, living room with sofa, kitchen with fridge, garage with car, 2 bathrooms"
    ),
    outputs=[
        gr.Image(label="Raw Floor Plan (2D)"),
        gr.Image(label="3D Engineering Floor Plan with Objects")
    ],
    title="VOICE2PLAN-AI (Professional 3D Engineering Floor Plan)",
    description="Generates a technical black & white floor plan and a 3D engineering-style floor plan with objects inside rooms."
)

demo.launch()
