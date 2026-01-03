import gradio as gr
from PIL import Image, ImageDraw, ImageFont, ImageOps
import math

# ----------------------------
# Professional Styling Constants
# ----------------------------
BG_COLOR = "#f8f9fa"        # Soft off-white
PLOT_COLOR = "#2c3e50"      # Deep Navy for boundary
WALL_COLOR = "#34495e"      # Structural grey-blue
ROOM_FILL = "#ffffff"       # Clean white rooms
TEXT_COLOR = "#2c3e50"
GRID_COLOR = "#e0e0e0"
DOOR_COLOR = "#e67e22"      # Wood/Accent color for doors

def parse_plot_size(text):
    try:
        w, h = text.lower().replace(" ", "").split("x")
        return int(w), int(h)
    except:
        raise ValueError("Use format WidthxHeight (e.g. 40x30)")

def parse_rooms(text):
    rooms = []
    for line in text.strip().split("\n"):
        parts = line.split(",")
        if len(parts) < 3: continue
        rooms.append({
            "name": parts[0].strip(),
            "name_lower": parts[0].strip().lower(),
            "w": int(parts[1]),
            "h": int(parts[2]),
            "pos": parts[3].strip().lower() if len(parts) > 3 else "any"
        })
    return rooms

def check_overlap(x, y, rw, rh, placed_rooms):
    for px, py, pw, ph in placed_rooms.values():
        if (x < px + pw and x + rw > px and y < py + ph and y + rh > py):
            return True
    return False

def draw_door(draw, x, y, rw, rh, pos_type, scale):
    """Draws a professional door swing arc."""
    door_w = int(3 * scale) # Standard 3ft door
    # Simplification: Draw door at bottom-left of room for this demo
    box = [x - door_w, y + rh - door_w, x + door_w, y + rh + door_w]
    draw.arc(box, start=270, end=0, fill=DOOR_COLOR, width=2)
    draw.line([x, y + rh, x, y + rh - door_w], fill=DOOR_COLOR, width=2)

# ----------------------------
# Core Generator
# ----------------------------
def generate_pro_plan(plot_size, room_text):
    plot_w, plot_h = parse_plot_size(plot_size)
    rooms = parse_rooms(room_text)

    CANVAS_W, CANVAS_H = 1000, 800
    MARGIN = 60
    scale = min((CANVAS_W - 2*MARGIN)/plot_w, (CANVAS_H - 2*MARGIN)/plot_h)

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Try to load a clean font
    try: font = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
    except: font = ImageFont.load_default()

    # 1. Draw Architectural Grid
    for i in range(0, CANVAS_W, 40):
        draw.line([(i, 0), (i, CANVAS_H)], fill=GRID_COLOR, width=1)
    for i in range(0, CANVAS_H, 40):
        draw.line([(0, i), (CANVAS_W, i)], fill=GRID_COLOR, width=1)

    # 2. Draw Plot Boundary (Thick Outer Wall)
    px0, py0 = MARGIN, MARGIN
    px1, py1 = px0 + int(plot_w * scale), py0 + int(plot_h * scale)
    draw.rectangle([px0-5, py0-5, px1+5, py1+5], outline=PLOT_COLOR, width=10)
    
    # 3. Placement Logic (Kept from your original for stability)
    placed = {}
    direction_map = {
        "left-of": lambda tx, ty, tw, th, rw, rh: (tx - rw, ty),
        "right-of": lambda tx, ty, tw, th, rw, rh: (tx + tw, ty),
        "top-of": lambda tx, ty, tw, th, rw, rh: (tx, ty - rh),
        "bottom-of": lambda tx, ty, tw, th, rw, rh: (tx, ty + th),
    }

    # Process absolute and relative positions
    for room in rooms:
        rw, rh = int(room["w"] * scale), int(room["h"] * scale)
        pos, name = room["pos"], room["name_lower"]
        
        # Simple Position Solver
        if pos == "top-left": x, y = px0, py0
        elif pos == "top-right": x, y = px1 - rw, py0
        elif pos == "bottom-left": x, y = px0, py1 - rh
        elif pos == "bottom-right": x, y = px1 - rw, py1 - rh
        elif "of-" in pos:
            parts = pos.split("-of-")
            target = parts[1].strip()
            if target in placed:
                tx, ty, tw, th = placed[target]
                x, y = direction_map[parts[0]+"-of"](tx, ty, tw, th, rw, rh)
            else: x, y = px0, py0
        else: x, y = px0 + 50, py0 + 50 # Default fallback

        # Avoid overlap by nudging
        while check_overlap(x, y, rw, rh, placed):
            x += 10
            if x + rw > px1: x = px0; y += 10
            
        placed[name] = (x, y, rw, rh)

    # 4. Final Render (Rooms, Dimensions, Doors)
    for room in rooms:
        name = room["name_lower"]
        x, y, rw, rh = placed[name]
        
        # Room Box with thick walls
        draw.rectangle([x, y, x + rw, y + rh], fill=ROOM_FILL, outline=WALL_COLOR, width=4)
        
        # Dimension Text
        label = f"{room['name'].upper()}\n{room['w']}' x {room['h']}'"
        draw.multiline_text((x + 10, y + 10), label, fill=TEXT_COLOR, font=font, spacing=4)
        
        # Feature: Add a door icon to each room
        if room['w'] > 5:
            draw_door(draw, x, y, rw, rh, "sw", scale)

    # Header Title
    draw.text((MARGIN, 20), f"PROJECT: {plot_w}ft x {plot_h}ft RESIDENTIAL PLAN", fill=PLOT_COLOR, font=font)

    return img

# ----------------------------
# Gradio Interface
# ----------------------------
demo = gr.Interface(
    fn=generate_pro_plan,
    inputs=[
        gr.Textbox(label="Total Plot Area (WxH)", value="40x30"),
        gr.Textbox(label="Room Requirements (Name,W,H,Position)", lines=8, value="Master Bedroom,15,12,top-left\nKitchen,10,10,right-of-Master Bedroom\nLiving Room,15,15,bottom-left\nToilet,5,8,right-of-Living Room")
    ],
    outputs=gr.Image(type="pil"),
    title="🏢 VOICE2PLAN AI | Pro Architect Engine",
    description="Generates precision-scaled civil engineering layouts with structural detailing."
)

if __name__ == "__main__":
    demo.launch()