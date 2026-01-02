import gradio as gr
from PIL import Image, ImageDraw, ImageFont

import re

# ----------------------------
# 1️⃣ Parse user input
# ----------------------------
def parse_prompt(prompt):
    prompt = prompt.lower()

    # Helper: extract number before keyword, default 0
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

    # If nothing detected, fallback to default
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
# 2️⃣ Object placement inside rooms
# We'll use simple colored rectangles as placeholders for objects
# ----------------------------
def draw_object(draw, x, y, w, h, label, color):
    draw.rectangle([x, y, x + w, y + h], fill=color)
    draw.text((x + 3, y + 3), label, fill="black")


# ----------------------------
# 3️⃣ RAW 2D Plan (Black & White)
# ----------------------------
def draw_raw_plan(layout):
    img = Image.new("RGB", (700, 450), "white")
    draw = ImageDraw.Draw(img)

    x, y = 20, 20

    def room(box_w, box_h, label):
        nonlocal x, y
        draw.rectangle([x, y, x + box_w, y + box_h], outline="black", width=3)
        draw.text((x + 5, y + 5), label, fill="black")
        y += box_h + 15

    if layout["living_room"]:
        room(320, 160, "Living Room")

    if layout["kitchen"]:
        room(200, 120, "Kitchen")

    for i in range(layout["bedrooms"]):
        room(220, 130, f"Bedroom {i+1}")

    for i in range(layout["bathrooms"]):
        room(140, 90, f"Bathroom {i+1}")

    if layout["garage"]:
        room(250, 150, "Garage")

    return img


# ----------------------------
# 4️⃣ 3D Engineering Plan with Objects
# ----------------------------
def draw_3d_plan(layout):
    img = Image.new("RGB", (800, 500), "#f4f4f4")
    draw = ImageDraw.Draw(img)

    depth = 15  # 3D shadow
    start_x, start_y = 50, 50

    # Simple grid positions
    positions = []

    x, y = start_x, start_y

    def room(x, y, w, h, label, color, objects=[]):
        # Shadow
        draw.rectangle([x + depth, y + depth, x + w + depth, y + h + depth], fill="#cfcfcf")
        # Top
        draw.rectangle([x, y, w, h], fill=color, outline="black", width=3)
        draw.text((x + 5, y + 5), label, fill="black")

        # Draw objects inside room
        for obj in objects:
            obj_label = obj["label"]
            obj_color = obj["color"]
            # Simple placeholder inside the room
            obj_w = (w - x) // 4
            obj_h = (h - y) // 4
            obj_x = x + obj["pos"][0] * (w - x)
            obj_y = y + obj["pos"][1] * (h - y)
            draw_object(draw, obj_x, obj_y, obj_x + obj_w, obj_y + obj_h, obj_label, obj_color)

    # Living Room
    if layout["living_room"]:
        room(x, y, x + 300, y + 160, "Living Room", "#e3f2fd",
             objects=[{"label": "Sofa", "color": "#ffcc80", "pos": (0.1,0.6)},
                      {"label": "Table", "color": "#90caf9", "pos": (0.5,0.4)}])
        x += 310

    # Kitchen
    if layout["kitchen"]:
        room(x, y, x + 200, y + 120, "Kitchen", "#fff9c4",
             objects=[{"label": "Fridge", "color": "#c5e1a5", "pos": (0.1,0.2)},
                      {"label": "Stove", "color": "#f48fb1", "pos": (0.5,0.3)}])
        y += 140
        x = start_x

    # Bedrooms
    for i in range(layout["bedrooms"]):
        room(x, y, x + 180, y + 130, f"Bedroom {i+1}", "#e8f5e9",
             objects=[{"label": "Bed", "color": "#ffab91", "pos": (0.2,0.2)}])
        x += 190
        if x + 180 > 780:
            x = start_x
            y += 140

    # Bathrooms
    for i in range(layout["bathrooms"]):
        room(x, y, x + 140, y + 100, f"Bathroom {i+1}", "#fce4ec",
             objects=[{"label": "Toilet", "color": "#b39ddb", "pos": (0.3,0.3)}])
        x += 150
        if x + 140 > 780:
            x = start_x
            y += 110

    # Garage
    if layout["garage"]:
        room(x, y, x + 250, y + 150, "Garage", "#d7ccc8",
             objects=[{"label": "Car", "color": "#90a4ae", "pos": (0.2,0.4)}])

    return img


# ----------------------------
# 5️⃣ Main pipeline
# ----------------------------
def generate_floor_plans(prompt):
    layout = parse_prompt(prompt)
    raw = draw_raw_plan(layout)
    three_d = draw_3d_plan(layout)
    return raw, three_d


# ----------------------------
# 6️⃣ Gradio UI
# ----------------------------
demo = gr.Interface(
    fn=generate_floor_plans,
    inputs=gr.Textbox(
        label="Describe your floor plan",
        placeholder="Example: 2 bedrooms, living room with sofa, kitchen with fridge, garage with car, 2 bathrooms"
    ),
    outputs=[
        gr.Image(label="Raw Floor Plan (2D)"),
        gr.Image(label="3D Engineering Floor Plan")
    ],
    title="VOICE2PLAN-AI (Engineering-Grade 3D)",
    description="Generates a technical black & white floor plan and a 3D engineering-style floor plan with objects."
)

demo.launch()
