import os
from dotenv import load_dotenv

load_dotenv()

# Autodesk APS
APS_HOST = "https://developer.api.autodesk.com"
APS_CLIENT_ID = os.environ.get("APS_CLIENT_ID", "")
APS_CLIENT_SECRET = os.environ.get("APS_CLIENT_SECRET", "")
APS_SCOPES = "data:read data:write data:create bucket:create bucket:read"

# Cyvl data
AWS_PROFILE = os.environ.get("AWS_PROFILE", "cyvl-hackathon")
BUCKET = "s3://cyvl-hackathon"
LAZ_DIR = os.environ.get("LAZ_DIR", "")  # where Xavier downloaded the tiles

# Default work area: one block around Davis Square (lon/lat WGS84)
DEFAULT_BBOX = (-71.1235, 42.3955, -71.1200, 42.3980)

# Tile download budget
DEFAULT_CAP_GB = 10.0
