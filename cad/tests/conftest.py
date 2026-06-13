import numpy as np
import pytest


@pytest.fixture
def synthetic_manifest():
    def feat(lon, lat, name):
        return {
            "properties": {
                "filename": name, "lon": lon, "lat": lat,
                "baseUrl": "https://cdn.example", "lasPath": f"/x/{name}",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon - 0.001, lat - 0.001], [lon + 0.001, lat - 0.001],
                    [lon + 0.001, lat + 0.001], [lon - 0.001, lat + 0.001],
                    [lon - 0.001, lat - 0.001],
                ]],
            },
        }
    return {"features": [
        feat(-71.1218, 42.3967, "a.laz"),
        feat(-71.1210, 42.3970, "b.laz"),
        feat(-71.0000, 42.0000, "far.laz"),
    ]}


@pytest.fixture
def synthetic_points():
    rng = np.random.default_rng(0)
    ground = np.column_stack([
        rng.uniform(0, 20, 4000), rng.uniform(0, 20, 4000), np.zeros(4000)])
    car = np.column_stack([
        rng.uniform(4, 8.5, 1500),
        rng.uniform(4.5, 6.3, 1500),
        rng.uniform(0.1, 1.6, 1500),
    ])
    return ground, car
