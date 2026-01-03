import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import re

CANVAS_W, CANVAS_H = 900, 550
MARGIN_X, MARGIN_Y = 50, 50


# ======================================================
# 1️⃣ INTENT PARSER (STRICT, NO HALLUCINATION)
# ======================================================
def parse_prompt(prompt):
    prompt = prompt.lower()

    def count(word):
        m = re.search(r"(\d+)\s*" + word, prompt)
        return int(m.group(1)) if m else 0

    layout = {
        "living_room": 1 if any(w in prompt for w in ["living", "hall"]) else 0,
        "bedrooms": count("bedroom"),
        "bathrooms": count("bathroom"),
        "kitchen": 1 if any(w in prompt for w in ["kitchen", "ktchen"]) else 0,
        "garage": 1 if "garage" in prompt else 0
    }

    # Handle "bed" without number
    if layout["bedrooms"] == 0 and "bed" in prompt:
        layout["bedrooms"] = 1

    # Safety: at least one room
    if sum(layout.values()) == 0:
        raise ValueError("No rooms detected. Please specify rooms clearly.")

    return layout


# ======================================================
# 2️⃣ ROOM GEOMETRY ENGINE (DETERMINISTIC)
# ======================================================
def compute_room_positions(layout):
    positions = {}
    x, y = MARGIN_X, MARGIN_Y

    def next_row(h):
        nonlocal x, y
        x = MARGIN_X
        y += h + 40

    # Living room
    if layout["living_room"]:
        positions["living_room"] = (x, y, 320, 180)
        x += 360

    # Kitchen
    if layout["kitchen"]:
        positions["kitchen"] = (x, y, 220, 140)
        next_row(180)

    # Bedrooms
    for i in range(layout["bedrooms"]):
        key = f"bedroom_{i+1}"
        positions[key] = (x, y, 220, 160)
        x += 260
        if x + 220 > CANVAS_W:
            next_row(160)

    # Bathrooms
    for i in range(layout["bathrooms"]):
        key = f"bathroom_{i+1}"
        positions[key] = (x, y, 160, 120)
        x += 200
        if x + 160 > CANVAS_W:
            next_row(120)

    # Garage
    if layout["garage"]:
        positions["garage"] = (x, y, 300, 170)

    return positions


# ======================================================
# 3️⃣ RAW ENGINEERING PLAN (WOW TECHNICAL LOOK)
# ======================================================
def draw_raw_plan(positions):
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "white")
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    for room, (x, y, w, h) in positions.items():
        # Outer wall
        d.rectangle([x, y, x + w, y + h], outline="black", width=4)

        # Door
        door_w = 35
        d.line([x + w//2, y + h, x + w//2 + door_w, y + h], fill="black", width=3)

        # Label
        label = room.replace("_", " ").title()
        d.text((x + 8, y + 6), label, fill="black", font=font)

    return img


# ======================================================
# 4️⃣ 3D ENGINEERING PLAN (DEPTH + FURNITURE)
# ======================================================
ROOM_COLORS = {
    "living_room": "#e3f2fd",
    "bedroom": "#e8f5e9",
    "kitchen": "#fff9c4",
    "bathroom": "#fce4ec",
    "garage": "#d7ccc8"
}

def draw_3d_plan(positions):
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#f0f0f0")
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    depth = 18

    for room, (x, y, w, h) in positions.items():
        base = room.split("_")[0]
        color = ROOM_COLORS.get(base, "#eeeeee")

        # Shadow
        d.rectangle(
            [x + depth, y + depth, x + w + depth, y + h + depth],
            fill="#bdbdbd"
        )

        # Room
        d.rectangle([x, y, x + w, y + h], fill=color, outline="black", width=3)

        # Label
        d.text((x + 8, y + 6), room.replace("_", " ").title(), fill="black", font=font)

        # Furniture (iconic)
        if "bedroom" in room:
            d.rectangle([x+20, y+50, x+120, y+120], fill="#bcaaa4")
        elif "kitchen" in room:
            d.rectangle([x+15, y+40, x+80, y+110], fill="#aed581")
            d.rectangle([x+90, y+40, x+150, y+80], fill="#ffab91")
        elif "living" in room:
            d.rectangle([x+30, y+60, x+150, y+120], fill="#90caf9")
        elif "bathroom" in room:
            d.ellipse([x+50, y+50, x+90, y+90], fill="#b39ddb")
        elif "garage" in room:
            d.rectangle([x+40, y+50, x+200, y+120], fill="#90a4ae")

    return img


# ======================================================
# 5️⃣ MAIN PIPELINE
# ======================================================
def generate_floor_plans(prompt):
    layout = parse_prompt(prompt)
    positions = compute_room_positions(layout)
    raw = draw_raw_plan(positions)
    three_d = draw_3d_plan(positions)
    return raw, three_d


# ======================================================
# 6️⃣ GRADIO APP (HF READY)
# ======================================================
demo = gr.Interface(
    fn=generate_floor_plans,
    inputs=gr.Textbox(
        label="Describe your floor plan",
        placeholder="Example: 1 bedroom and 1 kitchen"
    ),
    outputs=[
        gr.Image(label="Raw Engineering Floor Plan (2D)"),
        gr.Image(label="3D Engineering Floor Plan")
    ],
    title="VOICE2PLAN-AI",
    description="AI-assisted civil engineering floor plan generator with synchronized 2D technical and 3D visualization."
)

demo.launch()
