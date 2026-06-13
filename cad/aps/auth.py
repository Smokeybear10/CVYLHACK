import base64
import requests
from config import APS_HOST, APS_CLIENT_ID, APS_CLIENT_SECRET, APS_SCOPES


def basic_auth_header(client_id, client_secret):
    raw = f"{client_id}:{client_secret}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def get_token(scopes=APS_SCOPES):
    """2-legged client-credentials token. POST /authentication/v2/token, Basic auth header."""
    r = requests.post(
        f"{APS_HOST}/authentication/v2/token",
        headers={
            "Authorization": basic_auth_header(APS_CLIENT_ID, APS_CLIENT_SECRET),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials", "scope": scopes},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]
