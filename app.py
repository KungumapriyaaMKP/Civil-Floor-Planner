import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# ----------------------------
# Parsing
# ----------------------------
def parse_plot_size(text):
    w, h = text.lower().replace(" ", "").split("x")
    return int(w), int(h)

def parse_rooms(text):
    rooms = []
    for line in text.strip().split("\n"):
        parts = line.split(",")
        rooms.append({
            "name": parts[0].strip(),
            "w": int(parts[1]),
            "h": int(parts[2]),
            "pos": parts[3].strip().lower() if len(parts) > 3 else "any"
        })
    return rooms

# ----------------------------
# Raw plan generator
# ----------------------------
def generate_raw_plan(plot_size, room_text):
    plot_w, plot_h = parse_plot_size(plot_size)
    rooms = parse_rooms(room_text)

    CANVAS_W, CANVAS_H = 900, 600
    MARGIN = 40

    scale = min(
        (CANVAS_W - 2 * MARGIN) / plot_w,
        (CANVAS_H - 2 * MARGIN) / plot_h
    )

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#f2f2f2")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # Plot boundary
    px0, py0 = MARGIN, MARGIN
    px1 = px0 + int(plot_w * scale)
    py1 = py0 + int(plot_h * scale)

    draw.rectangle([px0, py0, px1, py1], outline="black", width=6)
    draw.text((px0, py0 - 15), f"PLOT {plot_w} x {plot_h}", fill="black", font=font)

    placed = {}
    padding = 10

    # First pass: absolute positions
    for room in rooms:
        rw = int(room["w"] * scale)
        rh = int(room["h"] * scale)
        pos = room["pos"]

        if pos == "top-right":
            x = px1 - rw - padding
            y = py0 + padding
        elif pos == "top-left":
            x = px0 + padding
            y = py0 + padding
        elif pos == "bottom-left":
            x = px0 + padding
            y = py1 - rh - padding
        elif pos == "bottom-right":
            x = px1 - rw - padding
            y = py1 - rh - padding
        elif pos == "entrance":
            x = px0 + (px1 - px0) // 2 - rw // 2
            y = py1 - rh - padding
        else:
            continue

        placed[room["name"].lower()] = (x, y, rw, rh)

    # Second pass: relative & auto
    cursor_x = px0 + padding
    cursor_y = py0 + padding + 150

    for room in rooms:
        name = room["name"].lower()
        if name in placed:
            continue

        rw = int(room["w"] * scale)
        rh = int(room["h"] * scale)
        pos = room["pos"]

        if pos == "left-of-kitchen" and "kitchen" in placed:
            kx, ky, kw, kh = placed["kitchen"]
            x = kx - rw - padding
            y = ky
        else:
            if cursor_x + rw > px1:
                cursor_x = px0 + padding
                cursor_y += rh + 20
            x = cursor_x
            y = cursor_y
            cursor_x += rw + 20

        placed[name] = (x, y, rw, rh)

    # Draw rooms
    for room in rooms:
        name = room["name"].lower()
        x, y, rw, rh = placed[name]

        draw.rectangle([x, y, x + rw, y + rh], outline="black", width=4)
        label = f'{room["name"]}\n{room["w"]}x{room["h"]}'
        draw.text((x + 5, y + 5), label, fill="black", font=font)

    return img

# ----------------------------
# UI
# ----------------------------
demo = gr.Interface(
    fn=generate_raw_plan,
    inputs=[
        gr.Textbox(label="Plot Size (W x H)", placeholder="40x30"),
        gr.Textbox(
            label="Rooms (Name,Width,Height,Position)",
            lines=7,
            placeholder=(
                "Bedroom,12,10,top-right\n"
                "Kitchen,8,7,center\n"
                "Pooja,5,5,left-of-kitchen\n"
                "Garage,14,10,entrance\n"
                "Bathroom,6,5,any"
            )
        )
    ],
    outputs=gr.Image(label="Raw Civil Floor Plan"),
    title="VOICE2PLAN-AI | Constraint-Based Civil Floor Plan Engine",
    description="Rule-driven room placement with civil & vastu constraints."
)

demo.launch()
