from fastapi.testclient import TestClient

from fincrime_os.api.main import app

client = TestClient(app)


def test_case_detail_returns_graph_timeline_explanation():
    r = client.get("/case/case_3")
    assert r.status_code == 200
    body = r.json()
    assert body["case_id"] == "case_3"
    assert body["decision"] == "DECLINE"
    assert len(body["graph"]["edges"]) >= 4
    assert len(body["timeline"]) >= 5
    codes = {rc["code"] for rc in body["explanation"]["reason_codes"]}
    assert "RING_OVERRIDE" in codes
    assert "DEVICE_CONNECTIVITY" in codes
    assert body["explanation"]["counterfactual"] != ""


def test_case_404_for_unknown():
    r = client.get("/case/does_not_exist")
    assert r.status_code == 404


def test_workspace_serves_html():
    r = client.get("/workspace")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Investigator Workspace" in r.text