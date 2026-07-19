"""Fixtures de pruebas: base de datos aislada y cliente HTTP."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import database
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """El limitador por IP es global al proceso; se limpia entre pruebas."""
    from app.core.ratelimit import login_limiter
    login_limiter.reset()
    yield
    login_limiter.reset()


@pytest.fixture(autouse=True)
def _sync_edit_queue():
    """Procesa la cola de edición en línea (determinista) durante las pruebas."""
    from app.core.config import settings
    from app.modules.gis.editor import StubEditor
    settings.GIS_EDIT_QUEUE_SYNC = True
    StubEditor.reset()
    yield
    StubEditor.reset()


@pytest.fixture()
def db_session():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
    Base.metadata.create_all(bind=engine)
    # Redirige la sesión global usada por el seed/servicios.
    database.SessionLocal = TestingSession
    database.engine = engine
    try:
        yield TestingSession
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        os.unlink(path)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        db = db_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded(db_session):
    """Ejecuta el seed sobre la base de pruebas."""
    from app import seed
    seed.run()
    return db_session


def login(client, username, password="Campo2026!"):
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
