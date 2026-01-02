# app.py
import gradio as gr
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from layout_engine import generate_layout  # make sure it returns x,y,w,h

def create_floor_plan(width, height, rooms_text):
    """
    width: int (plot width)
    height: int (plot height)
    rooms_text: str (room_name:width,height per line)
    """
    try:
        # Parse input
        rooms = {}
        lines = rooms_text.strip().split("\n")
        for line in lines:
            name, size = line.split(":")
            w, h = map(int, size.split(","))
            rooms[name.strip()] = (w, h)
        
        # Generate layout: expect dict {room_name: (x, y, w, h)}
        layout = generate_layout((width, height), rooms)

        # Draw floor plan
        fig, ax = plt.subplots()
        for room, coords in layout.items():
            x, y, w, h = coords
            rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='black', facecolor='lightblue')
            ax.add_patch(rect)
            ax.text(x + w/2, y + h/2, room, ha='center', va='center', fontsize=10)
        
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.set_aspect('equal')
        ax.set_title("Floor Plan")
        plt.gca().invert_yaxis()  # optional: origin at top-left like floor plans
        
        return fig

    except Exception as e:
        return f"Error: {str(e)}"

demo = gr.Interface(
    fn=create_floor_plan,
    inputs=[
        gr.Number(label="Plot Width"),
        gr.Number(label="Plot Height"),
        gr.Textbox(
            label="Rooms (format: room_name:width,height per line)",
            lines=10,
            placeholder="LivingRoom:5,6\nBedroom:4,4"
        )
    ],
    outputs=gr.Image(type="matplotlib"),
    title="Civil Floor Plan Generator",
    description="Enter plot dimensions and room sizes to get a simple floor plan layout."
)

demo.launch(share=True)
