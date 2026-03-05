# Polygon Merger (Qt C++ Version)

A Qt C++ application for drawing and merging polygons. Draw two polygons and merge them into a single outline.

## Features

- Draw polygons by clicking to add vertices
- Close a polygon by clicking near the first point
- Drag polygons to move them
- Drag vertices to adjust polygon shape
- Merge two polygons into a single convex hull

## Building

### Prerequisites

- CMake 3.16 or higher
- Qt5 (5.15+) or Qt6
- C++17 compatible compiler

### macOS / Linux

```bash
cd cpp
mkdir build && cd build
cmake ..
make
./PolygonMerger
```

### Windows (Visual Studio)

```bash
cd cpp
mkdir build && cd build
cmake ..
cmake --build . --config Release
.\Release\PolygonMerger.exe
```

### Using Qt Creator

1. Open `CMakeLists.txt` in Qt Creator
2. Configure the project with your Qt kit
3. Build and run

## Usage

1. Click to draw Polygon 1 (blue). Click near the first point to close it.
2. Click "Switch to Polygon 2" to start drawing the second polygon.
3. Draw Polygon 2 (red) the same way.
4. Click "Merge Polygons" to combine them.
5. Drag polygons or vertices to adjust positions.
6. Re-click "Merge" to update after adjustments.
7. Click "Clear All" to start over.

## Notes

- The merge operation uses a convex hull algorithm as a fallback
- For true polygon union operations, consider integrating a library like [Clipper](http://www.angusj.com/delphi/clipper.php) or [CGAL](https://www.cgal.org/)
