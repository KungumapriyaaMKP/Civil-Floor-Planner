import gradio as gr
from PIL import Image, ImageDraw
import re

# ----------------------------
# Parse prompt
# ----------------------------
def parse_prompt(prompt):
    prompt = prompt.lower()

    def extract_count(word):
        match = re.search(rf"(\d+)\s*{word}", prompt)
        return int(match.group(1)) if match else 0

    layout = {
        "living_room": 1 if "living" in prompt or "hall" in prompt else 0,
        "bedrooms": extract_count("bedroom"),
        "bathrooms": extract_count("bathroom"),
        "kitchen": 1 if "kitchen" in prompt else 0
    }

    if sum(layout.values()) == 0:
        layout = {
            "living_room": 1,
            "bedrooms": 1,
            "bathrooms": 1,
            "kitchen": 1
        }

    return layout


# ----------------------------
# RAW 2D PLAN (Black & White)
# ----------------------------
def draw_raw_plan(layout):
    img = Image.new("RGB", (700, 450), "white")
    draw = ImageDraw.Draw(img)

    x, y = 20, 20

    def room(w, h, label):
        nonlocal x, y
        draw.rectangle([x, y, x + w, y + h], outline="black", width=3)
        draw.text((x + 10, y + 10), label, fill="black")
        y += h + 15

    if layout["living_room"]:
        room(320, 160, "Living Room")

    if layout["kitchen"]:
        room(200, 120, "Kitchen")

    for i in range(layout["bedrooms"]):
        room(220, 130, f"Bedroom {i+1}")

    for i in range(layout["bathrooms"]):
        room(140, 90, f"Bathroom {i+1}")

    return img


# ----------------------------
# 3D-LIKE PLAN (Isometric)
# ----------------------------
def draw_3d_plan(layout):
    img = Image.new("RGB", (800, 500), "#f4f4f4")
    draw = ImageDraw.Draw(img)

    x, y = 80, 80
    depth = 15

    def room(w, h, label, color):
        nonlocal x, y

        # shadow
        draw.rectangle(
            [x + depth, y + depth, x + w + depth, y + h + depth],
            fill="#cfcfcf"
        )

        # top
        draw.rectangle(
            [x, y, x + w, y + h],
            fill=color,
            outline="black",
            width=3
        )

        draw.text((x + 10, y + 10), label, fill="black")
        y += h + 25

    if layout["living_room"]:
        room(350, 170, "Living Room", "#e3f2fd")

    if layout["kitchen"]:
        room(240, 130, "Kitchen", "#fff9c4")

    for i in range(layout["bedrooms"]):
        room(260, 140, f"Bedroom {i+1}", "#e8f5e9")

    for i in range(layout["bathrooms"]):
        room(160, 100, f"Bathroom {i+1}", "#fce4ec")

    return img


# ----------------------------
# Main pipeline
# ----------------------------
def generate_floor_plans(prompt):
    layout = parse_prompt(prompt)
    raw = draw_raw_plan(layout)
    three_d = draw_3d_plan(layout)
    return raw, three_d


# ----------------------------
# UI
# ----------------------------
demo = gr.Interface(
    fn=generate_floor_plans,
    inputs=gr.Textbox(
        label="Describe your floor plan",
        placeholder="Example: 3 bedroom house with living room, kitchen and 2 bathrooms"
    ),
    outputs=[
        gr.Image(label="Raw Floor Plan (2D)"),
        gr.Image(label="3D-Style Floor Plan")
    ],
    title="VOICE2PLAN-AI",
    description="Generates both a technical 2D plan and a 3D-like visualization."
)

demo.launch()
