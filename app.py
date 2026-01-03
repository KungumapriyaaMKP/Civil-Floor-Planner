import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# ==================================================
# Helpers
# ==================================================
def parse_plot_size(text):
    w, h = text.lower().replace(" ", "").split("x")
    return int(w), int(h)

def parse_rooms(text):
    rooms = []
    for line in text.strip().split("\n"):
        p = line.split(",")
        if len(p) < 3:
            continue
        rooms.append({
            "name": p[0].strip(),
            "key": p[0].strip().lower(),
            "w": int(p[1]),
            "h": int(p[2]),
            "pos": p[3].strip().lower() if len(p) > 3 else "any"
        })
    return rooms

def check_overlap(x, y, w, h, placed, ignore=None):
    for k, (px, py, pw, ph) in placed.items():
        if k == ignore:
            continue
        if x < px+pw and x+w > px and y < py+ph and y+h > py:
            return True
    return False

# ==================================================
# Layout computation
# ==================================================
def compute_layout(plot_w, plot_h, rooms):
    CANVAS_W, CANVAS_H = 900, 600
    MARGIN, PAD = 40, 10

    scale = min(
        (CANVAS_W - 2*MARGIN) / plot_w,
        (CANVAS_H - 2*MARGIN) / plot_h
    )

    px0, py0 = MARGIN, MARGIN
    px1 = px0 + int(plot_w * scale)
    py1 = py0 + int(plot_h * scale)

    placed = {}

    # absolute placement
    for r in rooms:
        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        if r["pos"] == "top-left":
            placed[r["key"]] = (px0+PAD, py0+PAD, rw, rh)
        elif r["pos"] == "top-right":
            placed[r["key"]] = (px1-rw-PAD, py0+PAD, rw, rh)
        elif r["pos"] == "bottom-left":
            placed[r["key"]] = (px0+PAD, py1-rh-PAD, rw, rh)
        elif r["pos"] == "bottom-right":
            placed[r["key"]] = (px1-rw-PAD, py1-rh-PAD, rw, rh)
        elif r["pos"] == "center":
            placed[r["key"]] = (
                px0 + (px1-px0)//2 - rw//2,
                py0 + (py1-py0)//2 - rh//2,
                rw, rh
            )

    # auto placement
    cx, cy = px0+PAD, py0+150
    for r in rooms:
        if r["key"] in placed:
            continue
        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        x, y = cx, cy
        while check_overlap(x, y, rw, rh, placed):
            y += 15
        placed[r["key"]] = (x, y, rw, rh)
        cx += rw + 20

    return placed, (px0, py0, px1, py1)

# ==================================================
# Rendering
# ==================================================
def render_2d(plot_w, plot_h, rooms, placed, bounds):
    px0, py0, px1, py1 = bounds
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

def render_3d(rooms, placed):
    img = Image.new("RGB", (900, 600), "#eaeaea")
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except:
        font = ImageFont.load_default()

    d.text((20, 20), "3D View (Final Layout)", fill="black", font=font)

    for r in rooms:
        x, y, w, h = placed[r["key"]]
        d.rectangle([x+6, y+6, x+w+6, y+h+6], fill="#cfcfcf")
        d.rectangle([x, y-18, x+w, y+h-18], fill="#ffffff", outline="#555", width=2)
        d.rectangle([x, y, x+w, y+h], fill="#fafafa", outline="#333", width=3)
        d.text((x+6, y+6), r["name"], fill="black", font=font)

    return img

# ==================================================
# Handlers
# ==================================================
def generate_2d(plot, room_text, state):
    plot_w, plot_h = parse_plot_size(plot)
    rooms = parse_rooms(room_text)

    placed, bounds = compute_layout(plot_w, plot_h, rooms)
    state.clear()
    state["placed"] = placed
    state["bounds"] = bounds
    state["final"] = False

    return render_2d(plot_w, plot_h, rooms, placed, bounds), state

def move_room(plot, room_text, room_key, direction, state):
    # SAFETY GUARDS — FIXES YOUR ERROR
    if (
        room_key is None or room_key == ""
        or "placed" not in state
        or room_key not in state["placed"]
        or state.get("final", False)
    ):
        return gr.update(), state

    plot_w, plot_h = parse_plot_size(plot)
    rooms = parse_rooms(room_text)
    placed = state["placed"]
    px0, py0, px1, py1 = state["bounds"]

    step = 10
    x, y, w, h = placed[room_key]

    dx = dy = 0
    if direction == "left": dx = -step
    if direction == "right": dx = step
    if direction == "up": dy = -step
    if direction == "down": dy = step

    nx = max(px0, min(x+dx, px1-w))
    ny = max(py0, min(y+dy, py1-h))

    if not check_overlap(nx, ny, w, h, placed, room_key):
        placed[room_key] = (nx, ny, w, h)

    return render_2d(plot_w, plot_h, rooms, placed, state["bounds"]), state

def confirm_3d(plot, room_text, state):
    if "placed" not in state:
        return gr.update(), state

    rooms = parse_rooms(room_text)
    state["final"] = True
    return render_3d(rooms, state["placed"]), state

# ==================================================
# UI
# ==================================================
with gr.Blocks(title="VOICE2PLAN-AI") as demo:
    gr.Markdown("## VOICE2PLAN-AI | 2D Planning → Confirm → 3D")

    plot = gr.Textbox(label="Plot Size", value="40x30")
    rooms = gr.Textbox(
        label="Rooms (Name,Width,Height,Position)",
        lines=8,
        value=(
            "Bedroom,12,10,top-left\n"
            "Living Room,10,12,center\n"
            "Kitchen,8,7,bottom-left\n"
            "Pooja,5,5,any"
        )
    )

    generate = gr.Button("Generate 2D Plan")
    room_select = gr.Dropdown(label="Select Room")
    img = gr.Image(label="Output")
    state = gr.State({})

    gr.Markdown("ℹ️ Select a room before moving")

    with gr.Row():
        up = gr.Button("⬆", scale=1)
    with gr.Row():
        left = gr.Button("⬅", scale=1)
        right = gr.Button("➡", scale=1)
    with gr.Row():
        down = gr.Button("⬇", scale=1)

    confirm = gr.Button("Confirm Layout & Generate 3D")

    def update_dropdown(txt):
        return [r["key"] for r in parse_rooms(txt)]

    rooms.change(update_dropdown, rooms, room_select)

    generate.click(generate_2d, [plot, rooms, state], [img, state])

    up.click(move_room, [plot, rooms, room_select, gr.State("up"), state], [img, state])
    down.click(move_room, [plot, rooms, room_select, gr.State("down"), state], [img, state])
    left.click(move_room, [plot, rooms, room_select, gr.State("left"), state], [img, state])
    right.click(move_room, [plot, rooms, room_select, gr.State("right"), state], [img, state])

    confirm.click(confirm_3d, [plot, rooms, state], [img, state])

if __name__ == "__main__":
    demo.launch()
