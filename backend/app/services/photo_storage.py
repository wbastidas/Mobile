"""Almacenamiento y ensamblado de fotos subidas por chunks (RF-SYNC.3/4).

Los chunks se guardan en un directorio de staging por hash; cuando se reciben
todos se ensamblan, se verifica la integridad (SHA-256) y se mueve el archivo
final. La operación es idempotente: reenviar un chunk simplemente lo sobrescribe.
"""
import hashlib
import os
import re
import shutil
from dataclasses import dataclass

from app.core.config import settings

# Un SHA-256 en hex: exactamente 64 caracteres [0-9a-f]. Cualquier otra cosa se
# rechaza ANTES de tocar el sistema de archivos (previene path traversal).
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class InvalidStorageKey(ValueError):
    """Identificador inválido para rutas de almacenamiento (posible traversal)."""


@dataclass
class ChunkResult:
    received: int
    total: int
    complete: bool
    verified: bool


def _require_sha(sha256: str) -> str:
    if not SHA256_RE.fullmatch(sha256 or ""):
        raise InvalidStorageKey("Hash SHA-256 inválido.")
    return sha256


def _safe_segment(value: str) -> str:
    """Sanitiza un segmento de ruta (p. ej. work_id): solo [A-Za-z0-9._-]."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", value or "")
    if not cleaned or cleaned in {".", ".."}:
        raise InvalidStorageKey("Segmento de ruta inválido.")
    return cleaned


def _incoming_dir(sha256: str) -> str:
    return os.path.join(settings.PHOTO_STORAGE_DIR, "incoming", _require_sha(sha256))


def final_path(work_id: str, sha256: str) -> str:
    """Ruta final pública de una foto verificada."""
    return os.path.join(
        settings.PHOTO_STORAGE_DIR, "photos", _safe_segment(work_id),
        f"{_require_sha(sha256)}.jpg",
    )


def save_chunk(sha256: str, index: int, total: int, data: bytes) -> ChunkResult:
    """Guarda un chunk y reporta el progreso (sin ensamblar todavía)."""
    d = _incoming_dir(sha256)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"part_{index:06d}"), "wb") as f:
        f.write(data)
    received = len([n for n in os.listdir(d) if n.startswith("part_")])
    return ChunkResult(received=received, total=total, complete=received >= total, verified=False)


def assemble_and_verify(sha256: str, total: int, work_id: str) -> ChunkResult:
    """Ensambla los chunks en orden, verifica el hash y mueve el archivo final.

    Devuelve verified=False si falta algún chunk o el hash no coincide (el trabajo
    quedará pendiente para reintento, RN-04).
    """
    d = _incoming_dir(sha256)
    if not os.path.isdir(d):
        return ChunkResult(0, total, complete=False, verified=False)

    parts = sorted(n for n in os.listdir(d) if n.startswith("part_"))
    if len(parts) < total:
        return ChunkResult(len(parts), total, complete=False, verified=False)

    hasher = hashlib.sha256()
    final = final_path(work_id, sha256)
    os.makedirs(os.path.dirname(final), exist_ok=True)
    with open(final, "wb") as out:
        for name in parts:
            with open(os.path.join(d, name), "rb") as p:
                chunk = p.read()
                hasher.update(chunk)
                out.write(chunk)

    verified = hasher.hexdigest() == sha256
    if verified:
        shutil.rmtree(d, ignore_errors=True)  # limpia el staging
    else:
        os.remove(final)  # integridad fallida: descarta para reintentar
    return ChunkResult(len(parts), total, complete=True, verified=verified)
