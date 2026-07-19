"""Selección del editor físico por configuración (PD-02)."""
from app.core.config import settings
from app.modules.gis.editor import GeodatabaseEditor, StubEditor, default_editor_factory


def test_default_is_stub():
    settings.GIS_EDITOR = "stub"
    assert isinstance(default_editor_factory(), StubEditor)


def test_oracle_editor_selected():
    settings.GIS_EDITOR = "oracle"
    settings.ORACLE_DSN = "host:1521/orcl"
    settings.ORACLE_USER = "gis"
    settings.ORACLE_PASSWORD = "x"
    try:
        editor = default_editor_factory()
        # Construir NO importa oracledb (solo begin_session lo hace).
        from app.modules.gis.editors_real import OracleSdeEditor
        assert isinstance(editor, OracleSdeEditor)
        assert isinstance(editor, GeodatabaseEditor)
    finally:
        settings.GIS_EDITOR = "stub"


def test_arcpy_editor_selected():
    settings.GIS_EDITOR = "arcpy"
    settings.ARCPY_WORKSPACE = "conn.sde"
    try:
        editor = default_editor_factory()
        from app.modules.gis.editors_real import ArcPyEditor
        assert isinstance(editor, ArcPyEditor)
        assert isinstance(editor, GeodatabaseEditor)
    finally:
        settings.GIS_EDITOR = "stub"


def test_real_editors_implement_full_contract():
    """Ambos editores implementan begin_session/apply/commit/abort."""
    from app.modules.gis.editors_real import ArcPyEditor, OracleSdeEditor
    for cls in (OracleSdeEditor, ArcPyEditor):
        for method in ("begin_session", "apply", "commit", "abort"):
            assert callable(getattr(cls, method))
