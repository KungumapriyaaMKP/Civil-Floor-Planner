import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import json

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
        if len(parts) < 3:
            continue
        pos = parts[3].strip().lower() if len(parts) > 3 else "any"
        rooms.append({
            "name": parts[0].strip(),
            "name_lower": parts[0].strip().lower(),
            "w": int(parts[1]),
            "h": int(parts[2]),
            "pos": pos,
            "area": int(parts[1]) * int(parts[2]),
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
    draw.arc([x, y, x+18, y+18], 0, 90, fill="black", width=2)

def draw_icon(draw, name, x, y, w, h):
    cx, cy = x + w//2, y + h//2
    if "bed" in name:
        draw.rectangle([cx-14, cy-7, cx+14, cy+7], outline="black", width=2)
    elif "kitchen" in name:
        draw.rectangle([cx-12, cy-6, cx+12, cy+6], outline="black", width=2)
    elif "pooja" in name:
        draw.polygon([cx, cy-8, cx-6, cy+6, cx+6, cy+6], outline="orange")
    elif "bath" in name:
        draw.ellipse([cx-6, cy-6, cx+6, cy+6], outline="black")
    elif "garage" in name:
        draw.rectangle([cx-16, cy-7, cx+16, cy+7], outline="black", width=2)

def zone_color(name):
    if "pooja" in name:
        return "orange"
    if "bed" in name:
        return "blue"
    if "kitchen" in name or "bath" in name:
        return "green"
    return "black"

# ----------------------------
# Explanation + Vastu
# ----------------------------
def generate_explanation(rooms):
    lines = []
    for r in rooms:
        if "pooja" in r["name_lower"]:
            lines.append("Pooja room placed away from public zones for sanctity.")
        if "bed" in r["name_lower"]:
            lines.append("Bedroom positioned for privacy and reduced circulation.")
        if "living" in r["name_lower"]:
            lines.append("Living room centralized for smooth movement.")
    return " ".join(lines[:3])

def vastu_check(rooms):
    checks = []
    for r in rooms:
        if "pooja" in r["name_lower"] and "toilet" in r["pos"]:
            checks.append("⚠ Pooja near toilet zone")
    if not checks:
        checks.append("✓ No major vastu conflicts detected")
    return checks

# ----------------------------
# Main generator
# ----------------------------
def generate_plan(plot_size, room_text, view_mode):
    plot_w, plot_h = parse_plot_size(plot_size)
    rooms = parse_rooms(room_text)

    if view_mode == "JSON":
        return json.dumps({
            "plot": f"{plot_w}x{plot_h}",
            "rooms": rooms
        }, indent=2)

    CANVAS_W, CANVAS_H = 1100, 750
    MARGIN, PADDING = 50, 10
    scale = min((CANVAS_W-300-2*MARGIN)/plot_w, (CANVAS_H-2*MARGIN)/plot_h)

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#f2f2f2")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    px0, py0 = MARGIN, MARGIN
    px1, py1 = px0 + int(plot_w*scale), py0 + int(plot_h*scale)

    # Outer wall
    draw.rectangle([px0, py0, px1, py1], outline="black", width=6)
    draw.text((px0, py0-25), f"PLOT {plot_w} x {plot_h}", fill="black", font=font)

    # North arrow
    draw.text((px1-40, py0-30), "↑ N", fill="black", font=font)

    # Scale bar
    draw.line([px0, py1+15, px0+50, py1+15], fill="black", width=3)
    draw.text((px0+55, py1+8), "5 ft", fill="black", font=font)

    placed = {}

    direction_map = {
        "bottom-of": lambda tx, ty, tw, th, rw, rh: (tx, ty+th+PADDING),
        "top-of": lambda tx, ty, tw, th, rw, rh: (tx, ty-rh-PADDING),
        "left-of": lambda tx, ty, tw, th, rw, rh: (tx-rw-PADDING, ty),
        "right-of": lambda tx, ty, tw, th, rw, rh: (tx+tw+PADDING, ty)
    }

    # Absolute placement
    for r in rooms:
        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        if r["pos"] == "top-left":
            placed[r["name_lower"]] = (px0+PADDING, py0+PADDING, rw, rh)
        elif r["pos"] == "center":
            placed[r["name_lower"]] = (
                px0+(px1-px0)//2-rw//2,
                py0+(py1-py0)//2-rh//2,
                rw, rh
            )

    # Relative / auto
    cx, cy = px0+PADDING, py0+150
    for r in rooms:
        if r["name_lower"] in placed:
            continue

        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        if "-of-" in r["pos"]:
            d, t = r["pos"].split("-of-")
            t = t.strip().lower()
            if t in placed:
                tx, ty, tw, th = placed[t]
                x, y = direction_map[d+"-of"](tx, ty, tw, th, rw, rh)
            else:
                x, y = cx, cy
        else:
            x, y = cx, cy

        while check_overlap(x, y, rw, rh, placed):
            y += 5

        placed[r["name_lower"]] = (x, y, rw, rh)
        cx += rw + 20

    # Draw rooms
    for r in rooms:
        x, y, rw, rh = placed[r["name_lower"]]
        draw.rectangle([x, y, x+rw, y+rh], outline=zone_color(r["name_lower"]), width=4)

        draw.text((x+5, y+5),
                  f"{r['name']}\n{r['w']}x{r['h']}\n{r['area']} sq.ft",
                  fill="black", font=font)

        draw_door(draw, x+rw-18, y+rh-18)
        draw_icon(draw, r["name_lower"], x, y, rw, rh)

    # Info panel
    panel_x = px1 + 20
    draw.rectangle([panel_x, py0, panel_x+230, py0+300], outline="black", width=2)
    draw.text((panel_x+10, py0+10), "AI Explanation", fill="black", font=font)
    draw.text((panel_x+10, py0+35), generate_explanation(rooms), fill="black", font=font)

    yv = py0 + 120
    draw.text((panel_x+10, yv), "Vastu Check:", fill="black", font=font)
    for c in vastu_check(rooms):
        yv += 20
        draw.text((panel_x+10, yv), c, fill="black", font=font)

    return img

# ----------------------------
# UI
# ----------------------------
demo = gr.Interface(
    fn=generate_plan,
    inputs=[
        gr.Textbox(label="Plot Size", value="40x30"),
        gr.Textbox(
            label="Rooms (Name,Width,Height,Position)",
            lines=8,
            value=(
                "Bedroom,12,10,top-left\n"
                "Pooja,5,5,bottom-of-bedroom\n"
                "Living Room,10,12,center\n"
                "Kitchen,8,7,bottom-left\n"
                "Garage,14,10,entrance"
            )
        ),
        gr.Radio(["Image", "JSON"], value="Image", label="View Mode")
    ],
    outputs=gr.Image(label="Civil Floor Plan") ,
    title="VOICE2PLAN-AI | Intelligent Civil Floor Planner",
    description="Rule-driven, vastu-aware, explanation-enabled civil planning system"
)

if __name__ == "__main__":
    demo.queue(concurrency_count=1).launch()
