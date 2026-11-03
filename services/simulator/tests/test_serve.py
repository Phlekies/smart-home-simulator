"""One local process for the compiled interface and the API (B-128)."""

import pytest
from fastapi.testclient import TestClient

from smart_environment import serve
from smart_environment.api import app


@pytest.fixture
def dist(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><title>Simulador</title>", encoding="utf-8")
    (tmp_path / "assets" / "app.js").write_text("console.log('ok')", encoding="utf-8")
    return tmp_path


@pytest.fixture
def served(dist):
    route = serve.mount_web(app, dist)
    try:
        yield TestClient(app)
    finally:
        app.router.routes.remove(route)  # leave the shared app as the other tests expect it


def test_interface_and_api_share_one_origin(served):
    page = served.get("/")
    assert page.status_code == 200 and "<title>Simulador</title>" in page.text
    assert served.get("/assets/app.js").text == "console.log('ok')"
    assert served.get("/api/health").json()["status"] == "ok"
    example = served.get("/api/examples/apartment").json()
    assert served.post("/api/simulations", json={"project": example}).status_code == 200


def test_unknown_paths_are_not_routed_to_the_api(served):
    assert served.get("/api/nope").status_code == 404
    assert served.get("/nope.js").status_code == 404


def test_missing_build_stops_with_the_command_to_make_it(tmp_path):
    with pytest.raises(SystemExit, match="npm --prefix apps/web run build"):
        serve.mount_web(app, tmp_path)
    assert not any(getattr(route, "name", None) == "web" for route in app.routes)


def test_main_listens_on_loopback_only(dist, monkeypatch):
    calls = []
    monkeypatch.setattr("uvicorn.run", lambda target, host, port: calls.append((target, host, port)))
    try:
        serve.main(["--port", "8123", "--dist", str(dist)])
    finally:
        app.router.routes[:] = [r for r in app.routes if getattr(r, "name", None) != "web"]
    assert calls == [(app, "127.0.0.1", 8123)]
