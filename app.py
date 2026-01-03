import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# =============================
# Helpers
# =============================
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

# =============================
# Initial layout
# =============================
def compute_layout(plot_w, plot_h, rooms, scale, px0, py0, px1, py1):
    PADDING = 10
    placed = {}

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

# =============================
# 3D Renderer (pseudo-3D)
# =============================
def render_3d(rooms, placed):
    img = Image.new("RGB", (900, 600), "#ececec")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except:
        font = ImageFont.load_default()

    draw.text((20, 20), "3D View (Generated from Finalized Layout)", fill="black", font=font)

    for r in rooms:
        x, y, w, h = placed[r["key"]]

        # shadow
        draw.rectangle([x+6, y+6, x+w+6, y+h+6], fill="#cfcfcf")

        # wall
        draw.rectangle([x, y-18, x+w, y+h-18], fill="#ffffff", outline="#444", width=2)
        draw.rectangle([x, y, x+w, y+h], fill="#fafafa", outline="#333", width=3)

        draw.text((x+6, y+6), r["name"], fill="black", font=font)

    return img

# =============================
# Main Controller
# =============================
def controller(plot_size, room_text, selected_room, move_dir, action, state):
    plot_w, plot_h = parse_plot_size(plot_size)
    rooms = parse_rooms(room_text)

    CANVAS_W, CANVAS_H = 900, 600
    MARGIN = 40
    STEP = 10

    scale = min((CANVAS_W-2*MARGIN)/plot_w, (CANVAS_H-2*MARGIN)/plot_h)
    px0, py0 = MARGIN, MARGIN
    px1, py1 = px0+int(plot_w*scale), py0+int(plot_h*scale)

    # init
    if "placed" not in state:
        state["placed"] = compute_layout(plot_w, plot_h, rooms, scale, px0, py0, px1, py1)
        state["finalized"] = False

    placed = state["placed"]

    # movement only if NOT finalized
    if not state["finalized"] and selected_room in placed:
        x, y, w, h = placed[selected_room]
        dx, dy = 0, 0

        if move_dir == "left": dx = -STEP
        if move_dir == "right": dx = STEP
        if move_dir == "up": dy = -STEP
        if move_dir == "down": dy = STEP

        nx = max(px0, min(x+dx, px1-w))
        ny = max(py0, min(y+dy, py1-h))

        if not check_overlap(nx, ny, w, h, placed, selected_room):
            placed[selected_room] = (nx, ny, w, h)

    # finalize
    if action == "finalize":
        state["finalized"] = True

    # render
    if state["finalized"]:
        return render_3d(rooms, placed), state

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#f2f2f2")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    draw.rectangle([px0, py0, px1, py1], outline="black", width=5)
    draw.text((px0, py0-20), "2D Editable Plan", fill="black", font=font)

    for r in rooms:
        x, y, w, h = placed[r["key"]]
        draw.rectangle([x, y, x+w, y+h], outline="black", width=4)
        draw.text((x+5, y+5), r["name"], fill="black", font=font)

    return img, state

# =============================
# UI
# =============================
with gr.Blocks(title="VOICE2PLAN-AI") as demo:
    gr.Markdown("## 🏠 VOICE2PLAN-AI — 2D → Adjust → Confirm → 3D")

    plot = gr.Textbox(label="Plot Size", value="40x30")
    rooms = gr.Textbox(
        label="Rooms",
        lines=6,
        value=(
            "Bedroom,12,10,top-left\n"
            "Living Room,10,12,center\n"
            "Kitchen,8,7,any\n"
            "Pooja,5,5,any"
        )
    )

    room_sel = gr.Dropdown(["bedroom","living room","kitchen","pooja"],
                           value="bedroom",
                           label="Select Room")

    gr.Markdown("### Move Selected Room")

    with gr.Row():
        up = gr.Button("⬆")
    with gr.Row():
        left = gr.Button("⬅")
        right = gr.Button("➡")
    with gr.Row():
        down = gr.Button("⬇")

    finalize = gr.Button("✅ Finalize Layout & Generate 3D")
    out = gr.Image(label="Output")
    state = gr.State({})

    up.click(controller, [plot, rooms, room_sel, gr.State("up"), gr.State(""), state], [out, state])
    down.click(controller, [plot, rooms, room_sel, gr.State("down"), gr.State(""), state], [out, state])
    left.click(controller, [plot, rooms, room_sel, gr.State("left"), gr.State(""), state], [out, state])
    right.click(controller, [plot, rooms, room_sel, gr.State("right"), gr.State(""), state], [out, state])

    finalize.click(controller, [plot, rooms, room_sel, gr.State(""), gr.State("finalize"), state], [out, state])

if __name__ == "__main__":
    demo.queue().launch()
