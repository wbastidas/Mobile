"""Almacenamiento y ensamblado de fotos subidas por chunks (RF-SYNC.3/4).

Los chunks se guardan en un directorio de staging por hash; cuando se reciben
todos se ensamblan, se verifica la integridad (SHA-256) y se mueve el archivo
final. La operación es idempotente: reenviar un chunk simplemente lo sobrescribe.
"""
import hashlib
import os
import shutil
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class ChunkResult:
    received: int
    total: int
    complete: bool
    verified: bool


def _incoming_dir(sha256: str) -> str:
    return os.path.join(settings.PHOTO_STORAGE_DIR, "incoming", sha256)


def _final_path(work_id: str, sha256: str) -> str:
    return os.path.join(settings.PHOTO_STORAGE_DIR, "photos", work_id, f"{sha256}.jpg")


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
    final = _final_path(work_id, sha256)
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
