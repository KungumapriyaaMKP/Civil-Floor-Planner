import gradio as gr
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image

# ----------------------------
# Model configuration
# ----------------------------
MODEL_ID = "PRAMAY3000/floor-plan-generation"

device = "cuda" if torch.cuda.is_available() else "cpu"

pipe = StableDiffusionPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
)

pipe = pipe.to(device)

# ----------------------------
# Generation function
# ----------------------------
def generate_floor_plan(prompt):
    if not prompt.strip():
        return None

    enhanced_prompt = (
        f"{prompt}, professional architectural floor plan, "
        f"top view, clear walls, labeled rooms, clean layout, blueprint style"
    )

    image = pipe(
        enhanced_prompt,
        num_inference_steps=50,
        guidance_scale=8.0
    ).images[0]

    return image

# ----------------------------
# Gradio UI
# ----------------------------
demo = gr.Interface(
    fn=generate_floor_plan,
    inputs=gr.Textbox(
        label="Describe your floor plan",
        placeholder="Example: 2 bedroom house with living room, kitchen, 2 bathrooms, 1200 sqft"
    ),
    outputs=gr.Image(label="Generated Floor Plan"),
    title="VOICE2PLAN – AI Floor Plan Generator",
    description="Describe your building in text and get an AI-generated floor plan."
)

demo.launch()
