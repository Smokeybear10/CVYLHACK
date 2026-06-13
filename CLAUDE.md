# CLAUDE.md

Guidance for Claude Code working in this repo.

## What this is

Cyvl hackathon project (Somerville, MA, June 2026). Build on real Cyvl infrastructure data: LiDAR point clouds, a digital twin of city streets, and CV-detected assets (signs, markings, pavement, distresses). Optionally pair with public Somerville/Boston data. Use one or two sponsor tools (NVIDIA, Autodesk, Ask Boston) in a way that actually fits.

Read [docs/HACKATHON.md](docs/HACKATHON.md), [docs/CYVL_API.md](docs/CYVL_API.md), [docs/SPATIAL_SDK.md](docs/SPATIAL_SDK.md), and [docs/IDEAS.md](docs/IDEAS.md) for context.

## Data access

- REST API base: `https://i3.cyvl.app` — see [docs/CYVL_API.md](docs/CYVL_API.md). Bearer auth with the team API key.
- MCP endpoint: `https://i3.cyvl.app/mcp` (HTTP transport, OAuth). Already added as server `i3`. Run `/mcp` to authenticate.
- Spatial SDK: `pip install "cyvl[viz] @ git+https://github.com/roadgnar/cyvl-spatial-sdk"` for 3D<->2D projection, LiDAR, and the viewer.

Almost every API query needs a `project_id` first (`GET /api/v1/projects`) plus a spatial filter (`bbox` or radius).

## Secrets

The team API key is private. Never commit it. Keep it in a `.env` (gitignored) and read from the environment. Use `CYVL_API_KEY` as the variable name.

## Conventions

- Real Cyvl data only. Do not generate or fall back to mock data, it scores lower with judges. If real data is missing, say so.
- Responses from list endpoints are GeoJSON. Default to GeoJSON / standard GIS formats so output drops into QGIS and CloudCompare.
- Prefer specific, scoped queries over pulling everything. The full point cloud is ~500 GB.

## How the user likes to work

Explain plainly before each step and make design decisions together. Keep prose short and nonchalant. No emojis, no em-dashes.
