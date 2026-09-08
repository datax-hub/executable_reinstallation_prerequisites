"""Modelo de resultado de etapa y codigos de salida del proceso."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class ExitCode(IntEnum):
    """Codigos de salida del proceso (ver README)."""

    OK = 0
    ERROR_CRITICO = 1
    SIN_PERMISOS = 2
    ADVERTENCIAS = 3
    REQUIERE_REINICIO = 4


@dataclass
class StageResult:
    """Resultado de una etapa del pipeline.

    ok=True                     -> la etapa termino bien.
    ok=False, critical=False    -> advertencia: se registra y el pipeline continua.
    ok=False, critical=True     -> error critico: el pipeline aborta.
    """

    ok: bool
    message: str
    critical: bool = True
    details: list[str] = field(default_factory=list)
    requiere_reinicio: bool = False
    omitida: bool = False

    @classmethod
    def exito(cls, message, details=None, requiere_reinicio=False):
        return cls(True, message, details=list(details or []),
                   requiere_reinicio=requiere_reinicio)

    @classmethod
    def omitir(cls, message, details=None):
        return cls(True, message, details=list(details or []), omitida=True)

    @classmethod
    def advertencia(cls, message, details=None):
        return cls(False, message, critical=False, details=list(details or []))

    @classmethod
    def fallo(cls, message, details=None):
        return cls(False, message, critical=True, details=list(details or []))

    @property
    def etiqueta(self) -> str:
        if self.omitida:
            return "OMITIDO"
        if self.ok:
            return "OK"
        return "AVISO" if not self.critical else "ERROR"
