import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import re

CANVAS_W, CANVAS_H = 950, 580
MARGIN_X, MARGIN_Y = 50, 50
PX_TO_FT = 0.05
APP_VERSION = "WOW_BUILD_v3"

# ----------------------------
# 1️⃣ Parse prompt strictly
# ----------------------------
def parse_prompt(prompt):
    prompt = prompt.lower()

    def count(word):
        m = re.search(r"(\d+)\s*" + word, prompt)
        return int(m.group(1)) if m else 0

    layout = {
        "living_room": 1 if any(w in prompt for w in ["living", "hall"]) else 0,
        "bedrooms": count("bedroom") or (1 if "bed" in prompt else 0),
        "bathrooms": count("bathroom"),
        "kitchen": 1 if any(w in prompt for w in ["kitchen", "ktchen"]) else 0,
        "garage": 1 if "garage" in prompt else 0
    }

    if sum(layout.values()) == 0:
        raise ValueError("Please specify rooms clearly")
    return layout

# ----------------------------
# 2️⃣ Room placements
# ----------------------------
def compute_room_positions(layout):
    positions = {}
    x, y = MARGIN_X, MARGIN_Y

    def new_row(h):
        nonlocal x, y
        x = MARGIN_X
        y += h + 40

    if layout["living_room"]:
        positions["living_room"] = (x, y, 340, 190)
        x += 380

    if layout["kitchen"]:
        positions["kitchen"] = (x, y, 230, 150)
        new_row(190)

    for i in range(layout["bedrooms"]):
        positions[f"bedroom_{i+1}"] = (x, y, 230, 170)
        x += 270
        if x + 230 > CANVAS_W:
            new_row(170)

    for i in range(layout["bathrooms"]):
        positions[f"bathroom_{i+1}"] = (x, y, 160, 120)
        x += 200
        if x + 160 > CANVAS_W:
            new_row(120)

    if layout["garage"]:
        positions["garage"] = (x, y, 300, 180)

    return positions

# ----------------------------
# 3️⃣ Raw Engineering Floor Plan
# ----------------------------
def draw_raw_plan(positions):
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "white")
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # North arrow
    d.polygon([(880, 60), (870, 90), (890, 90)], fill="black")
    d.text((865, 95), "N", fill="black", font=font)

    for room, (x, y, w, h) in positions.items():
        # Walls
        d.rectangle([x, y, x + w, y + h], outline="black", width=4)

        # Door
        door = 36
        d.arc([x + w // 2 - door, y + h - door, x + w // 2 + door, y + h + door],
              start=180, end=270, fill="black", width=3)

        # Label
        d.text((x + 8, y + 6), room.replace("_", " ").title(), fill="black", font=font)

        # Dimensions
        ft_w = round(w * PX_TO_FT, 1)
        ft_h = round(h * PX_TO_FT, 1)
        d.text((x + w // 2 - 20, y - 14), f"{ft_w} ft", fill="black", font=font)
        d.text((x - 45, y + h // 2), f"{ft_h} ft", fill="black", font=font)

    # Version label
    d.text((10, CANVAS_H - 20), APP_VERSION, fill="black", font=font)
    return img

# ----------------------------
# 4️⃣ 3D Engineering Floor Plan
# ----------------------------
ROOM_COLORS = {
    "living_room": "#e3f2fd",
    "bedroom": "#e8f5e9",
    "kitchen": "#fff9c4",
    "bathroom": "#fce4ec",
    "garage": "#d7ccc8"
}

def draw_3d_plan(positions):
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#efefef")
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    depth = 20

    for room, (x, y, w, h) in positions.items():
        base = room.split("_")[0]
        color = ROOM_COLORS.get(base, "#eeeeee")

        # Shadow
        d.rectangle([x + depth, y + depth, x + w + depth, y + h + depth], fill="#bdbdbd")

        # Room
        d.rectangle([x, y, x + w, y + h], fill=color, outline="black", width=3)
        d.text((x + 8, y + 6), room.replace("_", " ").title(), fill="black", font=font)

        # Furniture icons
        if "bedroom" in room:
            d.rectangle([x + 30, y + 60, x + 150, y + 130], fill="#a1887f")
        elif "kitchen" in room:
            d.rectangle([x + 20, y + 50, x + 90, y + 120], fill="#aed581")
            d.rectangle([x + 100, y + 50, x + 160, y + 90], fill="#ffab91")
        elif "living" in room:
            d.rectangle([x + 40, y + 70, x + 190, y + 140], fill="#90caf9")
        elif "bathroom" in room:
            d.ellipse([x + 50, y + 50, x + 95, y + 95], fill="#b39ddb")
        elif "garage" in room:
            d.rectangle([x + 40, y + 60, x + 220, y + 140], fill="#90a4ae")

    # Version label
    d.text((10, CANVAS_H - 20), APP_VERSION, fill="black", font=font)
    return img

# ----------------------------
# 5️⃣ Main pipeline
# ----------------------------
def generate_floor_plans(prompt):
    layout = parse_prompt(prompt)
    positions = compute_room_positions(layout)
    raw = draw_raw_plan(positions)
    three_d = draw_3d_plan(positions)
    return raw, three_d

# ----------------------------
# 6️⃣ Gradio UI with SSR OFF
# ----------------------------
demo = gr.Interface(
    fn=generate_floor_plans,
    inputs=gr.Textbox(
        label="Describe your floor plan",
        placeholder="Example: 1 bedroom and 1 kitchen"
    ),
    outputs=[
        gr.Image(label="Raw Engineering Floor Plan (2D)", format="png"),
        gr.Image(label="3D Engineering Floor Plan (3D View)", format="png")
    ],
    title="VOICE2PLAN-AI",
    description="Civil floor plan generator with technical 2D and 3D visuals."
)

demo.launch(ssr_mode=False)
