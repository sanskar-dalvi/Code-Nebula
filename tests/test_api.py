from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_process_endpoint():
    response = client.post(
        "/process",
        json={"filepath": "input_code/SampleController.cs"}
    )
    # Check status code
    assert response.status_code == 200
    # Check response content
    data = response.json()
    assert data["status"] == "success"
    assert data["nodes"] == 1
