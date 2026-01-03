import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# ----------------------------
# Helpers
# ----------------------------
def parse_plot_size(text):
    w, h = text.lower().replace(" ", "").split("x")
    return int(w), int(h)

def parse_rooms(text):
    rooms = []
    for line in text.strip().split("\n"):
        parts = line.split(",")
        if len(parts) < 3:
            continue
        rooms.append({
            "name": parts[0].strip(),
            "name_lower": parts[0].strip().lower(),
            "w": int(parts[1]),
            "h": int(parts[2]),
            "pos": parts[3].strip().lower() if len(parts) > 3 else "any"
        })
    return rooms

def check_overlap(x, y, rw, rh, placed, ignore=None):
    for k, (px, py, pw, ph) in placed.items():
        if k == ignore:
            continue
        if x < px + pw and x + rw > px and y < py + ph and y + rh > py:
            return True
    return False

# ----------------------------
# Core layout engine (unchanged logic)
# ----------------------------
def compute_layout(plot_w, plot_h, rooms, scale, px0, py0, px1, py1):
    PADDING = 10
    placed = {}

    direction_map = {
        "left-of": lambda tx, ty, tw, th, rw, rh: (tx - rw - PADDING, ty),
        "right-of": lambda tx, ty, tw, th, rw, rh: (tx + tw + PADDING, ty),
        "top-of": lambda tx, ty, tw, th, rw, rh: (tx, ty - rh - PADDING),
        "bottom-of": lambda tx, ty, tw, th, rw, rh: (tx, ty + th + PADDING),
    }

    # First pass (absolute)
    for r in rooms:
        rw, rh = int(r["w"] * scale), int(r["h"] * scale)
        pos = r["pos"]
        name = r["name_lower"]

        if pos == "top-left":
            x, y = px0 + PADDING, py0 + PADDING
        elif pos == "top-right":
            x, y = px1 - rw - PADDING, py0 + PADDING
        elif pos == "bottom-left":
            x, y = px0 + PADDING, py1 - rh - PADDING
        elif pos == "bottom-right":
            x, y = px1 - rw - PADDING, py1 - rh - PADDING
        elif pos == "center":
            x = px0 + (px1 - px0)//2 - rw//2
            y = py0 + (py1 - py0)//2 - rh//2
        else:
            continue

        placed[name] = (x, y, rw, rh)

    # Second pass (relative / auto)
    cx, cy = px0 + PADDING, py0 + 150

    for r in rooms:
        name = r["name_lower"]
        if name in placed:
            continue

        rw, rh = int(r["w"] * scale), int(r["h"] * scale)
        pos = r["pos"]

        if "-of-" in pos:
            d, t = pos.split("-of-")
            t = t.strip().lower()
            if t in placed:
                tx, ty, tw, th = placed[t]
                x, y = direction_map[d + "-of"](tx, ty, tw, th, rw, rh)
            else:
                x, y = cx, cy
        else:
            x, y = cx, cy

        while check_overlap(x, y, rw, rh, placed):
            y += 10

        placed[name] = (x, y, rw, rh)
        cx += rw + 20

    return placed

# ----------------------------
# Main render + move handler
# ----------------------------
def generate_plan(plot_size, room_text, selected_room, direction, offsets):
    plot_w, plot_h = parse_plot_size(plot_size)
    rooms = parse_rooms(room_text)

    CANVAS_W, CANVAS_H = 900, 600
    MARGIN = 40
    MOVE_STEP = 10

    scale = min(
        (CANVAS_W - 2*MARGIN) / plot_w,
        (CANVAS_H - 2*MARGIN) / plot_h
    )

    px0, py0 = MARGIN, MARGIN
    px1, py1 = px0 + int(plot_w * scale), py0 + int(plot_h * scale)

    placed = compute_layout(plot_w, plot_h, rooms, scale, px0, py0, px1, py1)

    # Apply movement to selected room
    if selected_room in placed:
        x, y, rw, rh = placed[selected_room]

        dx, dy = 0, 0
        if direction == "Left":
            dx = -MOVE_STEP
        elif direction == "Right":
            dx = MOVE_STEP
        elif direction == "Up":
            dy = -MOVE_STEP
        elif direction == "Down":
            dy = MOVE_STEP

        nx = max(px0, min(x + dx, px1 - rw))
        ny = max(py0, min(y + dy, py1 - rh))

        if not check_overlap(nx, ny, rw, rh, placed, ignore=selected_room):
            placed[selected_room] = (nx, ny, rw, rh)

    # Draw
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#f2f2f2")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    draw.rectangle([px0, py0, px1, py1], outline="black", width=6)
    draw.text((px0, py0 - 20), f"PLOT {plot_w} x {plot_h}", fill="black", font=font)

    for r in rooms:
        x, y, rw, rh = placed[r["name_lower"]]
        draw.rectangle([x, y, x+rw, y+rh], outline="black", width=4)
        draw.text((x+5, y+5),
                  f'{r["name"]}\n{r["w"]}x{r["h"]}',
                  fill="black", font=font)

    return img, placed

# ----------------------------
# UI
# ----------------------------
with gr.Blocks(title="VOICE2PLAN-AI") as demo:
    gr.Markdown("## VOICE2PLAN-AI – Interactive Civil Floor Planner")

    plot = gr.Textbox(label="Plot Size", value="40x30")
    rooms = gr.Textbox(
        label="Rooms",
        lines=8,
        value=(
            "Bedroom,12,10,top-left\n"
            "Pooja,5,5,bottom-of-bedroom\n"
            "Living Room,10,12,center\n"
            "Kitchen,8,7,bottom-left\n"
            "Garage,14,10,entrance"
        )
    )

    room_select = gr.Dropdown(
        choices=["bedroom", "pooja", "living room", "kitchen", "garage"],
        label="Select Room to Move",
        value="bedroom"
    )

    direction = gr.Radio(
        ["Left", "Right", "Up", "Down"],
        label="Move Direction",
        value="Right"
    )

    move_btn = gr.Button("Apply Move")
    image = gr.Image(label="Floor Plan")

    state = gr.State({})

    move_btn.click(
        generate_plan,
        inputs=[plot, rooms, room_select, direction, state],
        outputs=[image, state]
    )

if __name__ == "__main__":
    demo.queue().launch()
