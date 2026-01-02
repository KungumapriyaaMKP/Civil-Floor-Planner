import gradio as gr
from PIL import Image, ImageDraw
import re

# ----------------------------
# Parse user input intelligently
# ----------------------------
def parse_prompt(prompt):
    prompt = prompt.lower()

    def extract_count(word, default=1):
        match = re.search(rf"(\d+)\s*{word}", prompt)
        return int(match.group(1)) if match else default if word in prompt else 0

    layout = {
        "living_room": 1 if "living" in prompt or "hall" in prompt else 0,
        "bedrooms": extract_count("bedroom"),
        "bathrooms": extract_count("bathroom"),
        "kitchen": 1 if "kitchen" in prompt else 0
    }

    # fallback
    if sum(layout.values()) == 0:
        layout = {
            "living_room": 1,
            "bedrooms": 1,
            "bathrooms": 1,
            "kitchen": 1
        }

    return layout


# ----------------------------
# Draw floor plan dynamically
# ----------------------------
def draw_floor_plan(layout):
    img = Image.new("RGB", (700, 450), "white")
    draw = ImageDraw.Draw(img)

    x, y = 20, 20

    def room(box_w, box_h, label):
        nonlocal x, y
        draw.rectangle([x, y, x + box_w, y + box_h], outline="black", width=3)
        draw.text((x + 10, y + 10), label, fill="black")
        y += box_h + 15

    # Living room (largest)
    if layout["living_room"]:
        room(320, 160, "Living Room")

    # Kitchen
    if layout["kitchen"]:
        room(200, 120, "Kitchen")

    # Bedrooms
    for i in range(layout["bedrooms"]):
        room(220, 130, f"Bedroom {i+1}")

    # Bathrooms
    for i in range(layout["bathrooms"]):
        room(140, 90, f"Bathroom {i+1}")

    return img


# ----------------------------
# Main pipeline
# ----------------------------
def generate_floor_plan(prompt):
    layout = parse_prompt(prompt)
    image = draw_floor_plan(layout)
    return image


# ----------------------------
# UI
# ----------------------------
demo = gr.Interface(
    fn=generate_floor_plan,
    inputs=gr.Textbox(
        label="Describe your floor plan",
        placeholder="Example: 3 bedroom house with kitchen and 2 bathrooms"
    ),
    outputs=gr.Image(label="Generated Floor Plan"),
    title="VOICE2PLAN-AI (Adaptive Layout)",
    description="Understands user changes and dynamically modifies the floor plan."
)

demo.launch()
