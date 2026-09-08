"""RF-02 + RF-11. Control del servicio de Windows via advapi32.

Se usa la API y no `sc.exe` a proposito: la salida de sc esta traducida al
idioma del sistema y parsearla romperia en Windows en espanol (RF-07).
"""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

from ..errors import ServicioError

_advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)

SC_MANAGER_CONNECT = 0x0001
SERVICE_QUERY_STATUS = 0x0004
SERVICE_START = 0x0010
SERVICE_STOP = 0x0020

SERVICE_STOPPED = 1
SERVICE_START_PENDING = 2
SERVICE_STOP_PENDING = 3
SERVICE_RUNNING = 4
SERVICE_CONTROL_STOP = 1

ERROR_SERVICE_DOES_NOT_EXIST = 1060
ERROR_SERVICE_NOT_ACTIVE = 1062
ERROR_SERVICE_ALREADY_RUNNING = 1056

_NOMBRES = {
    SERVICE_STOPPED: "detenido",
    SERVICE_START_PENDING: "iniciandose",
    SERVICE_STOP_PENDING: "deteniendose",
    SERVICE_RUNNING: "iniciado",
    5: "continuando",
    6: "pausandose",
    7: "pausado",
}


class SERVICE_STATUS(ctypes.Structure):
    _fields_ = [
        ("dwServiceType", wintypes.DWORD),
        ("dwCurrentState", wintypes.DWORD),
        ("dwControlsAccepted", wintypes.DWORD),
        ("dwWin32ExitCode", wintypes.DWORD),
        ("dwServiceSpecificExitCode", wintypes.DWORD),
        ("dwCheckPoint", wintypes.DWORD),
        ("dwWaitHint", wintypes.DWORD),
    ]


_advapi32.OpenSCManagerW.restype = wintypes.HANDLE
_advapi32.OpenServiceW.restype = wintypes.HANDLE


def nombre_estado(codigo):
    return _NOMBRES.get(codigo, f"desconocido ({codigo})")


class _Servicio:
    """Context manager sobre un handle de servicio."""

    def __init__(self, nombre, acceso):
        self.nombre = nombre
        self.acceso = acceso
        self._scm = None
        self._svc = None

    def __enter__(self):
        self._scm = _advapi32.OpenSCManagerW(None, None, SC_MANAGER_CONNECT)
        if not self._scm:
            raise ServicioError(
                f"No se pudo abrir el administrador de servicios "
                f"(error {ctypes.get_last_error()})")
        self._svc = _advapi32.OpenServiceW(self._scm, self.nombre, self.acceso)
        if not self._svc:
            codigo = ctypes.get_last_error()
            self.__exit__(None, None, None)
            if codigo == ERROR_SERVICE_DOES_NOT_EXIST:
                return None
            raise ServicioError(
                f"No se pudo abrir el servicio '{self.nombre}' (error {codigo})")
        return self._svc

    def __exit__(self, *_):
        if self._svc:
            _advapi32.CloseServiceHandle(self._svc)
            self._svc = None
        if self._scm:
            _advapi32.CloseServiceHandle(self._scm)
            self._scm = None
        return False


def _consultar(handle):
    estado = SERVICE_STATUS()
    if not _advapi32.QueryServiceStatus(handle, ctypes.byref(estado)):
        raise ServicioError(
            f"No se pudo consultar el estado (error {ctypes.get_last_error()})")
    return estado.dwCurrentState


def existe(nombre):
    with _Servicio(nombre, SERVICE_QUERY_STATUS) as handle:
        return handle is not None


def estado(nombre):
    """Estado actual, o None si el servicio no existe."""
    with _Servicio(nombre, SERVICE_QUERY_STATUS) as handle:
        if handle is None:
            return None
        return _consultar(handle)


def _esperar(handle, objetivo, timeout, intervalo=0.5):
    limite = time.monotonic() + timeout
    actual = _consultar(handle)
    while actual != objetivo and time.monotonic() < limite:
        time.sleep(intervalo)
        actual = _consultar(handle)
    return actual


def detener(nombre, timeout=60):
    """Detiene el servicio y ESPERA confirmacion. Devuelve (ok, estado_final)."""
    acceso = SERVICE_QUERY_STATUS | SERVICE_STOP
    with _Servicio(nombre, acceso) as handle:
        if handle is None:
            return False, None
        actual = _consultar(handle)
        if actual == SERVICE_STOPPED:
            return True, SERVICE_STOPPED
        if actual != SERVICE_STOP_PENDING:
            estructura = SERVICE_STATUS()
            if not _advapi32.ControlService(handle, SERVICE_CONTROL_STOP,
                                            ctypes.byref(estructura)):
                codigo = ctypes.get_last_error()
                if codigo == ERROR_SERVICE_NOT_ACTIVE:
                    return True, SERVICE_STOPPED
                raise ServicioError(
                    f"No se pudo enviar la orden de detencion (error {codigo})")
        final = _esperar(handle, SERVICE_STOPPED, timeout)
        return final == SERVICE_STOPPED, final


def iniciar(nombre, timeout=90):
    """Inicia el servicio y ESPERA confirmacion. Devuelve (ok, estado_final)."""
    acceso = SERVICE_QUERY_STATUS | SERVICE_START
    with _Servicio(nombre, acceso) as handle:
        if handle is None:
            return False, None
        actual = _consultar(handle)
        if actual == SERVICE_RUNNING:
            return True, SERVICE_RUNNING
        if actual != SERVICE_START_PENDING:
            if not _advapi32.StartServiceW(handle, 0, None):
                codigo = ctypes.get_last_error()
                if codigo != ERROR_SERVICE_ALREADY_RUNNING:
                    raise ServicioError(
                        f"No se pudo iniciar el servicio (error {codigo})")
        final = _esperar(handle, SERVICE_RUNNING, timeout)
        return final == SERVICE_RUNNING, final
