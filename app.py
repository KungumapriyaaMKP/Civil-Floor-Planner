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
            rooms.append({
                "name": p[0].strip(),
                "key": p[0].strip().lower(),
                "w": int(p[1]),
                "h": int(p[2]),
                "pos": p[3].strip().lower() if len(p) > 3 else "any",
                "color": f"rgb({random.randint(50,200)}, {random.randint(50,200)}, {random.randint(50,200)})"
            })
        except:
            continue
    return rooms

def check_overlap(x, y, w, h, placed, ignore=None):
    for k, (px, py, pw, ph) in placed.items():
        if k == ignore:
            continue
        if x < px+pw and x+w > px and y < py+ph and y+h > py:
            return True
    return False

# ==================================================
# Layout Algorithm (Simplified)
# ==================================================
def compute_layout(plot_w, plot_h, rooms):
    # Constants for 2D Rendering
    CANVAS_W, CANVAS_H = 800, 600
    M, P = 50, 10
    
    scale = min((CANVAS_W-2*M)/plot_w, (CANVAS_H-2*M)/plot_h)
    
    # Plot Boundaries relative to Canvas
    px0, py0 = M, M
    px1, py1 = px0 + int(plot_w*scale), py0 + int(plot_h*scale)
    
    placed = {}
    
    # 1. Place fixed/corner constraints first
    for r in rooms:
        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        if r["pos"] == "top-left":
            placed[r["key"]] = (px0+P, py0+P, rw, rh)
        elif r["pos"] == "top-right":
            placed[r["key"]] = (px1-rw-P, py0+P, rw, rh)
        elif r["pos"] == "bottom-left":
            placed[r["key"]] = (px0+P, py1-rh-P, rw, rh)
        elif r["pos"] == "bottom-right":
            placed[r["key"]] = (px1-rw-P, py1-rh-P, rw, rh)
        elif r["pos"] == "center":
            placed[r["key"]] = (px0+(px1-px0)//2-rw//2, py0+(py1-py0)//2-rh//2, rw, rh)

    # 2. Place remaining "any" rooms using a simple bin packing heuristic
    # Start placing from top-left, moving right then down
    cx, cy = px0+P, py0+P + 50 # Start a bit offset from corners if possible
    
    row_h = 0
    for r in rooms:
        if r["key"] in placed:
            continue
        
        rw, rh = int(r["w"]*scale), int(r["h"]*scale)
        
        # Simple overlap check and scan
        # Reset to start of line if we go too far right
        if cx + rw > px1 - P:
            cx = px0 + P
            cy += row_h + P
            row_h = 0
            
        found_spot = False
        # Try to find a spot in the current 'cy' band
        for _ in range(50): # limit attempts
            if not check_overlap(cx, cy, rw, rh, placed):
                placed[r["key"]] = (cx, cy, rw, rh)
                cx += rw + P
                row_h = max(row_h, rh)
                found_spot = True
                break
            cx += 20 # Step forward
            
        if not found_spot:
            # Force place somewhere (fallback)
            placed[r["key"]] = (px0+P, cy + 50, rw, rh)

    return placed, (px0, py0, px1, py1), scale

# ==================================================
# 2D Rendering
# ==================================================
def render_2d_image(plot_w, plot_h, rooms, placed, bounds):
    px0, py0, px1, py1 = bounds
    img = Image.new("RGB", (800, 600), "#ffffff")
    d = ImageDraw.Draw(img)
    
    try:
        font_check = ImageFont.truetype("arial.ttf", 16)
        font_bold = ImageFont.truetype("arialbd.ttf", 20)
    except:
        font_check = ImageFont.load_default()
        font_bold = ImageFont.load_default()

    # Draw Plot Boundary
    d.rectangle([px0-5, py0-5, px1+5, py1+5], outline="#333333", width=2)
    d.rectangle([px0, py0, px1, py1], fill="#f9f9f9", outline="#555555", width=2)
    
    # Label Plot
    d.text((px0, py0 - 30), f"PLOT AREA: {plot_w}ft x {plot_h}ft", fill="#333", font=font_bold)

    # Draw Rooms
    for r in rooms:
        if r["key"] in placed:
            x, y, w, h = placed[r["key"]]
            
            # Shadow
            d.rectangle([x+4, y+4, x+w+4, y+h+4], fill="#dddddd")
            # Room Body
            d.rectangle([x, y, x+w, y+h], fill="#e3f2fd", outline="#1565c0", width=3)
            
            # Text centering
            cx, cy = x + w/2, y + h/2
            text = f"{r['name']}\n{r['w']}x{r['h']}"
            
            bbox = d.textbbox((0,0), text, font=font_check)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            d.text((cx-tw/2, cy-th/2), text, fill="#0d47a1", font=font_check, align="center")

    return img

# ==================================================
# 3D Visualization (Plotly)
# ==================================================
def create_3d_plot(plot_w, plot_h, rooms, placed, scale):
    fig = go.Figure()
    
    # Ground Plane (The Plot)
    fig.add_trace(go.Mesh3d(
        x=[0, plot_w, plot_w, 0],
        y=[0, 0, plot_h, plot_h],
        z=[0, 0, 0, 0],
        color='lightgrey',
        opacity=0.5,
        name='Plot Area'
    ))

    # Helper to get vertices for a 3D box
    def get_box_mesh(x, y, w, h, z_h, color):
        # 8 vertices
        # Bottom: 0-3, Top: 4-7
        X = [x, x+w, x+w, x,   x, x+w, x+w, x]
        Y = [y, y, y+h, y+h,   y, y, y+h, y+h]
        Z = [0, 0, 0, 0,       z_h, z_h, z_h, z_h]
        
        # 12 triangles (2 per face)
        # i, j, k indices
        return go.Mesh3d(
            x=X, y=Y, z=Z,
            color=color,
            alphahull=0, # Convex hull
            flatshading=True,
            name="Room",
            hoverinfo='all'
        )

    # Add each room as a 3D block
    for r in rooms:
        if r["key"] in placed:
            # We need to un-scale the coordinates back to real plot units
            # Layout coords (pixels) -> Plot units
            # (Pixel - Origin) / scale = Unit
            # But the layout was done in pixels relative to (px0, py0).
            # To simplify, we re-calculate positions in abstract units roughly or reverse logic.
            # Easier: Just use the original w/h and 'relative' position derived from pixel placement?
            # Or better: Assume the 'placed' x,y are pixels, convert back to plot units:
            
            # Actually, let's just visualize the PIXEL layout in 3D (it preserves relative positions perfectly)
            # and just label axes as "Relative Units".
            # Or to be precise:
            
            # Using the pixel coordinates directly for 3D is easiest for distinct visualization
            # without float rounding issues.
            
            px, py, pw, ph = placed[r["key"]]
            
            # Invert Y for plotting usually (graphics y down vs plot y up), 
            # but for floor plan top-down 2D matches 3D top-down.
            # Let's simple use x->x, y->y, z->height
            
            # Height of walls (random or fixed) - let's say 10ft proportional
            wall_h = 10 * scale # Scaled height to match
            
            fig.add_trace(go.Mesh3d(
                # explicit cube faces for better control than convex hull sometimes
                x=[px, px+pw, px+pw, px,   px, px+pw, px+pw, px],
                y=[py, py, py+ph, py+ph,   py, py, py+ph, py+ph],
                z=[0, 0, 0, 0,             wall_h, wall_h, wall_h, wall_h],
                i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
                j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
                k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                color=r['color'],
                opacity=0.9,
                flatshading=True,
                name=r['name']
            ))
            
            # Add Wireframe/Edges (simulated via Line3d if needed, omitted for simplicity)

    # Update Camera and Layout
    fig.update_layout(
        scene = dict(
            xaxis = dict(visible=False),
            yaxis = dict(visible=False),
            zaxis = dict(visible=False),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

# ==================================================
# App Logic
# ==================================================
def generate_step_1(plot, room_text):
    plot_w, plot_h = parse_plot_size(plot)
    rooms = parse_rooms(room_text)
    
    placed, bounds, scale = compute_layout(plot_w, plot_h, rooms)
    
    img = render_2d_image(plot_w, plot_h, rooms, placed, bounds)
    
    # Store state
    new_state = {
        "plot_w": plot_w,
        "plot_h": plot_h,
        "rooms": rooms,
        "placed": placed,
        "scale": scale
    }
    
    # Return: Image, State, Show Confirm Button
    return img, new_state, gr.update(visible=True), gr.update(visible=False)

def generate_step_2(state):
    if not state:
        return None
    
    fig = create_3d_plot(
        state["plot_w"], 
        state["plot_h"], 
        state["rooms"], 
        state["placed"],
        state["scale"]
    )
    
    # Return: Plot, Show Plot
    return fig, gr.update(visible=True)

# ==================================================
# UI Construction
# ==================================================
custom_css = """
body { background-color: #f0f2f5; }
.container { max-width: 1200px; margin: auto; padding: 20px; }
h1 { color: #1a237e; font-family: 'Helvetica Neue', sans-serif; text-align: center; }
.gr-button { background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); border: none; font-weight: bold; color: white !important; }
.gr-button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
"""

with gr.Blocks(theme=gr.themes.Soft(), css=custom_css, title="CivilPlan AI") as demo:
    
    state = gr.State()
    
    with gr.Column(elem_classes="container"):
        gr.Markdown("# 🏗️ CivilPlan AI | Intelligent Floor Planner")
        gr.Markdown("Transform text requirements into professional 2D & 3D floor plans instantly.")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 1. Requirements")
                plot_input = gr.Textbox(label="Plot Size (ft)", value="40x30", placeholder="e.g. 50x40")
                rooms_input = gr.Textbox(
                    label="Room Details (Name, Width, Height, Position)", 
                    lines=6,
                    value="Master Bedroom, 14, 12, top-left\nLiving Room, 16, 14, center\nKitchen, 10, 10, bottom-right\nBathroom, 8, 6, any\nGuest Room, 12, 11, top-right"
                )
                btn_gen_2d = gr.Button("🎨 Generate 2D Plan", size="lg")
                
            with gr.Column(scale=2):
                gr.Markdown("### 2. 2D Preview")
                out_image = gr.Image(label="2D Layout", type="pil", interactive=False)
                
                btn_confirm = gr.Button("✅ Confirm & Verify in 3D", size="lg", visible=False)
        
        with gr.Row():
            with gr.Column():
                out_3d = gr.Plot(label="3D Visualization", visible=False)

    # Interactions
    btn_gen_2d.click(
        generate_step_1, 
        inputs=[plot_input, rooms_input], 
        outputs=[out_image, state, btn_confirm, out_3d] 
        # Note: out_3d hidden when generating new 2D
    )
    
    btn_confirm.click(
        generate_step_2,
        inputs=[state],
        outputs=[out_3d, out_3d] # One to update value, one to update visibility
    )

if __name__ == "__main__":
    demo.launch()
