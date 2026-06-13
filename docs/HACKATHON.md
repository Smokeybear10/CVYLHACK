# Cyvl Hackathon - Full Brief

Somerville, MA. June 13, 2026. CYVL, 76 School Street.
Brief v2, updated 2026-05-29.

## The one-line version

Cyvl drives cars around cities and builds a "digital twin" of the streets: every sign, road marking, pole, and stretch of pavement, captured as LiDAR point clouds and street-level photos, with computer vision labeling the assets and scoring pavement condition. You get access to all of that for Somerville. Build something useful on top of it.

## What you can do before kickoff

Explore freely. Get into the platform, click around the Somerville digital twin, inspect a sign, look at how geometry layers over real imagery. Come with ideas, not code. The only thing to hold off on is building your actual project.

## The data Cyvl gives you (Somerville)

- Street-level capture across the whole city.
- LiDAR point clouds. Full Somerville cloud is ~500 GB, so download only the sections you need from the platform. Ask staff directly if you want the whole thing.
- Digital twin: geometry plus asset attributes.
- CV-detected assets: signs, road markings, pavement features, distresses.
- It is a snapshot, not a live feed. No real-time updates.

## Sponsor tools (use one or two, not all three)

- **NVIDIA** — train your own model on Cyvl data. A CV model to detect an asset, score pavement, classify imagery, or anything that fits your idea.
- **Autodesk** — turn Cyvl capture data into CAD and 3D design output.
- **Ask Boston** — Cyvl infrastructure data layered with Boston Open Data: 311 requests, Vision Zero crashes, sidewalks, streetlights. Explore at https://askboston.ai.

What matters: the tool has to be genuinely useful to the idea, not tacked on at the end.

## Platform access

- Accept the email invite to the Cyvl platform. You land in the Cyvl Hackathon org on cyvl.app.
- Verification code might be in spam.
- Entry point: https://cyvl.app/projects?chatModal=open
- Login walkthrough: https://www.youtube.com/watch?v=67g9plfDd4U&list=PLN8D9I84Yoz1vjHcmmcZSOuZ6aEJ2gLOi
- Platform overview videos: https://screen.studio/share/Xrin0mX0 and https://screen.studio/share/IdnvbHau
- Reference build for inspiration: https://phi-cyvl.github.io/

## External data you can layer on

Integration is on you. Knowing what exists is what makes it possible.

- MassGIS: https://www.mass.gov/massgis-data-layers
- Somerville open data portal
- USGS National Map (elevation, hydrography)
- OpenStreetMap (road network, land use)
- Boston Open Data via Ask Boston (311, Vision Zero crashes, sidewalks, streetlights)

## What you get at Saturday kickoff

- Team confirmation.
- Team API key with $200 of Anthropic credit.
- Offline dataset and tool guides.
- On-site engineering support.

## Tools to install

- **QGIS** — free GIS desktop app. Visualize the dataset, overlay government layers, do spatial analysis without code. https://qgis.org
- **CloudCompare** — open source 3D point cloud viewer, loads .las/.laz. https://www.cloudcompare.org
- **Claude Code** — connect it to the Cyvl MCP. Works best with a specific question ("pavement condition on Main St?") over a vague one.

## API access

- Main docs (Swagger UI): https://i3.cyvl.app/docs
- MCP endpoint: https://i3.cyvl.app/mcp
- See [CYVL_API.md](CYVL_API.md) for the full endpoint reference.

You can access: LiDAR point cloud data, digital twin queries (geometry, asset attributes), CV model inference (pavement, signs, markings), and the Cyvl MCP for AI agent integration.

## Rules and scoring

- Real Cyvl data is the point. Mock data scores lower.
- Build must come from real Somerville Cyvl data, optionally paired with real external sources.
- Before committing to a direction, search for existing work that already solves it. Reframing a known solution as novel is the most common mistake.
- Keep the API key private. Do not commit it to a public repo.

## Support

- Discord #questions channel.
- Cyvl engineers on-site 9:30 AM to 5:00 PM. If the API goes down, flag staff for the offline dataset.
