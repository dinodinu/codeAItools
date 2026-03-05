# Polygon Merger (PyQt5)

Interactive desktop app to draw two polygons, edit them freely, and merge them into a single outline.

## Features

- Draw Polygon 1 (blue) and Polygon 2 (red) on a canvas.
- Close polygons by clicking near the first vertex.
- Drag any polygon body to reposition it.
- Drag any vertex to reshape polygons at any time.
- Merge both polygons into one green outline.
- Move/edit and merge again to recompute the final outline.

## Requirements

- Python 3.9+
- macOS/Windows/Linux

## Installation

1. Open terminal in project folder:

```bash
cd /tmp/polygon_merger
```

2. On macOS, if pip install fails with Xcode license error, run:

```bash
sudo xcodebuild -license accept
```

3. Install dependencies:

```bash
pip3 install -r requirements.txt
```

## Run

```bash
python3 main.py
```

## How to use

1. Draw Polygon 1 (blue).
2. Click `Switch to Polygon 2` and draw Polygon 2 (red).
3. Click `Merge Polygons` to compute the combined green polygon.
4. At any time:
   - Drag a polygon body to move it.
   - Drag vertices to adjust shape.
5. Click `Merge Polygons` again after edits to refresh the merged outline.

## Notes

- Merge uses `shapely` union when available.
- If `shapely` is unavailable, a convex hull fallback is used.
# Polygon Merger - Qt Application

A PyQt5 application for drawing and merging two polygons with overlap handling.

## Features

- **Interactive Canvas Drawing**: Click to add vertices and create polygons
- **Two Polygon Support**: Draw two separate polygons with visual distinction
- **Drag to Move All Polygons**: Click and drag any polygon (blue, red, or merged green) to reposition it
- **Vertex Editing**: Click and drag individual vertices to adjust polygon shape anytime
- **Smart Polygon Merging**: Automatically merges overlapping polygons considering shared edges
- **Re-merge After Moving**: Move individual polygons or edit vertices and merge again to update the result
- **Visual Feedback**: Color-coded polygons (blue, red) and merged result (green)
- **Cursor Hints**: Crosshair when hovering over vertices, open hand over polygons, closed hand when dragging
- **Easy to Use**: Simple click-to-draw interface with automatic polygon closure

## Installation

1. Install Python 3.7 or higher

2. **macOS Users**: If you encounter issues with pip, you may need to accept the Xcode license first:

```bash
sudo xcodebuild -license accept
```

3. Install dependencies:

```bash
pip3 install -r requirements.txt
```

**Note**: If `pip` command is not found, use `pip3` instead. On macOS, you may need to use `python3` instead of `python`.

## Usage

Run the application:

```bash
python3 main.py
```

Or if you're on a system where `python` points to Python 3:

```bash
python main.py
```

### How to Use:

1. **Draw Polygon 1 (Blue)**:
   - Click on the canvas to add vertices
   - The first point is shown larger
   - Click near the first point to close the polygon (within 15 pixels)
   - You can drag the completed polygon to reposition it

2. **Draw Polygon 2 (Red)**:
   - Click "Switch to Polygon 2" button
   - Draw the second polygon using the same method
   - You can drag this polygon to reposition it as well

3. **Merge Polygons**:
   - Click "Merge Polygons" button
   - The merged result will be shown in green
   - The algorithm considers overlapping edges and creates a unified outline

4. **Move Polygons**:
   - Click and drag any polygon (blue, red, or green) to move it to a different location
   - The cursor changes to an open hand when hovering, closed hand when dragging
   - Moving blue or red polygons clears the merge, allowing you to re-merge at new positions

5. **Edit Vertices**:
   - Click and drag any vertex (corner point) to adjust the polygon shape
   - The cursor changes to a crosshair (✛) when hovering over a vertex
   - Editing vertices of blue or red polygons clears the merge
   - You can edit vertices at any time, even after merging

6. **Re-merge After Editing**:
   - After moving polygons or editing vertices, click "Merge Polygons" again to update the result

7. **Clear All**:
   - Click "Clear All" to start over

## Algorithm

The application uses:
- **Shapely library**: For robust polygon union operations with proper handling of overlapping edges
- **Fallback convex hull**: If Shapely is not available, uses Graham scan algorithm

The merge operation creates a single polygon outline that represents the union of both input polygons, properly handling:
- Overlapping areas
- Shared edges
- Complex intersections

All polygons (individual and merged) can be repositioned by clicking and dragging, using a ray-casting algorithm for hit detection. Individual vertices can also be edited by clicking and dragging them to adjust polygon shapes. When individual polygons are moved or their vertices are edited, the merge is cleared, allowing you to reposition and re-merge them at different locations or with different shapes.

## Requirements

- Python 3.7+
- PyQt5
- Shapely (optional but recommended for better results)

## Project Structure

```
polygon_merger/
├── main.py              # Main application window and UI controls
├── canvas_widget.py     # Canvas drawing and polygon merging logic
├── requirements.txt     # Python dependencies
└── README.md           # This file
```
