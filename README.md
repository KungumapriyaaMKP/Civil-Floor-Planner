---
title: Civil Project
emoji: 🏙️
colorFrom: indigo
colorTo: gray
sdk: docker
pinned: false
---

# 🏛️ Civil Floor Plan Generator
### AI-Powered Architectural Blueprinting & 3D Visualization

[![Architecture: Hybrid](https://img.shields.io/badge/Architecture-Hybrid-blueviolet)](https://github.com/) 
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com/) 
[![Frontend: React](https://img.shields.io/badge/Frontend-React-61DAFB)](https://reactjs.org/) 
[![AI: OpenAI_Whisper](https://img.shields.io/badge/AI-Whisper-white)](https://openai.com/research/whisper)

---

## 🌟 Overview
**Civil Floor Plan Generator** is a state-of-the-art tool designed to bridge the gap between natural language descriptions and professional architectural layouts. By leveraging cutting-edge AI for voice transcription and natural language parsing, users can literally *speak* their house designs into existence.

The system doesn't just draw blocks; it computes a non-overlapping, topologically sound floor plan and elevates it into a **3D Dollhouse Model** instantly.

---

## 🚀 Key Features

### 🎙️ 1. Intelligent Voice Control
Powered by **OpenAI's Whisper**, the application understands spoken architectural requirements with high precision.
> "Add a large living room, a master bedroom, and two small bathrooms near the kitchen."

### 📐 2. Smart Layout Engine
A procedural computation engine that ensures:
- **No Overlaps**: Every room respects its neighbors' boundaries.
- **Architectural Scaling**: Rooms are sized according to standard residential ratios.
- **Dynamic Color Palettes**: Professional architectural color coding for high readability.

### 🧊 3. Real-Time 3D Visualization
One-click elevation transforms 2D blueprints into an interactive 3D model:
- **Dollhouse View**: Transparent walls and floors for clear interior inspection.
- **Procedural Furniture**: Automatic placement of beds, tables, and sofas based on room type.
- **Interactive Plotly Scene**: Zoom, rotate, and pan to inspect every corner.

---

## 🎨 Master Class: How to Prompt
To get the most out of the AI, follow these simple guidelines for your descriptions or voice commands:

### ✅ Good Prompting (Specific & Structured)
> "Create a house with a **15x20 living room**, a **12x12 bedroom**, and a **10x10 kitchen**. Add a **small balcony** next to the bedroom."

### 💡 Pro-Tips for Judges
| Feature | Suggestion | Example |
| :--- | :--- | :--- |
| **Sizes** | Mention dimensions for precision. | "20x15 hall" |
| **Quantity** | Use numbers for multiple rooms. | "three 10x10 bedrooms" |
| **Relative Placement** | Mention what should be "next to" what. | "kitchen near the hall" |
| **Adjectives** | Use "large", "small", or "tiny". | "a tiny utility room" |

---

## 🛠️ Technical Architecture
The project employs a sophisticated **Hybrid Cloud Architecture**:

- **Layer 1: Frontend (Client Interfacing)**
  - Hosted on **Firebase Hosting** for global CDN performance.
  - Built with **React 18** and **Tailwind CSS** for a premium, dark-mode UI.
  - Interactive 2D Canvas rendering for blueprints.

- **Layer 2: AI Backend (Computation)**
  - Hosted on **Hugging Face Spaces** via a **Dockerized FastAPI** instance.
  - High-Memory environment for running the **Whisper AI** model in real-time.
  - Procedural 3D Plotly generation engine.

---

## 📦 Tech Stack
- **Frontend**: React, Plotly.js, Tailwind CSS, Axios, Lucide Icons.
- **Backend**: FastAPI (Python), OpenAI Whisper (ML), Pydantic, Uvicorn.
- **Deployment**: Docker, Firebase, Hugging Face.

---

> [!IMPORTANT]
> This project was built to demonstrate the power of AI in civil engineering and CAD workflows. It showcases full-stack proficiency, AI integration, and complex geometric computation.

---
© 2026 Civil Project Team
