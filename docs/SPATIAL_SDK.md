# Cyvl Spatial SDK

Python SDK for working with Cyvl street-level imagery, LiDAR point clouds, and infrastructure data for Somerville, MA. Full 3D<->2D projection using the same calibration and SLAM poses as Cyvl's production pipeline.

Repo: https://github.com/roadgnar/cyvl-spatial-sdk

## What's in the dataset

- 311,784 posed camera frames with validated 6-DoF poses and calibrated intrinsics.
- 514 LiDAR tiles in COPC format, queryable over HTTP.
- 215k infrastructure features (pavement conditions, distresses, signs, road markings).

## Install

```bash
pip install "cyvl[viz] @ git+https://github.com/roadgnar/cyvl-spatial-sdk"
```

## Core functions

- `cyvl.load_scene()` — load imagery and spatial data.
- `frame.points_in_view()` — project LiDAR points into a photo.
- `frame.project()` / `frame.unproject()` — convert between pixels and 3D world coordinates.
- `frame.open_viewer()` — browser 3D viewer with calibrated camera rendering.
- `cyvl.measure()` — extract real-world measurements from photos.

## What you can build with it

- Depth maps aligned to any photo.
- NeRF / Gaussian Splat training exports (no COLMAP needed).
- PLY exports for CAD software (pairs well with the Autodesk track).
- Text-to-3D object location via SAM3 segmentation (through fal.ai), which lifts a text prompt to 3D coordinates using LiDAR depth.

## Why it matters for the hackathon

This is the bridge between the flat REST API and real spatial work. If your idea needs measurements, 3D geometry, or putting CV detections into world coordinates, start here instead of the raw point cloud. Language is ~90% Python.
