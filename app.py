# app.py
import gradio as gr
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Simple layout engine: places rooms in rows, adds doors/windows
def generate_layout(plot_size, rooms):
    """
    rooms: dict of room_name -> (width, height)
    Returns: dict of room_name -> (x, y, width, height)
    """
    layout = {}
    plot_width, plot_height = plot_size
    x_cursor = 0
    y_cursor = 0
    max_row_height = 0

    for name, (w, h) in rooms.items():
        if x_cursor + w > plot_width:
            # wrap to next row
            x_cursor = 0
            y_cursor += max_row_height + 1  # add 1 unit gap
            max_row_height = 0

        layout[name] = (x_cursor, y_cursor, w, h)
        x_cursor += w + 1  # 1 unit gap between rooms
        max_row_height = max(max_row_height, h)

    return layout

def create_floor_plan(width, height, rooms_text):
    """
    width: int (plot width)
    height: int (plot height)
    rooms_text: str (room_name:width,height per line)
    """
    try:
        # Parse input rooms
        rooms = {}
        lines = rooms_text.strip().split("\n")
        for line in lines:
            if ":" not in line:
                continue
            name, size = line.split(":")
            w, h = map(int, size.split(","))
            rooms[name.strip()] = (w, h)
        
        # Generate layout
        layout = generate_layout((width, height), rooms)

        # Draw floor plan
        fig, ax = plt.subplots(figsize=(8,8))
        for room, coords in layout.items():
            x, y, w, h = coords
            # Room rectangle
            rect = patches.Rectangle((x, y), w, h, linewidth=2, edgecolor='black', facecolor='lightgray')
            ax.add_patch(rect)
            # Room name
            ax.text(x + w/2, y + h/2, room, ha='center', va='center', fontsize=10, weight='bold')

            # Optional: add simple doors/windows (for demo)
            # Draw a small door on the bottom wall
            door_width = min(2, w/4)
            ax.plot([x + w/2 - door_width/2, x + w/2 + door_width/2], [y, y], color='brown', linewidth=3)
            # Draw a small window on the top wall
            window_width = min(2, w/4)
            ax.plot([x + w/2 - window_width/2, x + w/2 + window_width/2], [y + h, y + h], color='blue', linewidth=2)

        ax.set_xlim(0, width + 2)
        ax.set_ylim(0, height + 2)
        ax.set_aspect('equal')
        ax.axis('off')  # hide axes
        ax.set_title("2D Floor Plan", fontsize=14)

        # Flip y-axis to match traditional floor plan view
        plt.gca().invert_yaxis()

        return fig

    except Exception as e:
        return f"Error: {str(e)}"


# Gradio Interface
demo = gr.Interface(
    fn=create_floor_plan,
    inputs=[
        gr.Number(label="Plot Width"),
        gr.Number(label="Plot Height"),
        gr.Textbox(
            label="Rooms (format: room_name:width,height per line)",
            lines=10,
            placeholder="Master Bedroom:14,12\nBedroom 2:12,10\nBathroom:6,5"
        )
    ],
    outputs=gr.Image(type="matplotlib"),
    title="Civil Floor Plan Generator",
    description="Enter plot dimensions and room sizes to get a 2D schematic floor plan."
)

demo.launch(share=True)
