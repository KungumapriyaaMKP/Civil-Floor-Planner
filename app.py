from PIL import Image, ImageDraw, ImageFont

# ----------------------------
# Helper functions
# ----------------------------
def parse_plot_size(text):
    w, h = text.lower().replace(" ", "").split("x")
    return int(w), int(h)

def parse_rooms(text):
    rooms = []
    for line in text.strip().split("\n"):
        parts = line.split(",")
        rooms.append({
            "name": parts[0].strip(),
            "w": int(parts[1]),
            "h": int(parts[2]),
            "pos": parts[3].strip().lower() if len(parts) > 3 else "any"
        })
    return rooms

def check_overlap(x, y, rw, rh, placed_rooms):
    """Returns True if the rectangle overlaps with any placed room"""
    for px, py, pw, ph in placed_rooms.values():
        if (x < px + pw and x + rw > px and y < py + ph and y + rh > py):
            return True
    return False

# ----------------------------
# Raw plan generator
# ----------------------------
def generate_raw_plan(plot_size, room_text):
    plot_w, plot_h = parse_plot_size(plot_size)
    rooms = parse_rooms(room_text)

    CANVAS_W, CANVAS_H = 900, 600
    MARGIN = 40
    PADDING = 10

    scale = min(
        (CANVAS_W - 2 * MARGIN) / plot_w,
        (CANVAS_H - 2 * MARGIN) / plot_h
    )

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#f2f2f2")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # Plot boundary
    px0, py0 = MARGIN, MARGIN
    px1 = px0 + int(plot_w * scale)
    py1 = py0 + int(plot_h * scale)
    draw.rectangle([px0, py0, px1, py1], outline="black", width=6)
    draw.text((px0, py0 - 15), f"PLOT {plot_w} x {plot_h}", fill="black", font=font)

    placed = {}

    # ----------------------------
    # First pass: absolute positions
    # ----------------------------
    for room in rooms:
        rw = int(room["w"] * scale)
        rh = int(room["h"] * scale)
        pos = room["pos"]

        if pos == "top-right":
            x = px1 - rw - PADDING
            y = py0 + PADDING
        elif pos == "top-left":
            x = px0 + PADDING
            y = py0 + PADDING
        elif pos == "bottom-left":
            x = px0 + PADDING
            y = py1 - rh - PADDING
        elif pos == "bottom-right":
            x = px1 - rw - PADDING
            y = py1 - rh - PADDING
        elif pos == "center":
            x = px0 + (px1 - px0)//2 - rw//2
            y = py0 + (py1 - py0)//2 - rh//2
        elif pos == "entrance":
            x = px0 + (px1 - px0)//2 - rw//2
            y = py1 - rh - PADDING
        else:
            continue

        # Avoid overlap
        while check_overlap(x, y, rw, rh, placed):
            y += 10
            if y + rh > py1:
                y = py0 + PADDING
                x += 10

        placed[room["name"].lower()] = (x, y, rw, rh)

    # ----------------------------
    # Second pass: relative & auto
    # ----------------------------
    cursor_x = px0 + PADDING
    cursor_y = py0 + PADDING + 150

    for room in rooms:
        name = room["name"].lower()
        if name in placed:
            continue

        rw = int(room["w"] * scale)
        rh = int(room["h"] * scale)
        pos = room["pos"]

        # Relative positioning
        if "left-of-" in pos:
            target_name = pos.replace("left-of-", "")
            if target_name in placed:
                tx, ty, tw, th = placed[target_name]
                x = tx - rw - PADDING
                y = ty
            else:
                x, y = cursor_x, cursor_y
        elif "right-of-" in pos:
            target_name = pos.replace("right-of-", "")
            if target_name in placed:
                tx, ty, tw, th = placed[target_name]
                x = tx + tw + PADDING
                y = ty
            else:
                x, y = cursor_x, cursor_y
        else:  # auto-placement
            x, y = cursor_x, cursor_y

        # Avoid overlap
        while check_overlap(x, y, rw, rh, placed):
            x += 10
            if x + rw > px1:
                x = px0 + PADDING
                y += 10
                if y + rh > py1:
                    break  # No space left

        placed[name] = (x, y, rw, rh)
        cursor_x = x + rw + 20
        if cursor_x + rw > px1:
            cursor_x = px0 + PADDING
            cursor_y += rh + 20

    # ----------------------------
    # Draw rooms
    # ----------------------------
    for room in rooms:
        name = room["name"].lower()
        x, y, rw, rh = placed[name]

        draw.rectangle([x, y, x + rw, y + rh], outline="black", width=4)
        label = f'{room["name"]}\n{room["w"]}x{room["h"]}'
        for i, line in enumerate(label.split("\n")):
            draw.text((x + 5, y + 5 + i*10), line, fill="black", font=font)

    return img
