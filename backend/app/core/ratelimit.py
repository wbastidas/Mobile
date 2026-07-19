"""Limitador de tasa por IP para endpoints de autenticación (RNF-01).

Ventana deslizante en memoria del proceso. Suficiente para un despliegue de un
solo nodo; en producción multi-nodo debe respaldarse en Redis o similar (la
interfaz `check()` no cambia).
"""
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from fastapi import HTTPException, status

from app.core.config import settings


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: Optional[str]) -> None:
        """Registra un intento y lanza 429 si la IP superó el límite."""
        if not key:
            return
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            cutoff = now - self.window_seconds
            while hits and hits[0] < cutoff:
                hits.popleft()
            if len(hits) >= self.max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Demasiados intentos desde esta dirección; espere un momento.",
                )
            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


# Limitador de logins: compartido por login web y móvil.
login_limiter = SlidingWindowLimiter(
    max_requests=settings.LOGIN_RATE_LIMIT_PER_MINUTE,
    window_seconds=60,
)
