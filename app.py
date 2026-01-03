import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# ==================================================
# Helper functions (UNCHANGED)
# ==================================================
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
            "key": parts[0].strip().lower(),
            "w": int(parts[1]),
            "h": int(parts[2]),
            "pos": parts[3].strip().lower() if len(parts) > 3 else "any"
        })
    return rooms

def check_overlap(x, y, rw, rh, placed, ignore=None):
    for k, (px, py, pw, ph) in placed.items():
        if k == ignore:
            continue
        if x < px+pw and x+rw > px and y < py+ph and y+rh > py:
            return True
    return False

# ==================================================
# Layout computation (EXTRACTED from your function)
# ==================================================
def compute_layout(plot_w, plot_h, rooms):
    CANVAS_W, CANVAS_H = 900, 600
    MARGIN, PADDING = 40, 10

    scale = min(
        (CANVAS_W - 2*MARGIN) / plot_w,
        (CANVAS_H - 2*MARGIN) / plot_h
    )

    px0, py0 = MARGIN, MARGIN
    px1, py1 = px0 + int(plot_w*scale), py0 + int(plot_h*scale)

    placed = {}

    # ---- First pass (absolute)
    for r in rooms:
        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        pos = r["pos"]

        if pos == "top-left":
            x, y = px0+PADDING, py0+PADDING
        elif pos == "top-right":
            x, y = px1-rw-PADDING, py0+PADDING
        elif pos == "bottom-left":
            x, y = px0+PADDING, py1-rh-PADDING
        elif pos == "bottom-right":
            x, y = px1-rw-PADDING, py1-rh-PADDING
        elif pos == "center":
            x = px0 + (px1-px0)//2 - rw//2
            y = py0 + (py1-py0)//2 - rh//2
        else:
            continue

        placed[r["key"]] = (x, y, rw, rh)

    # ---- Auto placement
    cx, cy = px0+PADDING, py0+150
    for r in rooms:
        if r["key"] in placed:
            continue
        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        x, y = cx, cy
        while check_overlap(x, y, rw, rh, placed):
            y += 15
        placed[r["key"]] = (x, y, rw, rh)
        cx += rw + 20

    return placed, (px0, py0, px1, py1, scale)

# ==================================================
# Render 2D (RAW IMAGE)
# ==================================================
def render_2d(plot_w, plot_h, rooms, placed, bounds):
    px0, py0, px1, py1, scale = bounds
    img = Image.new("RGB", (900, 600), "#f2f2f2")
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    d.rectangle([px0, py0, px1, py1], outline="black", width=6)
    d.text((px0, py0-20), f"PLOT {plot_w} x {plot_h}", fill="black", font=font)

    for r in rooms:
        x, y, w, h = placed[r["key"]]
        d.rectangle([x, y, x+w, y+h], outline="black", width=4)
        d.text((x+5, y+5), r["name"], fill="black", font=font)

    return img

# ==================================================
# Render pseudo-3D (AFTER CONFIRM)
# ==================================================
def render_3d(rooms, placed):
    img = Image.new("RGB", (900, 600), "#eaeaea")
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except:
        font = ImageFont.load_default()

    d.text((20, 20), "3D View (Generated from Confirmed Layout)", fill="black", font=font)

    for r in rooms:
        x, y, w, h = placed[r["key"]]
        d.rectangle([x+6, y+6, x+w+6, y+h+6], fill="#cfcfcf")      # shadow
        d.rectangle([x, y-18, x+w, y+h-18], fill="#ffffff", outline="#555", width=2)
        d.rectangle([x, y, x+w, y+h], fill="#fafafa", outline="#333", width=3)
        d.text((x+6, y+6), r["name"], fill="black", font=font)

    return img

# ==================================================
# Controller
# ==================================================
def controller(plot_size, room_text, selected_room, direction, confirm, state):
    plot_w, plot_h = parse_plot_size(plot_size)
    rooms = parse_rooms(room_text)

    if "placed" not in state:
        placed, bounds = compute_layout(plot_w, plot_h, rooms)
        state["placed"] = placed
        state["bounds"] = bounds
        state["final"] = False

    placed = state["placed"]
    bounds = state["bounds"]
    px0, py0, px1, py1, _ = bounds

    # ---- Move (ONLY before confirm)
    if not state["final"] and selected_room in placed:
        x, y, w, h = placed[selected_room]
        step = 10
        dx = dy = 0
        if direction == "left": dx = -step
        if direction == "right": dx = step
        if direction == "up": dy = -step
        if direction == "down": dy = step

        nx = max(px0, min(x+dx, px1-w))
        ny = max(py0, min(y+dy, py1-h))
        if not check_overlap(nx, ny, w, h, placed, selected_room):
            placed[selected_room] = (nx, ny, w, h)

    if confirm:
        state["final"] = True
        return render_3d(rooms, placed), state

    return render_2d(plot_w, plot_h, rooms, placed, bounds), state

# ==================================================
# UI
# ==================================================
with gr.Blocks(title="VOICE2PLAN-AI") as demo:
    gr.Markdown("## VOICE2PLAN-AI | 2D Planning → Confirm → 3D")

    plot = gr.Textbox(label="Plot Size", value="40x30")
    rooms = gr.Textbox(
        label="Rooms (Name,Width,Height,Position)",
        lines=8
    )

    room_select = gr.Dropdown(label="Select Room")
    img = gr.Image(label="Output")
    state = gr.State({})

    gr.Markdown("### Move Selected Room")
    with gr.Row():
        up = gr.Button("⬆", scale=1)
    with gr.Row():
        left = gr.Button("⬅", scale=1)
        right = gr.Button("➡", scale=1)
    with gr.Row():
        down = gr.Button("⬇", scale=1)

    confirm = gr.Button("✅ Confirm Layout & Generate 3D")

    def update_rooms(txt):
        return [r["key"] for r in parse_rooms(txt)]

    rooms.change(update_rooms, rooms, room_select)

    up.click(controller, [plot, rooms, room_select, gr.State("up"), gr.State(False), state], [img, state])
    down.click(controller, [plot, rooms, room_select, gr.State("down"), gr.State(False), state], [img, state])
    left.click(controller, [plot, rooms, room_select, gr.State("left"), gr.State(False), state], [img, state])
    right.click(controller, [plot, rooms, room_select, gr.State("right"), gr.State(False), state], [img, state])

    confirm.click(controller, [plot, rooms, room_select, gr.State(""), gr.State(True), state], [img, state])

if __name__ == "__main__":
    demo.launch()
