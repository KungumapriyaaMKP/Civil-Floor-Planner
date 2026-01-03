import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# ----------------------------
# Utility functions
# ----------------------------
def parse_plot_size(text):
    w, h = text.lower().replace(" ", "").split("x")
    return int(w), int(h)

def parse_rooms(text):
    rooms = []
    for line in text.strip().split("\n"):
        name, w, h = line.split(",")
        rooms.append({
            "name": name.strip(),
            "w": int(w),
            "h": int(h)
        })
    return rooms

# ----------------------------
# Raw floor plan generator
# ----------------------------
def generate_raw_plan(plot_size, room_text):
    plot_w, plot_h = parse_plot_size(plot_size)
    rooms = parse_rooms(room_text)

    CANVAS_W, CANVAS_H = 900, 600
    MARGIN = 40

    # Scale factor
    scale_x = (CANVAS_W - 2 * MARGIN) / plot_w
    scale_y = (CANVAS_H - 2 * MARGIN) / plot_h
    scale = min(scale_x, scale_y)

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#f2f2f2")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.load_default()
    except:
        font = None

    # Draw plot boundary
    plot_px_w = int(plot_w * scale)
    plot_px_h = int(plot_h * scale)

    px0 = MARGIN
    py0 = MARGIN
    px1 = px0 + plot_px_w
    py1 = py0 + plot_px_h

    draw.rectangle([px0, py0, px1, py1], outline="black", width=6)
    draw.text((px0, py0 - 15), f"PLOT {plot_w} x {plot_h}", fill="black", font=font)

    # Place rooms
    cursor_x = px0 + 10
    cursor_y = py0 + 10
    row_height = 0

    for room in rooms:
        rw = int(room["w"] * scale)
        rh = int(room["h"] * scale)

        # Move to next row if overflow
        if cursor_x + rw > px1:
            cursor_x = px0 + 10
            cursor_y += row_height + 15
            row_height = 0

        # Draw room
        draw.rectangle(
            [cursor_x, cursor_y, cursor_x + rw, cursor_y + rh],
            outline="black",
            width=4
        )

        # Label
        label = f'{room["name"]}\n{room["w"]}x{room["h"]}'
        draw.text((cursor_x + 5, cursor_y + 5), label, fill="black", font=font)

        cursor_x += rw + 15
        row_height = max(row_height, rh)

    return img

# ----------------------------
# Gradio UI
# ----------------------------
demo = gr.Interface(
    fn=generate_raw_plan,
    inputs=[
        gr.Textbox(label="Total Plot Size (W x H)", placeholder="Example: 40x30"),
        gr.Textbox(
            label="Rooms (one per line: Name,Width,Height)",
            placeholder="Bedroom,12,10\nKitchen,8,7\nBathroom,6,5",
            lines=6
        )
    ],
    outputs=gr.Image(label="Raw Civil Floor Plan (2D)"),
    title="VOICE2PLAN-AI | Professional Raw Civil Floor Plan Generator",
    description=(
        "Enter exact plot size and room dimensions. "
        "Generates a clean, technical, judge-ready raw floor plan."
    )
)

demo.launch()
