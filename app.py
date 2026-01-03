import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# --- Styling Constants ---
BG_COLOR = "#f4f7f6"
WALL_COLOR = "#2c3e50"
ROOM_COLOR = "#ffffff"
TEXT_COLOR = "#34495e"
GRID_COLOR = "#dcdde1"

def generate_interactive_plan(plot_size, room_data, move_room_name, move_x, move_y):
    # 1. Setup Canvas
    try:
        w_ft, h_ft = map(int, plot_size.lower().split('x'))
    except: return None
    
    canvas_w, canvas_h = 800, 600
    scale = min(700/w_ft, 500/h_ft)
    offset_x, offset_y = 50, 50

    img = Image.new("RGB", (canvas_w, canvas_h), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Draw Grid
    for i in range(0, canvas_w, 20): draw.line([(i, 0), (i, canvas_h)], fill=GRID_COLOR, width=1)
    for i in range(0, canvas_h, 20): draw.line([(0, i), (canvas_w, i)], fill=GRID_COLOR, width=1)

    # 2. Parse and Place Rooms
    rooms = []
    for line in room_data.strip().split('\n'):
        parts = line.split(',')
        if len(parts) >= 3:
            rooms.append({"name": parts[0].strip(), "w": int(parts[1]), "h": int(parts[2])})

    placed_rooms = {}
    current_x, current_y = offset_x, offset_y

    for room in rooms:
        rw, rh = int(room['w'] * scale), int(room['h'] * scale)
        
        # INTERACTIVE STEP: If this is the room the user wants to move, use the sliders
        if room['name'].lower() == move_room_name.lower():
            x, y = offset_x + int(move_x * scale), offset_y + int(move_y * scale)
        else:
            x, y = current_x, current_y
            current_x += rw + 10 # Default auto-layout logic
            if current_x + rw > offset_x + (w_ft * scale):
                current_x = offset_x
                current_y += rh + 10

        # Draw Room
        draw.rectangle([x, y, x + rw, y + rh], fill=ROOM_COLOR, outline=WALL_COLOR, width=3)
        draw.text((x+5, y+5), f"{room['name']}\n({room['w']}x{room['h']})", fill=TEXT_COLOR)

    # Draw Plot Boundary
    draw.rectangle([offset_x, offset_y, offset_x + int(w_ft*scale), offset_y + int(h_ft*scale)], outline="#e74c3c", width=5)
    
    return img

# --- UI with Custom CSS ---
custom_css = """
.gradio-container { font-family: 'Segoe UI', sans-serif; }
.move-panel { background-color: #f9f9f9; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
"""

with gr.Blocks(css=custom_css) as demo:
    gr.Markdown("# 🏢 VOICE2PLAN-AI: Interactive Designer")
    gr.Markdown("Step 1: Define your plot. Step 2: List rooms. Step 3: **Move any room manually.**")
    
    with gr.Row():
        with gr.Column(scale=1):
            plot_input = gr.Textbox(label="Plot Size (WxH)", value="40x30")
            room_input = gr.Textbox(label="Rooms (Name,W,H)", lines=5, value="Bedroom,12,12\nKitchen,10,8\nLiving,15,15")
            
            gr.Markdown("### 🔧 Move Room Tools", elem_classes="move-panel")
            target_room = gr.Textbox(label="Room Name to Move", placeholder="e.g., Kitchen")
            pos_x = gr.Slider(0, 50, label="Move Horizontal (ft)", value=0)
            pos_y = gr.Slider(0, 50, label="Move Vertical (ft)", value=0)
            
            btn = gr.Button("Generate / Update Plan", variant="primary")
            
        with gr.Column(scale=2):
            output_image = gr.Image(type="pil", label="Architectural Layout")

    btn.click(generate_interactive_plan, 
              inputs=[plot_input, room_input, target_room, pos_x, pos_y], 
              outputs=output_image)

demo.launch()