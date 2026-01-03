from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import random
import plotly
import plotly.graph_objects as go
from transformers import pipeline
import re
import os

# ==================================================
# App Setup
# ==================================================
app = FastAPI(title="CivilPlan AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:7860",
        "https://civil-floor-plan-generator.web.app",
        "https://civil-floor-plan-generator.firebaseapp.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "engine": "ready"}

# Serve Frontend (Static Files)
# We mount 'frontend/dist' to root
from fastapi.responses import FileResponse
import os

# API Routes first!
# ... (API logic below) ...

# Mount Static assets
if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/")
async def serve_index():
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    return {"message": "Frontend not built yet. Run 'npm run build' in frontend/"}

# ==================================================
# LOGIC: Voice & Parsing
# ==================================================
# Voice Recognition Setup (Startup Logic)
asr_pipe = None
try:
    print("Loading Whisper Model...")
    # OPTIMIZATION: Reverting to 'tiny.en' for speed
    asr_pipe = pipeline("automatic-speech-recognition", model="openai/whisper-tiny.en")
    print("Whisper Model Loaded Successfully.")
except Exception as e:
    print(f"Failed to load Whisper: {e}")
    asr_pipe = None

def parse_natural_language(text):
    import re
    word_to_num = {
        "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
        "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
        "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14", "fifteen": "15",
        "twenty": "20", "thirty": "30", "forty": "40", "fifty": "50", "sixty": "60"
    }
    text_lower = text.lower()
    for word, digit in word_to_num.items():
        text_lower = text_lower.replace(word, digit)
        
    # 1. Extract Room Name
    room_types = ["master bedroom", "bedroom", "kitchen", "living room", "living", "dining room", "dining", "bathroom", "bath", "garage", "office", "study", "hall"]
    name = "Room"
    for r in room_types:
        if r in text_lower:
            start_idx = text_lower.find(r)
            name = text[start_idx : start_idx+len(r)].title()
            break
            
    # 2. Extract Dimensions
    dims = re.search(r'(\d+)\s*(?:x|by|\s)\s*(\d+)', text_lower)
    w, h = 10, 10
    if dims:
        w, h = int(dims.group(1)), int(dims.group(2))
    else:
        nums = re.findall(r'\d+', text_lower)
        if len(nums) >= 2: w, h = int(nums[0]), int(nums[1])
    
    # 3. Extract Position
    pos = "any"
    if "top left" in text_lower: pos = "top-left"
    elif "top right" in text_lower: pos = "top-right"
    elif "bottom left" in text_lower: pos = "bottom-left"
    elif "bottom right" in text_lower: pos = "bottom-right"
    elif "center" in text_lower: pos = "center"
    
    return f"{name}, {w}, {h}, {pos}"

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    if not asr_pipe:
        raise HTTPException(status_code=503, detail="Whisper model not loaded")
    
    contents = await file.read()
    # Save temp
    with open("temp.wav", "wb") as f:
        f.write(contents)
        
    try:
        text = asr_pipe("temp.wav")["text"]
        parsed = parse_natural_language(text.strip())
        return {"original": text.strip(), "parsed": parsed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists("temp.wav"): os.remove("temp.wav")

# ==================================================
# LOGIC: Layout Engine
# ==================================================
class GenerateRequest(BaseModel):
    plot_size: str
    room_text: str

def parse_rooms_data(text):
    rooms = []
    for line in text.strip().split("\n"):
        p = line.split(",")
        if len(p) < 3: continue
        try:
            name = p[0].strip()
            key_name = name.lower()
            # Colors
            if "bed" in key_name:     floor = "#E8EAF6"
            elif "bath" in key_name:  floor = "#E1F5FE"
            elif "kitchen" in key_name: floor = "#EFEBE9"
            elif "living" in key_name: floor = "#FAFAFA"
            elif "dining" in key_name: floor = "#F3E5F5"
            else: floor = "#F5F5F5"
            
            rooms.append({
                "name": name, "key": key_name,
                "w": int(p[1]), "h": int(p[2]),
                "pos": p[3].strip().lower() if len(p) > 3 else "any",
                "floor_color": floor,
                "area": int(p[1]) * int(p[2])
            })
        except: continue
    return rooms

def check_overlap(x, y, w, h, placed):
    for k, (px, py, pw, ph) in placed.items():
        if x < px+pw and x+w > px and y < py+ph and y+h > py:
            return True
    return False

def compute_layout(plot_w, plot_h, rooms):
    # Constants
    M = 2 # Virtual Margin in feet
    scale = 1 # Logical scale
    
    px0, py0 = 0, 0
    px1, py1 = plot_w, plot_h
    
    placed = {}
    fixed_rooms = [r for r in rooms if r["pos"] in ["top-left", "top-right", "bottom-left", "bottom-right", "center"]]
    floating_rooms = [r for r in rooms if r["pos"] not in ["top-left", "top-right", "bottom-left", "bottom-right", "center"]]
    floating_rooms.sort(key=lambda r: r["area"], reverse=True)
    
    # Place Fixed
    for r in fixed_rooms:
        rw, rh = r["w"], r["h"]
        x, y = None, None
        if r["pos"] == "top-left": x, y = px0, py0
        elif r["pos"] == "top-right": x, y = px1-rw, py0
        elif r["pos"] == "bottom-left": x, y = px0, py1-rh
        elif r["pos"] == "bottom-right": x, y = px1-rw, py1-rh
        elif r["pos"] == "center": x, y = (px1-rw)//2, (py1-rh)//2
        
        if x is not None and not check_overlap(x, y, rw, rh, placed):
            placed[r["key"]] = (x, y, rw, rh)

    # Place Floating
    step = 1
    for r in floating_rooms:
        rw, rh = r["w"], r["h"]
        found = False
        for y in range(py0, py1 - rh + 1, step):
            for x in range(px0, px1 - rw + 1, step):
                if not check_overlap(x, y, rw, rh, placed):
                    placed[r["key"]] = (x, y, rw, rh)
                    found = True
                    break
            if found: break
            
    return placed

@app.post("/api/generate")
async def generate_layout(req: GenerateRequest):
    try:
        pw, ph = req.plot_size.lower().replace(" ", "").split("x")
        plot_w, plot_h = int(pw), int(ph)
    except:
        plot_w, plot_h = 40, 30
        
    rooms = parse_rooms_data(req.room_text)
    placed = compute_layout(plot_w, plot_h, rooms)
    
    # Calculate Stats
    total_area = sum(r["area"] for r in rooms)
    placed_area = sum([r["area"] for r in rooms if r["key"] in placed])
    efficiency = int((placed_area / (plot_w*plot_h)) * 100)
    
    return {
        "plot": {"w": plot_w, "h": plot_h},
        "rooms": rooms,
        "placed": placed,
        "efficiency": efficiency,
        "unplaced_count": len(rooms) - len(placed)
    }

# ==================================================
# LOGIC: 3D Visualization
# ==================================================
class VisRequest(BaseModel):
    plot: Dict[str, int]
    rooms: List[Dict[str, Any]]
    placed: Dict[str, List[int]]

@app.post("/api/visualize")
async def visualize_3d(req: VisRequest):
    plot_w = req.plot["w"]
    plot_h = req.plot["h"]
    
    fig = go.Figure()
    
    # Base
    fig.add_trace(go.Mesh3d(
        x=[0, plot_w, plot_w, 0], y=[0, 0, plot_h, plot_h], z=[0, 0, 0, 0],
        color='#ffffff', name='Base', opacity=0.8
    ))
    
    wall_h, wall_t = 10, 0.4
    
    # Helper
    def make_box(x, y, z, w, h, d, color, name):
        return go.Mesh3d(
            x=[x, x+w, x+w, x,   x, x+w, x+w, x],
            y=[y, y, y+h, y+h,   y, y, y+h, y+h],
            z=[z, z, z, z,       z+d, z+d, z+d, z+d],
            i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            color=color, name=name, flatshading=True,
            lighting=dict(ambient=0.6, diffuse=1, roughness=0.1, specular=1, fresnel=2)
        )

    for r in req.rooms:
        if r["key"] not in req.placed: continue
        px, py, pw, ph = req.placed[r["key"]]
        
        # Floor
        hover_txt = f"<b>{r['name']}</b><br>{r['w']}x{r['h']}"
        fig.add_trace(go.Mesh3d(
            x=[px, px+pw, px+pw, px], y=[py, py, py+ph, py+ph], z=[0.1]*4,
            i=[0,0], j=[1,2], k=[2,3], color=r["floor_color"],
            name=r["name"], hovertext=hover_txt, hoverinfo="text",
            lighting=dict(ambient=0.8)
        ))
        
        # Walls
        fig.add_trace(make_box(px, py, 0, pw, wall_t, wall_h, "#E0E0E0", "Wall")) # N
        fig.add_trace(make_box(px, py+ph-wall_t, 0, pw, wall_t, wall_h, "#E0E0E0", "Wall")) # S
        fig.add_trace(make_box(px, py, 0, wall_t, ph, wall_h, "#E0E0E0", "Wall")) # W
        fig.add_trace(make_box(px+pw-wall_t, py, 0, wall_t, ph, wall_h, "#E0E0E0", "Wall")) # E
        
        # Furniture
        key = r["key"]
        if "bed" in key:
            bx, by = px+(pw-6)/2, py+(ph-7)/2
            fig.add_trace(make_box(bx, by, 0, 6, 7, 2, "#FAFAFA", "Bed"))
            fig.add_trace(make_box(bx, by, 0, 6, 1, 4, "#5D4037", "Headboard"))
        elif "kitchen" in key:
             fig.add_trace(make_box(px, py, 0, pw, 2, 3, "#E0E0E0", "Counter"))
        elif "dining" in key:
             tx, ty = px+(pw-5)/2, py+(ph-5)/2
             fig.add_trace(make_box(tx, ty, 2.5, 5, 5, 0.2, "#8D6E63", "Table"))
        elif "living" in key:
             fig.add_trace(make_box(px+2, py+2, 0.1, pw-4, ph-4, 0.05, "#90A4AE", "Rug"))

    fig.update_layout(
         scene = dict(
            xaxis = dict(title='Width', range=[0, plot_w], showgrid=True, gridcolor='#333'),
            yaxis = dict(title='Depth', range=[plot_h, 0], showgrid=True, gridcolor='#333'),
            zaxis = dict(title='Height', range=[0, 15], showgrid=True, gridcolor='#333'),
            aspectmode='manual',
            aspectratio=dict(x=1, y=plot_h/plot_w, z=0.5), # Increased Height
            camera=dict(eye=dict(x=1.8, y=1.8, z=1.5)) # Improved Default Angle
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    
    return json.loads(plotly.io.to_json(fig))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
