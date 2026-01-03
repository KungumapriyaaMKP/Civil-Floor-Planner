import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# ============================
# Helpers
# ============================
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
        if x < px + pw and x + w > px and y < py + ph and y + h > py:
            return True
    return False

# ============================
# 2D Layout Engine
# ============================
def compute_layout(plot_w, plot_h, rooms, scale, px0, py0, px1, py1):
    PADDING = 10
    placed = {}

    # absolute
    for r in rooms:
        rw, rh = int(r["w"] * scale), int(r["h"] * scale)
        if r["pos"] == "top-left":
            placed[r["key"]] = (px0+PADDING, py0+PADDING, rw, rh)
        elif r["pos"] == "center":
            placed[r["key"]] = (
                px0 + (px1-px0)//2 - rw//2,
                py0 + (py1-py0)//2 - rh//2,
                rw, rh
            )

    # auto / relative
    cx, cy = px0 + 20, py0 + 140
    for r in rooms:
        if r["key"] in placed:
            continue
        rw, rh = int(r["w"] * scale), int(r["h"] * scale)
        x, y = cx, cy
        while check_overlap(x, y, rw, rh, placed):
            y += 15
        placed[r["key"]] = (x, y, rw, rh)
        cx += rw + 20

    return placed

# ============================
# 3D Renderer (Pseudo-3D)
# ============================
def render_3d(plot_w, plot_h, rooms, placed):
    CANVAS_W, CANVAS_H = 900, 600
    WALL_HEIGHT = 20
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#ececec")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except:
        font = ImageFont.load_default()

    # draw floor
    draw.rectangle([50, 50, CANVAS_W-50, CANVAS_H-50], fill="#f7f7f7", outline="#aaa", width=3)

    for r in rooms:
        x, y, w, h = placed[r["key"]]

        # shadow
        draw.rectangle(
            [x+5, y+5, x+w+5, y+h+5],
            fill="#d0d0d0"
        )

        # wall top
        draw.rectangle(
            [x, y-WALL_HEIGHT, x+w, y+h-WALL_HEIGHT],
            fill="#ffffff",
            outline="#555",
            width=2
        )

        # wall front
        draw.rectangle(
            [x, y, x+w, y+h],
            fill="#fafafa",
            outline="#444",
            width=3
        )

        draw.text(
            (x+8, y+8),
            r["name"],
            fill="black",
            font=font
        )

    draw.text((60, 20), "3D Floor Plan (Generated from Final Layout)", fill="black", font=font)
    return img

# ============================
# Main Controller
# ============================
def app(plot_size, room_text, action, state):
    plot_w, plot_h = parse_plot_size(plot_size)
    rooms = parse_rooms(room_text)

    CANVAS_W, CANVAS_H = 900, 600
    MARGIN = 40

    scale = min(
        (CANVAS_W-2*MARGIN)/plot_w,
        (CANVAS_H-2*MARGIN)/plot_h
    )

    px0, py0 = MARGIN, MARGIN
    px1, py1 = px0 + int(plot_w*scale), py0 + int(plot_h*scale)

    # init state
    if "placed" not in state:
        state["placed"] = compute_layout(plot_w, plot_h, rooms, scale, px0, py0, px1, py1)
        state["finalized"] = False

    if action == "Finalize & Generate 3D":
        state["finalized"] = True

    if state["finalized"]:
        img = render_3d(plot_w, plot_h, rooms, state["placed"])
        return img, state

    # draw raw 2D
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#f2f2f2")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    draw.rectangle([px0, py0, px1, py1], outline="black", width=5)
    draw.text((px0, py0-20), "2D Editable Plan", fill="black", font=font)

    for r in rooms:
        x, y, w, h = state["placed"][r["key"]]
        draw.rectangle([x, y, x+w, y+h], outline="black", width=4)
        draw.text((x+5, y+5), r["name"], fill="black", font=font)

    return img, state

# ============================
# UI
# ============================
with gr.Blocks(title="VOICE2PLAN-AI") as demo:
    gr.Markdown("## 🏠 VOICE2PLAN-AI — 2D Planning → 3D Visualization")

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

    action = gr.Radio(
        ["Edit 2D Layout", "Finalize & Generate 3D"],
        value="Edit 2D Layout",
        label="Action"
    )

    out = gr.Image(label="Output")
    state = gr.State({})

    btn = gr.Button("Run")

    btn.click(app, [plot, rooms, action, state], [out, state])

if __name__ == "__main__":
    demo.queue().launch()
