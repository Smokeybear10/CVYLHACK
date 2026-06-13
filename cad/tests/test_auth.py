import base64
from aps.auth import basic_auth_header


def test_basic_auth_header_base64_of_id_colon_secret():
    h = basic_auth_header("abc", "xyz")
    assert h == "Basic " + base64.b64encode(b"abc:xyz").decode()
