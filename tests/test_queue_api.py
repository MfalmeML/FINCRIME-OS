from fastapi.testclient import TestClient
from fincrime_os.api.main import app

client = TestClient(app)


def test_queue_returns_ranked_alerts():
    r = client.get("/queue")
    assert r.status_code == 200
    body = r.json()
    assert body["alerts_considered"] == 5
    assert body["alerts_returned"] <= body["capacity"]
    ranks = [a["rank"] for a in body["ranked"]]
    assert ranks == sorted(ranks)
    values = [a["expected_loss_prevented"] for a in body["ranked"]]
    assert values == sorted(values, reverse=True)


def test_queue_network_case_surfaces_above_isolated_equal_risk():
    r = client.get("/queue")
    body = r.json()
    case_ids = [a["case_id"] for a in body["ranked"]]
    assert case_ids.index("case_3") < case_ids.index("case_1")


def test_queue_priority_labels_valid():
    r = client.get("/queue")
    valid = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
    for a in r.json()["ranked"]:
        assert a["priority"] in valid