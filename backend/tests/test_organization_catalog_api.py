from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.main import app


client = TestClient(app)


def setup_function():
    app.dependency_overrides.clear()


def teardown_function():
    app.dependency_overrides.clear()


def test_catalog_requires_authenticated_user():
    response = client.get("/api/organization/regionals")
    assert response.status_code == 401


def test_authenticated_catalog_returns_eight_regionals_and_twenty_six_scs():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=10)
    regionals = client.get("/api/organization/regionals")
    assert regionals.status_code == 200
    assert [item["code"] for item in regionals.json()["regionals"]] == ["BA", "CE", "GP", "MG/SPN", "PR", "RJ", "SPE", "SPS"]

    total = 0
    for item in regionals.json()["regionals"]:
        response = client.get(f"/api/organization/regionals/{item['code']}/scs")
        assert response.status_code == 200
        total += len(response.json()["service_centers"])
    assert total == 26


def test_catalog_returns_expected_sc_codes_and_rejects_invalid_regional():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=10)
    expected = {"BA": ["AJU", "FEC", "VDC"], "SPE": ["GRU"], "SPS": ["BRE"]}
    for regional, codes in expected.items():
        response = client.get(f"/api/organization/regionals/{regional}/scs")
        assert [item["code"] for item in response.json()["service_centers"]] == codes
    invalid = client.get("/api/organization/regionals/INVALID/scs")
    assert invalid.status_code == 404
    assert invalid.json() == {"detail": "REGIONAL_NOT_FOUND"}
