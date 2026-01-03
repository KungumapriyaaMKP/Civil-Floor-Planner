import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------
# Helpers
# --------------------------------------------------
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

def check_overlap(x, y, w, h, placed, ignore=None):
    for k, (px, py, pw, ph) in placed.items():
        if k == ignore:
            continue
        if x < px+pw and x+w > px and y < py+ph and y+h > py:
            return True
    return False

# --------------------------------------------------
# Initial layout
# --------------------------------------------------
def compute_layout(plot_w, plot_h, rooms, scale, px0, py0, px1, py1):
    PADDING = 10
    placed = {}

    # Absolute placements
    for r in rooms:
        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        if r["pos"] == "top-left":
            placed[r["key"]] = (px0+PADDING, py0+PADDING, rw, rh)
        elif r["pos"] == "center":
            placed[r["key"]] = (
                px0+(px1-px0)//2-rw//2,
                py0+(py1-py0)//2-rh//2,
                rw, rh
            )

    # Auto placement
    cx, cy = px0+20, py0+140
    for r in rooms:
        if r["key"] in placed:
            continue
        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        x, y = cx, cy
        while check_overlap(x, y, rw, rh, placed):
            y += 15
        placed[r["key"]] = (x, y, rw, rh)
        cx += rw+20

    return placed

# --------------------------------------------------
# Render 2D
# --------------------------------------------------
def render_2d(plot_w, plot_h, rooms, placed):
    W, H = 900, 600
    M = 40
    img = Image.new("RGB", (W, H), "#f2f2f2")
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    d.rectangle([M, M, W-M, H-M], outline="black", width=5)
    d.text((M, M-20), "2D Editable Floor Plan", fill="black", font=font)

    for r in rooms:
        x, y, w, h = placed[r["key"]]
        d.rectangle([x, y, x+w, y+h], outline="black", width=4)
        d.text((x+5, y+5), r["name"], fill="black", font=font)

    return img

# --------------------------------------------------
# Render pseudo-3D
# --------------------------------------------------
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

        d.rectangle([x+6, y+6, x+w+6, y+h+6], fill="#cfcfcf")   # shadow
        d.rectangle([x, y-18, x+w, y+h-18], fill="#ffffff", outline="#555", width=2)
        d.rectangle([x, y, x+w, y+h], fill="#fafafa", outline="#333", width=3)
        d.text((x+6, y+6), r["name"], fill="black", font=font)

    return img

# --------------------------------------------------
# Controller
# --------------------------------------------------
def controller(plot_size, room_text, selected_room, move_dir, action, state):
    plot_w, plot_h = parse_plot_size(plot_size)
    rooms = parse_rooms(room_text)

    W, H, M = 900, 600, 40
    scale = min((W-2*M)/plot_w, (H-2*M)/plot_h)
    px0, py0 = M, M
    px1, py1 = px0+int(plot_w*scale), py0+int(plot_h*scale)

    if "placed" not in state:
        state["placed"] = compute_layout(plot_w, plot_h, rooms, scale, px0, py0, px1, py1)
        state["mode"] = "edit"

    placed = state["placed"]

    # Move only in edit mode
    if state["mode"] == "edit" and selected_room in placed:
        x, y, w, h = placed[selected_room]
        dx, dy = 0, 0
        step = 10
        if move_dir == "left": dx = -step
        if move_dir == "right": dx = step
        if move_dir == "up": dy = -step
        if move_dir == "down": dy = step

        nx = max(px0, min(x+dx, px1-w))
        ny = max(py0, min(y+dy, py1-h))

        if not check_overlap(nx, ny, w, h, placed, selected_room):
            placed[selected_room] = (nx, ny, w, h)

    if action == "confirm":
        state["mode"] = "final"

    state["placed"] = placed

    if state["mode"] == "final":
        return render_3d(rooms, placed), state

    return render_2d(plot_w, plot_h, rooms, placed), state

# --------------------------------------------------
# UI
# --------------------------------------------------
with gr.Blocks(title="VOICE2PLAN-AI") as demo:
    gr.Markdown("## VOICE2PLAN-AI — 2D Planning → Confirm → 3D")

    plot = gr.Textbox(label="Plot Size", value="40x30")
    rooms = gr.Textbox(
        label="Rooms (Name,Width,Height,Position)",
        lines=6,
        value=(
            "Bedroom,12,10,top-left\n"
            "Living Room,10,12,center\n"
            "Kitchen,8,7,any\n"
            "Pooja,5,5,any"
        )
    )

    room_select = gr.Dropdown(label="Select Room to Move")
    image = gr.Image(label="Output")
    state = gr.State({})

    gr.Markdown("### Move Selected Room")

    with gr.Row():
        btn_up = gr.Button("⬆", scale=1)
    with gr.Row():
        btn_left = gr.Button("⬅", scale=1)
        btn_right = gr.Button("➡", scale=1)
    with gr.Row():
        btn_down = gr.Button("⬇", scale=1)

    confirm = gr.Button("✅ Confirm Layout & Generate 3D")

    def update_dropdown(room_text):
        return [r["key"] for r in parse_rooms(room_text)]

    rooms.change(update_dropdown, rooms, room_select)

    btn_up.click(controller, [plot, rooms, room_select, gr.State("up"), gr.State(""), state], [image, state])
    btn_down.click(controller, [plot, rooms, room_select, gr.State("down"), gr.State(""), state], [image, state])
    btn_left.click(controller, [plot, rooms, room_select, gr.State("left"), gr.State(""), state], [image, state])
    btn_right.click(controller, [plot, rooms, room_select, gr.State("right"), gr.State(""), state], [image, state])

    confirm.click(controller, [plot, rooms, room_select, gr.State(""), gr.State("confirm"), state], [image, state])

if __name__ == "__main__":
    demo.queue().launch()
