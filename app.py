import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import plotly.graph_objects as go
import random

# ==================================================
# Data & Parsing Helpers
# ==================================================
def parse_plot_size(text):
    try:
        w, h = text.lower().replace(" ", "").split("x")
        return int(w), int(h)
    except:
        return 40, 30  # Default fallback

def parse_rooms(text):
    rooms = []
    for line in text.strip().split("\n"):
        p = line.split(",")
        if len(p) < 3:
            continue
        try:
            # Assign colors based on room type
            name = p[0].strip()
            key_name = name.lower()
            
            # Floor colors (Carpet/Tile simulation)
            # Floor colors (Architectural Palette)
            if "bed" in key_name:     floor = "#E8EAF6" # Indigo 50 (Calm)
            elif "bath" in key_name:  floor = "#E1F5FE" # Light Blue (Clean)
            elif "kitchen" in key_name: floor = "#EFEBE9" # Brown 50 (Stone/Tile)
            elif "living" in key_name: floor = "#FAFAFA" # Off White
            elif "dining" in key_name: floor = "#F3E5F5" # Purple 50
            elif "garage" in key_name: floor = "#CFD8DC" # Blue Grey
            else: floor = "#F5F5F5" # Default Light Grey

            rooms.append({
                "name": name,
                "key": key_name,
                "w": int(p[1]),
                "h": int(p[2]),
                "pos": p[3].strip().lower() if len(p) > 3 else "any",
                "floor_color": floor,
                "area": int(p[1]) * int(p[2])
            })
        except:
            continue
    # Sort by area descending (Heuristic for better packing)
    # But keep fixed position rooms first in priority implicitly by handling them first
    return rooms

def check_overlap(x, y, w, h, placed, ignore=None):
    for k, (px, py, pw, ph) in placed.items():
        if k == ignore:
            continue
        # Strict overlap check (no touching allowed? touching is fine, overlapping is not)
        # Using < and > implies touching edges is OK.
        if x < px+pw and x+w > px and y < py+ph and y+h > py:
            return True
    return False

# ==================================================
# Layout Algorithm (Strict & Grid-Based)
# ==================================================
def compute_layout(plot_w, plot_h, rooms):
    # Constants for 2D Rendering
    CANVAS_W, CANVAS_H = 800, 600
    M = 50 
    
    scale = min((CANVAS_W-2*M)/plot_w, (CANVAS_H-2*M)/plot_h)
    
    # Plot Boundaries relative to Canvas
    px0, py0 = M, M
    px1, py1 = px0 + int(plot_w*scale), py0 + int(plot_h*scale)
    
    placed = {}
    
    # Separate fixed vs floating rooms
    fixed_rooms = [r for r in rooms if r["pos"] in ["top-left", "top-right", "bottom-left", "bottom-right", "center"]]
    floating_rooms = [r for r in rooms if r["pos"] not in ["top-left", "top-right", "bottom-left", "bottom-right", "center"]]
    
    # Sort floating rooms by area descending (Bin Packing Heuristic)
    floating_rooms.sort(key=lambda r: r["area"], reverse=True)

    P = 0 # No padding between rooms (they share walls)
    
    # 1. Place Fixed Constraints
    for r in fixed_rooms:
        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        x, y = None, None
        
        if r["pos"] == "top-left":      x, y = px0, py0
        elif r["pos"] == "top-right":   x, y = px1-rw, py0
        elif r["pos"] == "bottom-left": x, y = px0, py1-rh
        elif r["pos"] == "bottom-right":x, y = px1-rw, py1-rh
        elif r["pos"] == "center":      x, y = px0+(px1-px0)//2-rw//2, py0+(py1-py0)//2-rh//2
        
        # Check if even the fixed room fits/overlaps
        if x is not None:
             # Ensure inside bounds
            if x >= px0 and y >= py0 and x+rw <= px1 and y+rh <= py1:
                if not check_overlap(x, y, rw, rh, placed):
                    placed[r["key"]] = (x, y, rw, rh)

    # 2. Place Floating Rooms (Grid Search)
    # We scan the plot coordinates with a step size.
    # Smaller step = better packing, slower.
    step = int(1 * scale) # 1 ft steps
    if step < 1: step = 1
    
    for r in floating_rooms:
        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        found = False
        
        # Grid Search Scan
        # Strategy: Top-Left to Bottom-Right
        for y in range(py0, py1 - rh + 1, step):
            for x in range(px0, px1 - rw + 1, step):
                if not check_overlap(x, y, rw, rh, placed):
                    placed[r["key"]] = (x, y, rw, rh)
                    found = True
                    break
            if found: break
            
        # Optional: Rotation logic? (Swap w,h and try again) - skipped for now to keep UI simple
        
    return placed, (px0, py0, px1, py1), scale

# ==================================================
# 2D Rendering
# ==================================================
def render_2d_image(plot_w, plot_h, rooms, placed, bounds):
    px0, py0, px1, py1 = bounds
    img = Image.new("RGB", (800, 600), "#ffffff")
    d = ImageDraw.Draw(img)
    
    try:
        font_main = ImageFont.truetype("arial.ttf", 14)
        font_head = ImageFont.truetype("arialbd.ttf", 20)
    except:
        font_main = ImageFont.load_default()
        font_head = ImageFont.load_default()

    # Draw Plot Boundary
    d.rectangle([px0-2, py0-2, px1+2, py1+2], outline="#333333", width=2)
    
    # Label
    d.text((px0, py0 - 40), f"2D FLOOR PLAN ({plot_w}ft x {plot_h}ft)", fill="#333", font=font_head)

    # Draw Rooms
    for r in rooms:
        # Check if placed
        if r["key"] in placed:
            x, y, w, h = placed[r["key"]]
            
            # Fill
            d.rectangle([x, y, x+w, y+h], fill=r["floor_color"], outline="#000000", width=2)
            
            # Label
            text = f"{r['name']}\n{r['w']}x{r['h']}"
            bbox = d.textbbox((0,0), text, font=font_main)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            if w > tw and h > th:
                d.text((x + w/2 - tw/2, y + h/2 - th/2), text, fill="#000000", font=font_main, align="center")
        else:
            # Draw Unplaced warning?
            pass

    return img

# ==================================================
# 3D Visualization ("Dollhouse" Style)
# ==================================================
def create_3d_plot(plot_w, plot_h, rooms, placed, scale):
    fig = go.Figure()
    
    # 1. Base Plot (Ground)
    fig.add_trace(go.Mesh3d(
        x=[0, plot_w, plot_w, 0],
        y=[0, 0, plot_h, plot_h],
        z=[0, 0, 0, 0],
        color='#f0f0f0',
        name='Plot Base',
        opacity=0.5
    ))

    # Constants for 3D construction
    wall_height = 10 # ft
    wall_thickness = 0.5 # ft
    
    # Helper for box mesh (generic)
    def make_box(x, y, z, w, h, d, color, name):
        # x,y,z = corner; w,h,d = dimensions
        return go.Mesh3d(
            x=[x, x+w, x+w, x,   x, x+w, x+w, x],
            y=[y, y, y+h, y+h,   y, y, y+h, y+h],
            z=[z, z, z, z,       z+d, z+d, z+d, z+d],
            i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            color=color,
            name=name,
            flatshading=True,
            lighting=dict(ambient=0.5, diffuse=0.8, specular=0.2)
        )

    for r in rooms:
        if r["key"] not in placed:
            continue
            
        # Convert pixel coords back to plot units (feet)
        # We know px0 is origin 0,0
        # px = (ft_x * scale) + px0  => ft_x = (px - px0) / scale
        px, py, pw, ph = placed[r["key"]]
        M = 50 # Must match compute_layout M
        
        gx = (px - M) / scale
        gy = (py - M) / scale
        gw = pw / scale
        gh = ph / scale
        
        # 1. FLOOR (Plane)
        # To avoid z-fighting with plot base, lift slightly
        z_floor = 0.1
        
        # Hover Text
        hover_txt = f"<b>{r['name']}</b><br>{r['w']}ft x {r['h']}ft<br>Area: {r['area']} sq ft"
        
        fig.add_trace(go.Mesh3d(
            x=[gx, gx+gw, gx+gw, gx],
            y=[gy, gy, gy+gh, gy+gh],
            z=[z_floor, z_floor, z_floor, z_floor],
            i=[0, 0], j=[1, 2], k=[2, 3], # Simple quad triangulation
            color=r["floor_color"],
            name=f"{r['name']}",
            flatshading=True,
            hoverinfo="text",
            hovertext=hover_txt
        ))
        
        # 2. WALLS
        # Generate 4 walls around the room.
        # Ensure they look "thick" (using boxes)
        
        # North Wall (y = 0 relative to room)
        fig.add_trace(make_box(gx, gy, 0, gw, wall_thickness, wall_height, "#ffffff", f"{r['name']} Wall"))
        
        # South Wall (y = h)
        fig.add_trace(make_box(gx, gy+gh-wall_thickness, 0, gw, wall_thickness, wall_height, "#ffffff", f"{r['name']} Wall"))
        
        # West Wall (x = 0)
        # Avoid overlapping corners - adjust start/end? Simple intersection is okay for visual
        fig.add_trace(make_box(gx, gy, 0, wall_thickness, gh, wall_height, "#ffffff", f"{r['name']} Wall"))
        
        # East Wall (x = w)
        fig.add_trace(make_box(gx+gw-wall_thickness, gy, 0, wall_thickness, gh, wall_height, "#ffffff", f"{r['name']} Wall"))

        # 3. Simple Furniture (Procedural)
        # Adds scale and realism
        key = r["key"]
        
        # Bed (in bedroom)
        if "bed" in key:
            bw, bh, bd = 6, 7, 2 # Standard bed size
            # Try to place in center
            bx = gx + (gw - bw)/2
            by = gy + (gh - bh)/2
            # Mattress
            fig.add_trace(make_box(bx, by, 0, bw, bh, bd, "#FFFFFF", "Bed"))
            # Headboard
            fig.add_trace(make_box(bx, by, 0, bw, 1, 4, "#5D4037", "Headboard"))
            # Pillow
            fig.add_trace(make_box(bx, by+1, bd, bw, 1.5, 0.5, "#E0E0E0", "Pillow"))
            
        # Kitchen Counters
        elif "kitchen" in key:
            depth = 2
            # L-Shape: Top wall + Left wall
            # Top strip
            fig.add_trace(make_box(gx, gy, 0, gw, depth, 3, "#BDBDBD", "Counter"))
            # Left strip
            fig.add_trace(make_box(gx, gy+depth, 0, depth, gh-depth, 3, "#BDBDBD", "Counter"))
            
        # Dining Table
        elif "dining" in key:
            tw, th = 5, 5
            tx = gx + (gw-tw)/2
            ty = gy + (gh-th)/2
            # Table Top
            fig.add_trace(make_box(tx, ty, 2.5, tw, th, 0.2, "#8D6E63", "Table"))
            # Legs (Simplified as one block)
            fig.add_trace(make_box(tx+1, ty+1, 0, tw-2, th-2, 2.5, "#4E342E", "Legs"))
            
        # Living Room (Sofa + Rug)
        elif "living" in key:
            # Rug
            fig.add_trace(make_box(gx+2, gy+2, 0.1, gw-4, gh-4, 0.05, "#90A4AE", "Rug"))
            # Sofa (Simple box against top wall)
            sw, sh, sd = 8, 3, 2.5
            sx = gx + (gw-sw)/2
            sy = gy + 2
            fig.add_trace(make_box(sx, sy, 0, sw, sh, sd, "#546E7A", "Sofa"))

    # Update Camera (Isometric View)
    fig.update_layout(
        scene = dict(
            xaxis = dict(title='Width (ft)', range=[0, plot_w]),
            yaxis = dict(title='Depth (ft)', range=[plot_h, 0]), # Reversed to match 2D Top-Down view
            zaxis = dict(title='Height (ft)', range=[0, 15]),
            aspectmode='manual',
            aspectratio=dict(x=1, y=plot_h/plot_w, z=0.3)
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        title=f"3D Layout: {plot_w}x{plot_h}",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig

# ==================================================
# Main App Flow
# ==================================================
def generate_step_1(plot, room_text):
    plot_w, plot_h = parse_plot_size(plot)
    rooms = parse_rooms(room_text)
    
    placed, bounds, scale = compute_layout(plot_w, plot_h, rooms)
    
    img = render_2d_image(plot_w, plot_h, rooms, placed, bounds)
    
    # Check for unplaced rooms
    placed_count = len(placed)
    total_count = len(rooms)
    msg = ""
    if placed_count < total_count:
        msg = f"⚠️ Warning: Could not fit {total_count - placed_count} rooms! Check plot size."
    else:
        msg = f"✅ Successfully placed all {total_count} rooms."
    
    state = {
        "plot_w": plot_w,
        "plot_h": plot_h,
        "rooms": rooms,
        "placed": placed,
        "scale": scale
    }
    
    # Return: Image, Status Msg, State, Show Confirm
    return img, msg, state, gr.update(visible=True)

def generate_step_2(state):
    if not state: 
        return gr.update()
    
    try:
        fig = create_3d_plot(state["plot_w"], state["plot_h"], state["rooms"], state["placed"], state["scale"])
        return gr.update(value=fig, visible=True)
    except Exception as e:
        gr.Warning(f"3D Generation Error: {str(e)}")
        return gr.update(visible=True)

# Voice Recognition Setup (Startup Logic)
try:
    print("Loading Whisper Model... this may take a moment.")
    from transformers import pipeline
    # OPTIMIZATION: Reverting to 'tiny.en' for speed (Base was causing timeouts/Failed to Fetch)
    # The 'Smart Parser' below will handle accuracy issues like "twenty" -> "20"
    asr_pipe = pipeline("automatic-speech-recognition", model="openai/whisper-tiny.en")
    print("Whisper Model Loaded Successfully.")
except Exception as e:
    print(f"Failed to load Whisper: {e}")
    asr_pipe = None

def parse_natural_language(text):
    """
    Attempts to extract room details from natural language.
    Expected patterns: "Kitchen 15 by 10 center", "Master Bedroom 14 x 12 top left"
    Returns formatted string "Name, W, H, Pos" or original text if parsing fails.
    """
    import re
    
    # Pre-process: Convert number words to digits (simple mapping for house sizes)
    word_to_num = {
        "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
        "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
        "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14", "fifteen": "15",
        "sixteen": "16", "seventeen": "17", "eighteen": "18", "nineteen": "19", "twenty": "20",
        "thirty": "30", "forty": "40", "fifty": "50", "sixty": "60"
    }
    
    text_lower = text.lower()
    for word, digit in word_to_num.items():
        text_lower = text_lower.replace(word, digit)
        
    print(f"DEBUG: Parsing '{text}' -> Normalized: '{text_lower}'") # Log for debugging
    
    # 1. Extract Room Name (Keywords)
    room_types = ["master bedroom", "bedroom", "kitchen", "living room", "living", "dining room", "dining", "bathroom", "bath", "garage", "office", "study", "hall", "patio", "deck"]
    name = "Room"
    for r in room_types:
        if r in text_lower:
            start_idx = text_lower.find(r)
            name = text[start_idx : start_idx+len(r)].title()
            break
            
    # 2. Extract Dimensions
    dims = re.search(r'(\d+)\s*(?:x|by|\s)\s*(\d+)', text_lower)
    w, h = 10, 10 # Defaults
    if dims:
        w = int(dims.group(1))
        h = int(dims.group(2))
    else:
        nums = re.findall(r'\d+', text_lower)
        if len(nums) >= 2:
            w = int(nums[0])
            h = int(nums[1])
    
    # 3. Extract Position
    pos = "any"
    if "top left" in text_lower or "top-left" in text_lower: pos = "top-left"
    elif "top right" in text_lower or "top-right" in text_lower: pos = "top-right"
    elif "bottom left" in text_lower or "bottom-left" in text_lower: pos = "bottom-left"
    elif "bottom right" in text_lower or "bottom-right" in text_lower: pos = "bottom-right"
    elif "center" in text_lower or "middle" in text_lower: pos = "center"
    
    result = f"{name}, {w}, {h}, {pos}"
    print(f"DEBUG: Result -> {result}")
    return result

def transcribe_voice(audio_path, current_text):
    global asr_pipe
    if audio_path is None or asr_pipe is None:
        return current_text
    
    try:
        text = asr_pipe(audio_path)["text"]
        text = text.strip()
        
        if not text: return current_text
        
        parsed_text = parse_natural_language(text)
        
        if current_text:
            return current_text + "\n" + parsed_text
        return parsed_text
    except Exception as e:
        gr.Warning(f"Voice Error: {str(e)}")
        return current_text

custom_css = """
.container { max-width: 1200px; margin: auto; padding: 20px; }
.gr-button { font-weight: bold; }
"""

# STARTUP FIX: Move theme/css to Blocks, but in simple way to support older versions too? 
# The warning said move to launch(). Let's keep Blocks clean and pass to launch if possible?
# Actually, let's just ignore the warning for now to minimize structural changes, 
# BUT fixing the model size is the priority.
with gr.Blocks(theme=gr.themes.Soft(), css=custom_css, title="CivilPlan AI 2.0") as demo:
    
    state = gr.State()
    
    gr.Markdown("# CivilPlan AI | Realistic Floor Planner")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Configuration")
            p_in = gr.Textbox(label="Plot Size (ft)", value="40x30", info="Width x Depth")
            
            r_in = gr.Textbox(label="Rooms (Name, Width, Depth, Position)", value="Master Bedroom, 14, 12, top-left\nLiving, 20, 15, center\nKitchen, 12, 10, bottom-right\nBath, 8, 6, any", lines=5)
            
            # Voice Input
            audio_in = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Voice Input (Dictate Rooms)")
            
            btn_gen = gr.Button("Generate 2D Plan", variant="primary")
            status_txt = gr.Markdown("")
            
        with gr.Column(scale=2):
            gr.Markdown("### Preview & Confirm")
            img_out = gr.Image(label="2D Blueprint", type="pil", interactive=False)
            btn_3d = gr.Button("Confirm & Build 3D View", size="lg", visible=False)
            
    # Event for Voice
    audio_in.stop_recording(transcribe_voice, [audio_in, r_in], [r_in])
    
    with gr.Row():
        plot_out = gr.Plot(label="3D Dollhouse View", visible=False)

    btn_gen.click(generate_step_1, [p_in, r_in], [img_out, status_txt, state, btn_3d])
    btn_3d.click(generate_step_2, [state], [plot_out])

if __name__ == "__main__":
    demo.queue().launch()
