# app.py

import gradio as gr
from layout_engine import generate_layout

def create_floor_plan(width, height, rooms_text):
    """
    width: int (plot width)
    height: int (plot height)
    rooms_text: str (room_name:width,height per line)
    """
    try:
        rooms = {}
        lines = rooms_text.strip().split("\n")
        for line in lines:
            name, size = line.split(":")
            w, h = map(int, size.split(","))
            rooms[name.strip()] = (w, h)
        
        layout = generate_layout((width, height), rooms)
        output = ""
        for room, coords in layout.items():
            output += f"{room}: x={coords[0]}, y={coords[1]}, width={coords[2]}, height={coords[3]}\n"
        return output
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
    outputs="text",
    title="Civil Floor Plan Generator",
    description="Enter plot dimensions and room sizes to get a simple floor plan layout."
)

demo.launch()
