# Polygon Merger

A PyQt5 desktop application for drawing two polygons, editing them interactively, and merging them into a single outline.

## Features

- **Draw Polygons**: Click to add vertices; click near the first point to close
- **Drag Polygon Bodies**: Click inside any closed polygon and drag to move it
- **Edit Vertices**: Click and drag any vertex to reshape polygons
- **Merge Polygons**: Combine two overlapping polygons into one unified outline
- **Re-merge After Edits**: Move or reshape polygons and merge again to update

## Installation

### Prerequisites

- Python 3.9 or higher
- macOS / Windows / Linux

### Steps

1. Navigate to the project folder:

```bash
cd /tmp/polygon_merger
```

2. **(macOS only)** If pip fails with Xcode license error:

```bash
sudo xcodebuild -license accept
```

3. Install dependencies:

```bash
pip3 install -r requirements.txt
```

## Usage

Run the application:

```bash
python3 main.py
```

### Workflow

1. **Draw Polygon 1 (Blue)**
   - Click on the canvas to place vertices
   - Click near the first vertex to close the polygon

2. **Switch to Polygon 2**
   - Click the "Switch to Polygon 2" button

3. **Draw Polygon 2 (Red)**
   - Draw the second polygon the same way

4. **Edit Polygons**
   - Drag any polygon body to reposition it
   - Drag any vertex to reshape the polygon
   - Cursor changes: crosshair over vertices, open hand over polygon body

5. **Merge Polygons**
   - Click "Merge Polygons" to create a green unified outline
   - Edit and click "Merge" again to update the result

6. **Clear All**
   - Click "Clear All" to start over

## Technical Details

- **Merge Algorithm**: Uses Shapely's `unary_union` for robust polygon union
- **Fallback**: Convex hull if Shapely is not available
- **Hit Detection**: Ray-casting algorithm for point-in-polygon tests

## Files

```
polygon_merger/
├── main.py           # Application window and controls
├── canvas_widget.py  # Drawing canvas with all interaction logic
├── requirements.txt  # Python dependencies
└── README.md         # This file
```
