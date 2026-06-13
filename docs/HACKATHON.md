# Cyvl Physical AI Hackathon - Full Brief

"Build the Physical Future." June 13, 2026. Cyvl HQ, 76 School Street, Somerville, MA. $12k in prizes.
Brief v2, updated 2026-05-29.

## Who Cyvl is

Vehicle-mounted LiDAR plus 360 imagery turn city streets into digital twins. Their AI detects, scores, and prioritizes infrastructure for 500+ communities nationwide. Mission: accelerate the future of the nation's infrastructure.

## The one-line version

Cyvl drives cars around cities and builds a "digital twin" of the streets: every sign, road marking, pole, and stretch of pavement, captured as LiDAR point clouds and street-level photos, with computer vision labeling the assets and scoring pavement condition. You get access to all of that for Somerville. Build something useful on top of it.

The framing from kickoff: **build a startup, not a demo.** Judges score the startup, not just the code. See [JUDGING.md](JUDGING.md).

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

## Official idea prompts (ideas, not tracks)

From the kickoff deck. You do not have to pick one of these, they are starting points.

1. **Freight that fits** — use LiDAR clearance data to set real truck limits and route freight safely through a city.
2. **Point cloud to CAD** — pipe Cyvl point clouds into Autodesk and generate real, build-ready CAD.
3. **Safe to bike?** — score how safe a city actually is for cyclists, and hold it accountable.
4. **Ask Boston, with eyes** — wire the Ask Boston MCP to Cyvl data so the city can answer with what its streets actually look like.
5. **Truly accessible?** — audit whether a city that calls itself handicap-friendly actually is, curb by curb.
6. **Blind spot tracker** — use point clouds to find driver blind spots and the cheapest fix, even if it is trimming a bush.

Our team's EV-charger siting idea is not on this list, which is fine ("ideas, not tracks"). See [IDEAS.md](IDEAS.md).

## What you present

Every team brings both: a working demo and a presentation that makes the business case. Judges score the startup, not just the code.

- **5 min** your pitch: demo what you built and present the business behind it.
- **+2 min** questions: judges ask, you answer.
- Same format both rounds: at your booth at 5:30 (round one), and on the big screen in the finals at 6:30.

## Prizes

$12k total pool.

- 1st: $8,000
- 2nd: $3,000
- 3rd: $1,000

## Schedule (June 13)

- 9:00 AM — Check-in. Doors open, find your table, runs to 9:20.
- 9:25 AM — Kickoff.
- 9:30 AM — Build. Eight hours, head down.
- 12:00 PM — Lunch (Jersey Mikes).
- 5:30 PM — Booth judging. Judges come to your table, round one, be ready.
- 6:30 PM — Finals. Top teams present on the big screen.
- 7:30 PM — Awards.

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

## Where everything lives

Everything is pinned in the Discord: docs, sample data, and access keys. Start there.

- **Data** — Cyvl API: LiDAR point clouds, 360 imagery, and condition data from real cities.
- **Design** — Autodesk APS: CAD, model, and viewer APIs for turning data into designs.
- **Docs** — pinned in Discord: guides, sample code, and keys, all in the server.

## Rules and scoring

- Real Cyvl data is the point. Fake data scores a 0 on the data criterion (a quarter of the total). See [JUDGING.md](JUDGING.md).
- Build must come from real Somerville Cyvl data, optionally paired with real external sources.
- "Google Maps clone" is named as a 0 on technical. Do something Maps cannot.
- Use one or two sponsor tools well. More is not better.
- Before committing to a direction, search for existing work that already solves it. Reframing a known solution as novel is the most common mistake.
- Keep the API key private. Do not commit it to a public repo.

## Support and contacts

- Discord #questions channel. Post anything, or grab a mentor on the floor all day.
- Cyvl engineers on-site 9:30 AM to 5:00 PM. If the API goes down, flag staff for the offline dataset.

Cyvl team on the floor:
- Daniel Pelaez, CEO
- Noah Parker, CTO
- Lily Jiang, SWE
- Brian Wang, SWE Intern
- Xavier Nishikawa, SWE Intern
