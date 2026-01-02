# layout_engine.py

def generate_layout(plot_size, rooms):
    """
    Generates a simple layout representation based on plot_size and room specifications.
    This is a placeholder function. Replace with your real algorithm.
    
    plot_size: tuple (width, height)
    rooms: dict {room_name: (width, height)}
    
    Returns: dict {room_name: (x, y, width, height)}
    """
    width, height = plot_size
    layout = {}
    x_offset = 0
    y_offset = 0
    
    for room_name, (w, h) in rooms.items():
        if x_offset + w > width:  # move to next row
            x_offset = 0
            y_offset += h
        layout[room_name] = (x_offset, y_offset, w, h)
        x_offset += w
    
    return layout
