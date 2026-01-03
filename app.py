import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# ----------------------------
# Helper functions
# ----------------------------
def parse_plot_size(text):
    try:
        w, h = text.lower().replace(" ", "").split("x")
        return int(w), int(h)
    except:
        raise ValueError("Plot size must be in format WidthxHeight, e.g., 40x30")

def parse_rooms(text):
    rooms = []
    for line in text.strip().split("\n"):
        parts = line.split(",")
        if len(parts) < 3:
            continue
        rooms.append({
            "name": parts[0].strip(),
            "w": int(parts[1]),
            "h": int(parts[2]),
            "pos": parts[3].strip().lower() if len(parts) > 3 else "any"
        })
    return rooms

def check_overlap(x, y, rw, rh, placed_rooms):
    """Returns True if the rectangle overlaps with any placed room"""
    for px, py, pw, ph in placed_rooms.values():
        if (x < px + pw and x + rw > px and y < py + ph and y + rh > py):
            return True
    return False

# ----------------------------
# Floor plan generator
# ----------------------------
def generate_raw_plan(plot_size, room_text):
    # Parse inputs
    plot_w, plot_h = parse_plot_size(plot_size)
    rooms = parse_rooms(room_text)

    # Canvas settings
    CANVAS_W, CANVAS_H = 900, 600
    MARGIN = 40
    PADDING = 10

    scale = min(
        (CANVAS_W - 2 * MARGIN) / plot_w,
        (CANVAS_H - 2 * MARGIN) / plot_h
    )

    # Image setup
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#f2f2f2")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    # Draw plot boundary
    px0, py0 = MARGIN, MARGIN
    px1 = px0 + int(plot_w * scale)
    py1 = py0 + int(plot_h * scale)
    draw.rectangle([px0, py0, px1, py1], outline="black", width=6)
    draw.text((px0, py0 - 20), f"PLOT {plot_w} x {plot_h}", fill="black", font=font)

    placed = {}

    # ----------------------------
    # First pass: absolute positions
    # ----------------------------
    for room in rooms:
        rw = int(room["w"] * scale)
        rh = int(room["h"] * scale)
        pos = room["pos"]

        if pos == "top-right":
            x = px1 - rw - PADDING
            y = py0 + PADDING
        elif pos == "top-left":
            x = px0 + PADDING
            y = py0 + PADDING
        elif pos == "bottom-left":
            x = px0 + PADDING
            y = py1 - rh - PADDING
        elif pos == "bottom-right":
            x = px1 - rw - PADDING
            y = py1 - rh - PADDING
        elif pos == "center":
            x = px0 + (px1 - px0)//2 - rw//2
            y = py0 + (py1 - py0)//2 - rh//2
        elif pos == "entrance":
            x = px0 + (px1 - px0)//2 - rw//2
            y = py1 - rh - PADDING
        else:
            continue

        # Avoid overlap
        attempts = 0
        while check_overlap(x, y, rw, rh, placed) and attempts < 100:
            y += 10
            if y + rh > py1:
                y = py0 + PADDING
                x += 10
            attempts += 1
        placed[room["name"].lower()] = (x, y, rw, rh)

    # ----------------------------
    # Second pass: relative & auto
    # ----------------------------
    cursor_x = px0 + PADDING
    cursor_y = py0 + PADDING + 150

    for room in rooms:
        name = room["name"].lower()
        if name in placed:
            continue

        rw = int(room["w"] * scale)
        rh = int(room["h"] * scale)
        pos = room["pos"]

        # Relative positions
        if "left-of-" in pos:
            target_name = pos.replace("left-of-", "")
            if target_name in placed:
                tx, ty, tw, th = placed[target_name]
                x = tx - rw - PADDING
                y = ty
            else:
                x, y = cursor_x, cursor_y
        elif "right-of-" in pos:
            target_name = pos.replace("right-of-", "")
            if target_name in placed:
                tx, ty, tw, th = placed[target_name]
                x = tx + tw + PADDING
                y = ty
            else:
                x, y = cursor_x, cursor_y
        else:
            x, y = cursor_x, cursor_y

        # Avoid overlap
        attempts = 0
        while check_overlap(x, y, rw, rh, placed) and attempts < 100:
            x += 10
            if x + rw > px1:
                x = px0 + PADDING
                y += 10
            attempts += 1
        placed[name] = (x, y, rw, rh)

        cursor_x = x + rw + 20
        if cursor_x + rw > px1:
            cursor_x = px0 + PADDING
            cursor_y += rh + 20

    # ----------------------------
    # Draw rooms
    # ----------------------------
    for room in rooms:
        name = room["name"].lower()
        x, y, rw, rh = placed[name]

        draw.rectangle([x, y, x + rw, y + rh], outline="black", width=4)
        label = f'{room["name"]}\n{room["w"]}x{room["h"]}'
        for i, line in enumerate(label.split("\n")):
            draw.text((x + 5, y + 5 + i*14), line, fill="black", font=font)

    return img

# ----------------------------
# Gradio UI
# ----------------------------
demo = gr.Interface(
    fn=generate_raw_plan,
    inputs=[
        gr.Textbox(label="Plot Size (W x H)", placeholder="40x30"),
        gr.Textbox(
            label="Rooms (Name,Width,Height,Position)",
            lines=10,
            placeholder=(
                "Bedroom,12,10,top-right\n"
                "Kitchen,8,7,center\n"
                "Pooja,5,5,left-of-kitchen\n"
                "Garage,14,10,entrance\n"
                "Bathroom,6,5,any\n"
                "Living Room,10,12,bottom-left\n"
                "Study,6,6,right-of-bedroom"
            )
        )
    ],
    outputs=gr.Image(label="Raw Civil Floor Plan"),
    title="VOICE2PLAN-AI | Constraint-Based Civil Floor Plan Engine",
    description="Rule-driven room placement with civil & vastu constraints."
)

# ----------------------------
# Launch app
# ----------------------------
if __name__ == "__main__":
    demo.launch()
