# Idea Shortlist

From team discussion. Ranked by current preference.

## 1. EV charger siting (favorite)

Use Cyvl data to find the best places to put EV chargers in Somerville. Pair with traffic data to show which sites get the most natural traffic. NVIDIA is moving into the EV space, so it fits the sponsor angle.

- Cyvl signals: poles and above-ground assets (mounting points), pavement/parking layout, curb and sign context.
- External pair: traffic / foot-traffic data, OSM road network, utility proximity.
- Sponsor fit: NVIDIA (train a model to detect viable curb/pole sites), Ask Boston (traffic + city data).
- Open question: framing so it is more than a generic "good spots" map. Lean on real siting constraints (power, parking, ADA, demand).

## 2. Urban cooling / climate resilience

Find areas with high heat exposure, low tree canopy, and high transit ridership. Prioritize stormwater reduction and added shade near schools and bus stops and flood-prone areas.

- Cyvl signals: tree/canopy presence, surface type, drainage assets, bus stop infrastructure.
- External pair: heat maps, flood zones, transit ridership, MassGIS canopy layers.
- Sponsor fit: Ask Boston (climate + city open data overlay).

## 3. Property risk for insurance

Better property risk assessment from nearby infrastructure condition: bad sidewalks, signs, flood exposure, fall hazards, heat damage. Could sell risk scores to insurers.

- Concern: judges may not love "help insurers charge more." Reframe toward homeowner-facing risk awareness or municipal repair prioritization.
- Concern: "infrastructure danger detector" is a crowded space. Needs a sharp niche.

## Other thrown-out ideas

- **Telecom small-cell siting** — carriers and tower companies hunt across dozens of poles to find a viable small-cell site. Same "drive around before finding one" problem EV solves.
- **Outdoor advertising siting** — find the best public places to advertise (big open areas, high visibility) paired with foot/traffic data.

## Recurring theme

Several ideas are "find the best site for X" using Cyvl assets plus traffic data: EV chargers, small cells, ad placements. Same engine, different vertical. Pick the one with the cleanest story and clearest sponsor fit (EV + NVIDIA leads).

## Decision criteria to keep in mind

- Real Cyvl data front and center. No mock data.
- One or two sponsor tools, woven in.
- Check it is not already solved before committing.
