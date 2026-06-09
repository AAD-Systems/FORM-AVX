"""
avx_ext/avx_builtins.py
Extensões Python injetadas no ambiente Pyrus.
"""

import struct
import time
import threading
import os as _os_module

AVX_FORMAT = '>Qddffffffff8s'
AVX_SIZE   = 64

_lock_files = threading.Lock()
_open_files = {}


def registrar_builtins(env, pyrus_module=None):
    if pyrus_module is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            '_pyrus_core',
            _os_module.path.join(_os_module.path.dirname(_os_module.path.dirname(__file__)), 'core.py'))
        pyrus_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pyrus_module)

    PyrusBuiltin = pyrus_module.PyrusBuiltin

    def B(name, fn):
        """Registra um builtin corretamente como PyrusBuiltin"""
        env.set(name, PyrusBuiltin(name, fn))

    # ── MAVLink desserialização ──────────────────────────
    def _mavlink_byte(raw, offset):
        if not isinstance(raw, (bytes, bytearray)): return 0
        if int(offset) >= len(raw): return 0
        return raw[int(offset)]

    def _mavlink_int32(raw, offset):
        if not isinstance(raw, (bytes, bytearray)) or int(offset)+4 > len(raw): return 0
        return struct.unpack_from('>i', raw, int(offset))[0]

    def _mavlink_uint16(raw, offset):
        if not isinstance(raw, (bytes, bytearray)) or int(offset)+2 > len(raw): return 0
        return struct.unpack_from('>H', raw, int(offset))[0]

    def _mavlink_float32(raw, offset):
        if not isinstance(raw, (bytes, bytearray)) or int(offset)+4 > len(raw): return 0.0
        return struct.unpack_from('<f', raw, int(offset))[0]

    B('mavlink_byte',    _mavlink_byte)
    B('mavlink_int32',   _mavlink_int32)
    B('mavlink_uint16',  _mavlink_uint16)
    B('mavlink_float32', _mavlink_float32)

    # ── Storage .avx-stream ──────────────────────────────
    def _storage_open(caminho):
        caminho = str(caminho)
        dirpath = _os_module.path.dirname(caminho)
        if dirpath:
            _os_module.makedirs(dirpath, exist_ok=True)
        with _lock_files:
            f = open(caminho, 'ab')
            hid = id(f)
            _open_files[hid] = f
            return hid

    def _storage_write(handle_id, pacote):
        with _lock_files:
            f = _open_files.get(int(handle_id))
            if f is None: 
                return False
            try:
                data = struct.pack(
                    AVX_FORMAT,
                    int(pacote.get('timestamp', int(time.time() * 1e6))),
                    float(pacote.get('lat',             0.0)),
                    float(pacote.get('lon',             0.0)),
                    float(pacote.get('alt',             0.0)),
                    float(pacote.get('speed',           0.0)),
                    float(pacote.get('pitch',           0.0)),
                    float(pacote.get('roll',            0.0)),
                    float(pacote.get('yaw',             0.0)),
                    float(pacote.get('battery_voltage', 0.0)),
                    float(pacote.get('signal_quality',  0.0)),
                    float(pacote.get('climb',           0.0)),
                    b'\x00' * 8,
                )
                f.write(data)
                f.flush()
                return True
            except Exception as e:
                print(f'[Storage] Erro: {e}')
                return False

    def _storage_close(handle_id):
        with _lock_files:
            f = _open_files.pop(int(handle_id), None)
            if f: 
                f.close()
        return None

    def _storage_record_count(caminho):
        caminho = str(caminho)
        if not _os_module.path.exists(caminho): 
            return 0
        return _os_module.path.getsize(caminho) // AVX_SIZE

    def _storage_read_at(caminho, indice):
        caminho = str(caminho)
        indice  = int(indice)
        if not _os_module.path.exists(caminho): 
            return None
        offset = indice * AVX_SIZE
        if offset + AVX_SIZE > _os_module.path.getsize(caminho): 
            return None
        with open(caminho, 'rb') as f:
            f.seek(offset)
            raw = f.read(AVX_SIZE)
        if len(raw) < AVX_SIZE: 
            return None
        v = struct.unpack(AVX_FORMAT, raw)
        return {
            'timestamp':       v[0], 'lat': v[1], 'lon': v[2],
            'alt':             v[3], 'speed': v[4], 'pitch': v[5],
            'roll':            v[6], 'yaw': v[7], 'battery_voltage': v[8],
            'signal_quality':  v[9], 'climb': v[10],
            'tipo':            'REPLAY',
        }

    def _storage_validate(caminho):
        caminho = str(caminho)
        if not _os_module.path.exists(caminho): 
            return 0
        size  = _os_module.path.getsize(caminho)
        resto = size % AVX_SIZE
        if resto != 0:
            with open(caminho, 'ab') as f:
                f.truncate(size - resto)
            print(f'[Storage] Truncado. {(size-resto)//AVX_SIZE} registros OK.')
        return _os_module.path.getsize(caminho) // AVX_SIZE

    B('storage_open',         _storage_open)
    B('storage_write',        _storage_write)
    B('storage_close',        _storage_close)
    B('storage_record_count', _storage_record_count)
    B('storage_read_at',      _storage_read_at)
    B('storage_validate',     _storage_validate)

    # ── Sistema ──────────────────────────────────────────
    def _listar_plugins():
        pasta = 'plugins'
        if not _os_module.path.isdir(pasta): 
            return []
        return [_os_module.path.join(pasta, f)
                for f in sorted(_os_module.listdir(pasta))
                if f.endswith('.pyu')]

    def _tentar(fn, arg):
        try:
            if callable(getattr(fn, 'fn', None)):
                fn.fn(arg)
            return True
        except Exception as e:
            print(f'[Builtin] Erro em listener: {e}')
            return False

    def _timestamp_us():
        return int(time.time() * 1_000_000)

    def _gerar_nome_log():
        ts = int(time.time())
        dirpath = 'logs'
        _os_module.makedirs(dirpath, exist_ok=True)
        return f'logs/voo_{ts}.avx-stream'

    def _has_func(nome):
        return True

    B('listar_plugins', _listar_plugins)
    B('tentar',         _tentar)
    B('timestamp_us',   _timestamp_us)
    B('gerar_nome_log', _gerar_nome_log)
    B('has_func',       _has_func)

    return env
