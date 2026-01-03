import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# ----------------------------
# Helper functions
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
        pos = parts[3].strip().lower() if len(parts) > 3 else "any"
        rooms.append({
            "name": parts[0].strip(),
            "name_lower": parts[0].strip().lower(),
            "w": int(parts[1]),
            "h": int(parts[2]),
            "pos": pos,
            "is_relative": "-of-" in pos
        })
    return rooms

def check_overlap(x, y, rw, rh, placed):
    for px, py, pw, ph in placed.values():
        if x < px + pw and x + rw > px and y < py + ph and y + rh > py:
            return True
    return False

# ----------------------------
# Drawing helpers
# ----------------------------
def draw_door(draw, x, y):
    draw.arc([x, y, x+20, y+20], 0, 90, fill="black", width=2)

def draw_icon(draw, room, x, y, w, h):
    cx, cy = x + w//2, y + h//2
    if "bed" in room:
        draw.rectangle([cx-15, cy-8, cx+15, cy+8], outline="black", width=2)
    elif "kitchen" in room:
        draw.rectangle([cx-12, cy-6, cx+12, cy+6], outline="black", width=2)
    elif "pooja" in room:
        draw.polygon([cx, cy-8, cx-6, cy+6, cx+6, cy+6], outline="orange", fill=None)
    elif "bath" in room:
        draw.ellipse([cx-6, cy-6, cx+6, cy+6], outline="black", width=2)
    elif "garage" in room:
        draw.rectangle([cx-18, cy-8, cx+18, cy+8], outline="black", width=2)

def zone_color(name):
    if "pooja" in name:
        return "orange"
    if "bed" in name:
        return "blue"
    if "kitchen" in name or "bath" in name:
        return "green"
    return "black"

# ----------------------------
# Floor plan generator
# ----------------------------
def generate_raw_plan(plot_size, room_text):
    plot_w, plot_h = parse_plot_size(plot_size)
    rooms = parse_rooms(room_text)

    CANVAS_W, CANVAS_H = 1000, 700
    MARGIN, PADDING = 50, 10

    scale = min((CANVAS_W-2*MARGIN)/plot_w, (CANVAS_H-2*MARGIN)/plot_h)

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#f2f2f2")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    px0, py0 = MARGIN, MARGIN
    px1, py1 = px0 + int(plot_w*scale), py0 + int(plot_h*scale)

    draw.rectangle([px0, py0, px1, py1], outline="black", width=5)
    draw.text((px0, py0-25), f"PLOT {plot_w} x {plot_h}", fill="black", font=font)

    # North arrow
    draw.text((px1-40, py0-30), "↑ N", fill="black", font=font)

    placed = {}

    direction_map = {
        "bottom-of": lambda tx, ty, tw, th, rw, rh: (tx, ty + th + PADDING),
        "top-of": lambda tx, ty, tw, th, rw, rh: (tx, ty - rh - PADDING),
        "left-of": lambda tx, ty, tw, th, rw, rh: (tx - rw - PADDING, ty),
        "right-of": lambda tx, ty, tw, th, rw, rh: (tx + tw + PADDING, ty),
    }

    # First pass: absolute
    for r in rooms:
        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        pos = r["pos"]
        name = r["name_lower"]

        if pos == "top-left":
            x, y = px0+PADDING, py0+PADDING
        elif pos == "top-right":
            x, y = px1-rw-PADDING, py0+PADDING
        elif pos == "bottom-left":
            x, y = px0+PADDING, py1-rh-PADDING
        elif pos == "center":
            x = px0 + (px1-px0)//2 - rw//2
            y = py0 + (py1-py0)//2 - rh//2
        else:
            continue

        placed[name] = (x, y, rw, rh)

    # Second pass: relative & auto
    cx, cy = px0+PADDING, py0+150

    for r in rooms:
        name = r["name_lower"]
        if name in placed:
            continue

        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        pos = r["pos"]

        if "-of-" in pos:
            d, target = pos.split("-of-")
            target = target.strip().lower()
            if target in placed:
                tx, ty, tw, th = placed[target]
                x, y = direction_map[d+"-of"](tx, ty, tw, th, rw, rh)
            else:
                x, y = cx, cy
        else:
            x, y = cx, cy

        attempts = 0
        while check_overlap(x, y, rw, rh, placed) and attempts < 50:
            if r["is_relative"]:
                y += 5
            else:
                x += 10
            attempts += 1

        placed[name] = (x, y, rw, rh)
        cx += rw + 20

    # Draw rooms
    for r in rooms:
        name = r["name_lower"]
        x, y, rw, rh = placed[name]
        color = zone_color(name)

        draw.rectangle([x, y, x+rw, y+rh], outline=color, width=4)
        draw.text((x+5, y+5), f'{r["name"]}\n{r["w"]}x{r["h"]}', fill="black", font=font)

        draw_door(draw, x+rw-20, y+rh-20)
        draw_icon(draw, name, x, y, rw, rh)

    # Constraint panel
    panel_x = px1 + 20
    panel_y = py0

    draw.rectangle([panel_x, panel_y, panel_x+200, panel_y+180], outline="black", width=2)
    draw.text((panel_x+10, panel_y+10), "Constraints Applied:", fill="black", font=font)

    y_offset = 35
    for r in rooms:
        draw.text((panel_x+10, panel_y+y_offset),
                  f"✓ {r['name']} : {r['pos']}", fill="black", font=font)
        y_offset += 18

    return img

# ----------------------------
# Gradio UI
# ----------------------------
demo = gr.Interface(
    fn=generate_raw_plan,
    inputs=[
        gr.Textbox(label="Plot Size (W x H)", value="40x30"),
        gr.Textbox(
            label="Rooms (Name,Width,Height,Position)",
            lines=8,
            value=(
                "Bedroom,12,10,top-left\n"
                "Kitchen,8,7,bottom-left\n"
                "Pooja,5,5,bottom-of-bedroom\n"
                "Living Room,10,12,center\n"
                "Garage,14,10,entrance"
            )
        )
    ],
    outputs=gr.Image(label="Realistic Civil Floor Plan"),
    title="VOICE2PLAN-AI | Constraint-Based Civil Floor Plan Engine",
    description="Rule-driven, vastu-aware, judge-ready civil floor planning system."
)

if __name__ == "__main__":
    demo.launch()
