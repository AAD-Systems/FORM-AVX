"""
avx_ext — Extensões Python para o FORM AVX
Injetadas no ambiente Pyrus antes de executar qualquer .pyu
"""
from avx_ext.avx_builtins import registrar_builtins

__all__ = ['registrar_builtins']
