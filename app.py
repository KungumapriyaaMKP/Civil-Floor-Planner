import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# ----------------------------
# Layout Generator (RULE BASED)
# ----------------------------
def generate_layout(prompt):
    prompt = prompt.lower()

    rooms = []

    if "living" in prompt:
        rooms.append("Living Room")
    if "bedroom" in prompt:
        count = 2 if "2" in prompt else 1
        for i in range(count):
            rooms.append(f"Bedroom {i+1}")
    if "kitchen" in prompt:
        rooms.append("Kitchen")
    if "bathroom" in prompt:
        rooms.append("Bathroom")

    if not rooms:
        rooms = ["Living Room", "Bedroom", "Kitchen"]

    return rooms


# ----------------------------
# Floor Plan Drawer
# ----------------------------
def draw_floor_plan(rooms):
    img = Image.new("RGB", (600, 400), "white")
    draw = ImageDraw.Draw(img)

    x, y = 20, 20
    w, h = 180, 120

    for room in rooms:
        draw.rectangle([x, y, x + w, y + h], outline="black", width=3)
        draw.text((x + 10, y + 50), room, fill="black")

        x += w + 20
        if x + w > 580:
            x = 20
            y += h + 20

    return img


# ----------------------------
# Main Function
# ----------------------------
def generate_floor_plan(prompt):
    rooms = generate_layout(prompt)
    image = draw_floor_plan(rooms)
    return image


# ----------------------------
# Gradio UI
# ----------------------------
demo = gr.Interface(
    fn=generate_floor_plan,
    inputs=gr.Textbox(
        label="Describe your floor plan",
        placeholder="Example: 2 bedroom house with living room and kitchen"
    ),
    outputs=gr.Image(label="Generated Floor Plan"),
    title="VOICE2PLAN-AI (Hybrid Mode)",
    description="Fast, free AI-assisted floor plan generator using rule-based layout."
)

demo.launch()
