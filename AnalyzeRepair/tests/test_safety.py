"""Pruebas del guard de rutas.

Es el modulo que impide que un error de construccion de rutas destruya el
sistema, asi que interesa mucho mas comprobar lo que RECHAZA que lo que acepta.
"""

from __future__ import annotations

import pytest

from analyzerepair.errors import RutaInsegura
from analyzerepair.safety import assert_ruta_limpiable, assert_ruta_renombrable


@pytest.fixture
def arbol(tmp_path):
    """Reproduce la estructura real: <raiz>/AS OLEDB/{110,140}."""
    raiz = tmp_path / "Program Files" / "Microsoft Analysis Services" / "AS OLEDB"
    (raiz / "110").mkdir(parents=True)
    (raiz / "110" / "msmdlocal.dll").write_text("contenido")
    (raiz / "140").mkdir()
    return raiz


def test_acepta_la_carpeta_de_version_base(arbol):
    assert assert_ruta_limpiable(arbol / "110", [arbol], nombre_esperado="110")


def test_acepta_renombrar_una_version_superior(arbol):
    assert assert_ruta_renombrable(arbol / "140", [arbol])


def test_rechaza_la_raiz_misma(arbol):
    """Vaciar la raiz borraria TODAS las versiones, no solo la 110."""
    with pytest.raises(RutaInsegura):
        assert_ruta_limpiable(arbol, [arbol])


def test_rechaza_ruta_fuera_de_las_raices(arbol, tmp_path):
    ajena = tmp_path / "otra" / "carpeta" / "profunda" / "objetivo"
    ajena.mkdir(parents=True)
    with pytest.raises(RutaInsegura):
        assert_ruta_limpiable(ajena, [arbol])


def test_rechaza_escape_por_puntos(arbol):
    """El caso clasico de ruta mal construida."""
    with pytest.raises(RutaInsegura):
        assert_ruta_limpiable(arbol / "110" / ".." / ".." / ".." / "..", [arbol])


def test_rechaza_ruta_inexistente(arbol):
    with pytest.raises(RutaInsegura):
        assert_ruta_limpiable(arbol / "999", [arbol])


def test_rechaza_archivo_en_vez_de_carpeta(arbol):
    with pytest.raises(RutaInsegura):
        assert_ruta_limpiable(arbol / "110" / "msmdlocal.dll", [arbol])


def test_rechaza_nombre_distinto_al_esperado(arbol):
    """Protege de limpiar la 140 creyendo que es la 110."""
    with pytest.raises(RutaInsegura):
        assert_ruta_limpiable(arbol / "140", [arbol], nombre_esperado="110")


def test_rechaza_renombrar_carpeta_no_numerica(arbol):
    (arbol / "backup").mkdir()
    with pytest.raises(RutaInsegura):
        assert_ruta_renombrable(arbol / "backup", [arbol])


def test_rechaza_carpetas_protegidas_del_sistema(tmp_path):
    """Aunque la ruta este dentro de una raiz permitida."""
    raiz = tmp_path / "a" / "b"
    objetivo = raiz / "Windows"
    objetivo.mkdir(parents=True)
    with pytest.raises(RutaInsegura):
        assert_ruta_limpiable(objetivo, [raiz])


def test_rechaza_ruta_demasiado_corta(tmp_path):
    with pytest.raises(RutaInsegura):
        assert_ruta_limpiable(tmp_path.anchor, [tmp_path.anchor])


def test_lista_de_raices_vacia_no_acepta_nada(arbol):
    with pytest.raises(RutaInsegura):
        assert_ruta_limpiable(arbol / "110", [])


def test_raices_con_none_se_ignoran_sin_romper(arbol):
    """En Windows de 32 bits program_files_x86() devuelve None (RF-08)."""
    assert assert_ruta_limpiable(arbol / "110", [None, arbol])
