---
title: Civil Project
emoji: 🏙️
colorFrom: indigo
colorTo: gray
sdk: docker
pinned: false
---

# 🏛️ Civil Floor Plan Generator  
### AI-Driven Architectural Planning & 3D Visualization Platform

[![Architecture: Hybrid](https://img.shields.io/badge/Architecture-Hybrid-blueviolet)](https://github.com/)  
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com/)  
[![Frontend: React](https://img.shields.io/badge/Frontend-React-61DAFB)](https://reactjs.org/)  
[![AI: Whisper](https://img.shields.io/badge/AI-Whisper-white)](https://openai.com/research/whisper)

---

## 🌟 Overview

**Civil Floor Plan Generator** is an AI-powered architectural design system that converts **natural language and voice inputs** into **valid 2D floor plans and real-time 3D visualizations**.

Traditional CAD and floor-planning tools require technical drafting skills, complex workflows, and prior architectural knowledge. This project removes those barriers by allowing users to **describe their requirements in plain language or voice**, while the system automatically generates a **non-overlapping, structurally coherent layout** that follows basic civil-engineering logic.

The result is a fast, intuitive, and accessible approach to early-stage architectural planning.

---

## 🚀 Key Features

### 🎙️ Intelligent Voice-Based Input
- Powered by **OpenAI Whisper** for accurate speech-to-text transcription.
- Converts spoken requirements directly into structured layout instructions.

**Example:**  
> *“Add a large living room, a master bedroom, and two small bathrooms near the kitchen.”*

---

### 📐 Smart Layout Computation Engine
A rule-based procedural engine that ensures:
- **Zero Overlap** between rooms  
- **Logical Adjacency** (e.g., kitchen near dining, attached bathrooms)
- **Proportional Room Scaling** based on residential standards
- **Clear Architectural Color Coding** for visual readability

---

### 🧊 Real-Time 3D Visualization
- Instant transformation of 2D plans into a **3D Dollhouse View**
- Transparent walls for interior inspection
- **Procedural furniture placement** based on room type
- Fully interactive **Plotly-based 3D scene** (zoom, rotate, pan)

---

## 🎨 Prompting Guide (For Best Results)

Clear and structured prompts lead to more accurate layouts.

### ✅ Recommended Prompt Style
> *“Create a house with a 15x20 living room, a 12x12 bedroom, and a 10x10 kitchen. Add a small balcony next to the bedroom.”*

### 💡 Tips for Judges & Evaluators

| Aspect | Recommendation | Example |
|------|----------------|---------|
| Dimensions | Specify sizes when possible | “20x15 hall” |
| Quantity | Use explicit counts | “three bedrooms” |
| Placement | Describe relative positions | “kitchen near dining” |
| Descriptors | Use size adjectives | “small utility room” |

---

## 🛠️ System Architecture

The application follows a **Hybrid Cloud Architecture**, separating user interaction, AI processing, and visualization logic.

### 🔹 Layer 1: Frontend (User Interface)
- **React 18** with **Tailwind CSS** for a clean, modern UI
- Hosted on **Firebase Hosting** for fast global delivery
- Interactive 2D blueprint rendering and prompt input

### 🔹 Layer 2: AI & Computation Backend
- **FastAPI** backend hosted on **Hugging Face Spaces**
- **Dockerized deployment** for portability and reproducibility
- Speech processing via **Whisper**
- Procedural layout generation and 3D scene construction

---

## 📦 Technology Stack

### Frontend
- React  
- Tailwind CSS  
- Plotly.js  
- Axios  
- Lucide Icons  

### Backend
- FastAPI (Python)  
- OpenAI Whisper  
- Pydantic  
- Uvicorn  

### Deployment
- Docker  
- Firebase Hosting  
- Hugging Face Spaces  

---

> ⚠️ **Important Note**  
> This project is a **proof-of-concept** demonstrating how AI can simplify civil-engineering and CAD-style workflows. It focuses on accessibility, automation, and intelligent layout generation rather than replacing professional architectural software.

---

© 2026 Civil Project Team
