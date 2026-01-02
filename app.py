import gradio as gr
from layout_engine import generate_layout  # your existing function

# Example function to wrap your floor plan generator
def create_floorplan(plot_width, plot_length, rooms_json):
    """
    Inputs:
        plot_width (int): Width of the plot
        plot_length (int): Length of the plot
        rooms_json (str): JSON string describing rooms and their dimensions
    Returns:
        Path to generated floorplan image
    """
    import json
    try:
        rooms = json.loads(rooms_json)
    except Exception as e:
        return f"Invalid rooms JSON: {e}"

    # Generate layout using your existing function
    floorplan_img = generate_layout(plot_width, plot_length, rooms)

    return floorplan_img  # should be a path to an image or PIL Image

# Define the Gradio interface
demo = gr.Interface(
    fn=create_floorplan,
    inputs=[
        gr.Number(label="Plot Width (meters)"),
        gr.Number(label="Plot Length (meters)"),
        gr.Textbox(label="Rooms JSON", placeholder='{"Living": [5,4], "Bedroom": [4,3]}')
    ],
    outputs=gr.Image(type="pil"),  # expects PIL Image output from your function
    title="Civil Floor Plan Generator",
    description="Generate building floor plans by providing plot dimensions and room details in JSON format.",
)

# Launch the app with a public link on Hugging Face Spaces
demo.launch(share=True)
