import gradio as gr
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import math

# -----------------------------
# CORE LAYOUT LOGIC
# -----------------------------
def generate_layout(plot_w, plot_h, rooms_text):
    """
    Ensures requested rooms are ALWAYS created
    """
    rooms = []
    tokens = rooms_text.lower().split(",")

    for t in tokens:
        t = t.strip()
        if "bed" in t:
            rooms.append("Bedroom")
        elif "kitchen" in t:
            rooms.append("Kitchen")
        elif "bath" in t:
            rooms.append("Bathroom")
        elif "living" in t:
            rooms.append("Living Room")

    if not rooms:
        rooms = ["Bedroom"]

    return rooms


# -----------------------------
# DRAW FLOOR PLAN
# -----------------------------
def draw_plan(plot_w, plot_h, rooms):
    fig, ax = plt.subplots(figsize=(8, 8))

    # Plot boundary
    ax.add_patch(
        Rectangle((0, 0), plot_w, plot_h, fill=False, linewidth=3)
    )

    cols = math.ceil(math.sqrt(len(rooms)))
    rows = math.ceil(len(rooms) / cols)

    room_w = plot_w / cols
    room_h = plot_h / rows

    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= len(rooms):
                break

            x = c * room_w
            y = plot_h - (r + 1) * room_h

            ax.add_patch(
                Rectangle(
                    (x, y),
                    room_w,
                    room_h,
                    fill=False,
                    linewidth=2
                )
            )

            ax.text(
                x + room_w / 2,
                y + room_h / 2,
                rooms[idx],
                ha="center",
                va="center",
                fontsize=11,
                weight="bold"
            )

            idx += 1

    # Dimension labels
    ax.text(plot_w / 2, -1, f"{plot_w} ft", ha="center", fontsize=10)
    ax.text(-1, plot_h / 2, f"{plot_h} ft", va="center", rotation=90, fontsize=10)

    # North arrow
    ax.arrow(plot_w - 2, plot_h - 4, 0, 2, head_width=0.4)
    ax.text(plot_w - 2, plot_h - 1.5, "N", ha="center", fontsize=12)

    ax.set_xlim(-3, plot_w + 3)
    ax.set_ylim(-3, plot_h + 3)
    ax.set_aspect("equal")
    ax.axis("off")

    return fig


# -----------------------------
# GRADIO PIPELINE
# -----------------------------
def generate_floor_plan(plot_width, plot_height, room_description):
    rooms = generate_layout(plot_width, plot_height, room_description)
    fig = draw_plan(plot_width, plot_height, rooms)
    return fig


# -----------------------------
# UI
# -----------------------------
with gr.Blocks(title="VOICE2PLAN-AI | Civil Floor Plan Generator") as demo:
    gr.Markdown(
        """
        ## 🏗️ VOICE2PLAN-AI – Civil Floor Plan Generator
        **Enter plot dimensions and room requirements**
        """
    )

    with gr.Row():
        plot_w = gr.Number(label="Plot Width (ft)", value=30)
        plot_h = gr.Number(label="Plot Height (ft)", value=40)

    room_text = gr.Textbox(
        label="Room Requirements",
        placeholder="Example: 1 bedroom, 1 kitchen"
    )

    generate_btn = gr.Button("Generate Floor Plan 🚀")

    output = gr.Plot(label="Raw 2D Civil Floor Plan")

    generate_btn.click(
        fn=generate_floor_plan,
        inputs=[plot_w, plot_h, room_text],
        outputs=output
    )

demo.launch(ssr_mode=False)
