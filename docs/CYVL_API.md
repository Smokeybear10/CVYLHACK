# Cyvl Data API Reference

Pulled from the live OpenAPI spec at https://i3.cyvl.app/openapi.json (v1.0.0).
Swagger UI: https://i3.cyvl.app/docs

RESTful access to Cyvl's infrastructure condition intelligence: pavement conditions, distresses, assets, signs, and striping, with spatial filters and multiple export formats.

## Base URL

```
https://i3.cyvl.app
```

## Authentication

Bearer token (HTTP `Authorization` header). Use your team API key.

```
Authorization: Bearer <YOUR_TEAM_API_KEY>
```

Example:

```bash
curl -H "Authorization: Bearer $CYVL_API_KEY" \
  "https://i3.cyvl.app/api/v1/projects"
```

The `/mcp` endpoint uses OAuth instead (browser login). The REST API uses the bearer key.

## Common spatial filters

Most list endpoints take a `project_id` (required) plus at least one spatial filter:

- `bbox` — bounding box string `west,south,east,north`
- `radius_lat`, `radius_lng`, `radius_meters` — circular filter around a point
- `limit`, `cursor` — pagination (cursor-based)

Responses are GeoJSON FeatureCollections where geometry applies.

## Asset types (enum)

`pavement`, `sign`, `above_ground_asset`, `distress`, `striping`, `centerline`

## Severity (enum)

`low`, `medium`, `high`

## Endpoints

### Projects
- `GET /api/v1/projects` — list projects. Get the `project_id` you need here first.

### Infrastructure (unified spatial query)
- `GET /api/v1/infrastructure/query` — query assets by spatial filter, returns GeoJSON with pagination. At least one of `bbox` or radius is required.
  - `project_id` (required), `asset_types[]`, `bbox`, `radius_lat`/`radius_lng`/`radius_meters`
  - `condition_min`/`condition_max` (PCI 0-100), `severity[]`, `functional_class[]`, `surface_type[]`, `era`
  - `limit`, `cursor`, `include_geometry`

### Pavement
- `GET /api/v1/pavement/scores` — pavement score records with line geometry. Filters: `label[]` (PCI labels), `score_min`/`score_max`, `era`, spatial, pagination.
- `GET /api/v1/pavement/scores/{inspect_id}` — single score detail.
- `GET /api/v1/pavement/segments` — pavement segments.
- `GET /api/v1/pavement/distresses` — distress records.
- `GET /api/v1/pavement/cells` — inspection cells.
- `GET /api/v1/pavement/pci-distribution` — PCI distribution summary.
- `GET /api/v1/pavement/distress-breakdown` — distress breakdown summary.

### Signs
- `GET /api/v1/signs` — sign inventory as GeoJSON. Filters: `mutcd[]`, `category[]`, `condition[]`, spatial, pagination.
- `GET /api/v1/signs/statistics` — sign stats.
- `GET /api/v1/signs/{sign_id}` — single sign.

### Assets (above-ground)
- `GET /api/v1/assets` — above-ground assets as GeoJSON. Filters: `asset_type[]`, `condition[]`, spatial, pagination.
- `GET /api/v1/assets/statistics` — asset stats.
- `GET /api/v1/assets/inventory` — asset inventory.
- `GET /api/v1/assets/detail/{asset_id}` — full detail.
- `GET /api/v1/assets/{asset_id}` — single asset.
- `GET /api/v1/assets/{asset_id}/imagery` — imagery for an asset.
- `GET /api/v1/assets/{asset_id}/history` — history for an asset.

### Markings / striping
- `GET /api/v1/markings` — striping and marking features. Filters: `category[]`, `type[]`, `color[]`, `condition[]`, spatial, pagination.
- `GET /api/v1/markings/statistics` — marking stats.
- `GET /api/v1/markings/{marking_id}` — single marking.

### Reference lookups
- `GET /api/v1/reference/distress-types`
- `GET /api/v1/reference/asset-types`
- `GET /api/v1/reference/sign-categories`
- `GET /api/v1/reference/mutcd-codes`
- `GET /api/v1/reference/line-types`

### Image embeddings (semantic image search)
- `POST /api/v1/embeddings/query` — natural language image search. Body fields: `query` (text), `project_id`, `page_size` (max 5000), `min_score` (0-1), `city`, `state`, `scan_id`, `bbox` `[west,south,east,north]`, `lat`/`lon`/`radius_m`, `detected_signs[]` (MUTCD codes), `detected_objects[]`, `has_signs`, `point_type`.
- `POST /api/v1/embeddings/query_image` — search by example image.
- `GET /api/v1/embeddings/results/{search_id}` — paged search results.
- `POST /api/v1/embeddings/browse` — browse images.
- `GET /api/v1/embeddings/browse/{browse_id}` — browse page.
- `GET /api/v1/embeddings/projects` — projects with embeddings.
- `GET /api/v1/embeddings/collections` — image collections.

### System / OAuth
- `GET /health`, `GET /ready`
- `GET /.well-known/oauth-protected-resource`, `/.well-known/oauth-protected-resource/mcp`, `/.well-known/oauth-authorization-server`
- `GET|POST /register`

## Quick start

```bash
export CYVL_API_KEY="..."   # from kickoff, keep private

# 1. find your project
curl -H "Authorization: Bearer $CYVL_API_KEY" \
  "https://i3.cyvl.app/api/v1/projects"

# 2. pull bad pavement in a bounding box
curl -H "Authorization: Bearer $CYVL_API_KEY" \
  "https://i3.cyvl.app/api/v1/pavement/scores?project_id=<UUID>&score_max=50&bbox=-71.12,42.37,-71.08,42.41&limit=100"

# 3. semantic image search
curl -X POST -H "Authorization: Bearer $CYVL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"cracked sidewalk near bus stop","project_id":"<UUID>","page_size":50}' \
  "https://i3.cyvl.app/api/v1/embeddings/query"
```

## MCP (for Claude Code / Claude Desktop / Cursor)

Endpoint: `https://i3.cyvl.app/mcp` (HTTP transport, OAuth login).

Add to Claude Code:

```bash
claude mcp add --transport http i3 https://i3.cyvl.app/mcp
```

Then run `/mcp` and authenticate `i3` in the browser. Once connected, ask specific questions and Claude writes and runs the queries for you.
