import os
import copy
import importlib.util
from urllib.parse import quote
from fastapi.testclient import TestClient
import pytest

# Load the application module directly from src/app.py so tests don't depend on package imports
HERE = os.path.dirname(__file__)
APP_PATH = os.path.abspath(os.path.join(HERE, "..", "src", "app.py"))
spec = importlib.util.spec_from_file_location("app_module", APP_PATH)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

app = app_module.app
activities = app_module.activities

# Keep a deep copy of the initial activities so we can reset between tests
_initial_activities = copy.deepcopy(activities)

@pytest.fixture(autouse=True)
def reset_activities():
    # Reset in-memory activities before each test
    activities.clear()
    activities.update(copy.deepcopy(_initial_activities))
    yield


def test_get_activities():
    client = TestClient(app)
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_unregister():
    client = TestClient(app)
    activity = "Chess Club"
    email = "new_student@example.com"

    # Signup
    res = client.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
    assert res.status_code == 200
    assert email in activities[activity]["participants"]

    # Verify GET sees the participant
    res2 = client.get("/activities")
    assert email in res2.json()[activity]["participants"]

    # Unregister
    res3 = client.delete(f"/activities/{quote(activity)}/participants?email={quote(email)}")
    assert res3.status_code == 200
    assert email not in activities[activity]["participants"]


def test_signup_duplicate_returns_400():
    client = TestClient(app)
    existing = _initial_activities["Chess Club"]["participants"][0]
    res = client.post(f"/activities/{quote('Chess Club')}/signup?email={quote(existing)}")
    assert res.status_code == 400


def test_unregister_not_registered_returns_400():
    client = TestClient(app)
    res = client.delete(f"/activities/{quote('Chess Club')}/participants?email={quote('not@here.com')}")
    assert res.status_code == 400
