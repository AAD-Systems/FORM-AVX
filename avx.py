#!/usr/bin/env python3
"""
avx.py — FORM AVX Launcher
Ground Control Station para drones — feita em Pyrus 🍐

Uso:
    python avx.py                        → simulador com UI (se PyQt6 disponível)
    python avx.py --mode sim             → simulador
    python avx.py --mode live            → MAVLink UDP:14550
    python avx.py --mode serial          → MAVLink Serial
    python avx.py --mode replay          → replay de log
    python avx.py --headless             → sem UI, só terminal
    python avx.py --replay logs/voo.avx-stream --mode replay

    python avx.py test                   → roda todos os testes
    python avx.py info                   → informações do sistema
"""

import sys
import os
import queue
import threading
import argparse
import importlib.util
import time

# ── Raiz do projeto
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# ── Verifica disponibilidade do PyQt6
try:
    import PyQt6
    HAS_QT = True
except ImportError:
    HAS_QT = False


# ══════════════════════════════════════════════════════
# CARREGAMENTO DO INTERPRETADOR PYRUS
# ══════════════════════════════════════════════════════

def _load_pyrus():
    """Importa core.py como módulo (evita conflito com nome 'core')."""
    spec = importlib.util.spec_from_file_location(
        'pyrus_core', os.path.join(ROOT, 'core.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_builtins():
    """Importa avx_ext/avx_builtins.py."""
    spec = importlib.util.spec_from_file_location(
        'avx_builtins', os.path.join(ROOT, 'avx_ext', 'avx_builtins.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ══════════════════════════════════════════════════════
# CORE ENGINE RUNNER
# ══════════════════════════════════════════════════════

def iniciar_core(modo: str, fila_ui: queue.Queue = None,
                 replay_file: str = '', serial_port: str = '/dev/ttyUSB0'):
    """
    Inicializa e executa o Core Engine Pyrus.
    Roda em thread separada quando há UI.
    """
    pyrus   = _load_pyrus()
    ext     = _load_builtins()

    interp = pyrus.Interpreter(
        source_path=os.path.join(ROOT, 'avx.py'))
    env = interp.globals

    # Injeta builtins de hardware e storage
    ext.registrar_builtins(env, pyrus_module=pyrus)

    # Injeta variáveis de configuração
    env.set('MODO_OP',      modo)
    env.set('SERIAL_PORT',  serial_port)
    env.set('REPLAY_FILE',  replay_file)
    env.set('UI_CONNECTED', fila_ui is not None)

    # Injeta ponte para a UI
    if fila_ui is not None:
        def _ui_push(pacote):
            try:
                fila_ui.put_nowait(pacote)
            except queue.Full:
                pass
        env.set('ui_push', pyrus.PyrusBuiltin('ui_push', _ui_push))
    else:
        # Modo headless: ui_push é no-op
        env.set('ui_push', pyrus.PyrusBuiltin('ui_push', lambda p: None))

    # Garante pasta de logs
    os.makedirs(os.path.join(ROOT, 'logs'), exist_ok=True)

    # Executa
    try:
        with open(os.path.join(ROOT, 'core', 'main.pyu'),
                  'r', encoding='utf-8') as f:
            source = f.read()
        pyrus.run_code(source,
                       source_path=os.path.join(ROOT, 'avx.py'),
                       env=env)
    except KeyboardInterrupt:
        print('\n[Core] Encerrado pelo usuário.')
    except SystemExit:
        pass
    except Exception as e:
        print(f'[Core] Erro fatal: {e}', file=sys.stderr)


# ══════════════════════════════════════════════════════
# MODO HEADLESS (terminal puro, sem UI)
# ══════════════════════════════════════════════════════

def rodar_headless(modo: str, replay_file: str = '',
                   serial_port: str = '/dev/ttyUSB0'):
    print(f'\n[AVX] Modo headless — {modo}')
    print('[AVX] Pressione Ctrl+C para encerrar.\n')
    iniciar_core(modo, fila_ui=None,
                 replay_file=replay_file,
                 serial_port=serial_port)


# ══════════════════════════════════════════════════════
# MODO INTERFACE GRÁFICA (PyQt6)
# ══════════════════════════════════════════════════════

def rodar_com_ui(modo: str, replay_file: str = '',
                 serial_port: str = '/dev/ttyUSB0'):
    if not HAS_QT:
        print('[AVX] PyQt6 não encontrado.')
        print('[AVX] Instale com: pip install PyQt6')
        print('[AVX] Rodando em modo headless como fallback...\n')
        rodar_headless(modo, replay_file, serial_port)
        return

    from PyQt6.QtWidgets  import QApplication
    from PyQt6.QtQml      import QQmlApplicationEngine
    from PyQt6.QtCore     import QTimer
    from PyQt6.QtGui      import QGuiApplication

    # Importa bridge (lazy, só quando Qt disponível)
    spec = importlib.util.spec_from_file_location(
        'ui_bridge', os.path.join(ROOT, 'ui', 'ui_bridge.py'))
    ui_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ui_mod)

    fila_ui = queue.Queue(maxsize=300)

    # Core em thread daemon
    t = threading.Thread(
        target=iniciar_core,
        args=(modo, fila_ui, replay_file, serial_port),
        daemon=True, name='AVXCore')
    t.start()

    app    = QGuiApplication(sys.argv)
    app.setApplicationName('FORM AVX')
    app.setApplicationVersion('0.1.0')

    bridge = ui_mod.AVXBridge(fila_ui)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('avx', bridge)
    engine.rootContext().setContextProperty('appVersion', '0.1.0')

    qml_file = os.path.join(ROOT, 'ui', 'qml', 'main.qml')
    engine.load(qml_file)

    if not engine.rootObjects():
        print('[AVX] Erro: falha ao carregar QML.')
        sys.exit(1)

    timer = QTimer()
    timer.setInterval(16)       # 60 Hz
    timer.timeout.connect(bridge.atualizar)
    timer.start()

    print('[AVX] Interface carregada.')
    sys.exit(app.exec())


# ══════════════════════════════════════════════════════
# RUNNER DE TESTES
# ══════════════════════════════════════════════════════

def rodar_testes():
    pyrus = _load_pyrus()
    ext   = _load_builtins()
    os.makedirs(os.path.join(ROOT, 'logs'), exist_ok=True)

    arquivos = [
        os.path.join(ROOT, 'tests', 'test_mavlink.pyu'),
        os.path.join(ROOT, 'tests', 'test_storage.pyu'),
    ]

    total_pass = 0
    total_fail = 0

    for arq in arquivos:
        if not os.path.exists(arq):
            print(f'[Testes] Arquivo não encontrado: {arq}')
            continue

        print(f'\n{"═"*50}')
        print(f'Rodando: {os.path.basename(arq)}')
        print('═'*50)

        # Remove log de teste anterior
        log_teste = os.path.join(ROOT, 'logs', 'teste_unitario.avx-stream')
        if os.path.exists(log_teste):
            os.remove(log_teste)

        interp = pyrus.Interpreter(source_path=arq)
        ext.registrar_builtins(interp.globals, pyrus_module=pyrus)
        interp.globals.set('MODO_OP',      'sim')
        interp.globals.set('UI_CONNECTED', False)
        interp.globals.set('SERIAL_PORT',  '/dev/ttyUSB0')
        interp.globals.set('REPLAY_FILE',  '')

        with open(arq, 'r', encoding='utf-8') as f:
            src = f.read()

        resultado = pyrus.run_code(src, source_path=arq,
                                   env=interp.globals)
        if resultado is not None:
            total_pass += 1
        else:
            total_fail += 1

    print(f'\n{"═"*50}')
    print(f'Arquivos OK: {total_pass} | Com erro: {total_fail}')
    print('═'*50)
    return total_fail == 0


# ══════════════════════════════════════════════════════
# INFO DO SISTEMA
# ══════════════════════════════════════════════════════

def mostrar_info():
    import platform, struct

    pyrus = _load_pyrus()

    print(f"""
╔══════════════════════════════════════════════════╗
║       FORM AVX — Informações do Sistema          ║
╚══════════════════════════════════════════════════╝

  Versão FORM AVX : 0.1.0
  Versão Pyrus    : {pyrus.VERSION}
  Python          : {sys.version.split()[0]}
  Plataforma      : {platform.system()} {platform.machine()}
  Arquitetura     : {struct.calcsize('P')*8}-bit
  Termux          : {'Sim' if 'TERMUX_VERSION' in os.environ else 'Não'}
  PyQt6           : {'Disponível ✅' if HAS_QT else 'Não instalado ❌'}

  Modos disponíveis:
    sim      → Simulador interno (padrão, sem hardware)
    live     → MAVLink via UDP:14550
    serial   → MAVLink via porta Serial
    replay   → Reprodução de log .avx-stream

  Zero dependências para o Core.
  PyQt6 necessário apenas para a interface gráfica.

  🍐 Feito em Alagoas, Brasil
""")


# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        prog='avx',
        description='🍐 FORM AVX — Ground Control Station para drones',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python avx.py                          Simulador com UI
  python avx.py --headless               Simulador sem UI (terminal)
  python avx.py --mode live              Drone real via UDP:14550
  python avx.py --mode serial            Drone via cabo serial
  python avx.py --mode replay \\
    --replay logs/voo.avx-stream         Replay de voo gravado
  python avx.py test                     Roda os testes
  python avx.py info                     Informações do sistema
        """)

    parser.add_argument('comando', nargs='?', default='run',
                        choices=['run', 'test', 'info'],
                        help='Comando a executar (padrão: run)')
    parser.add_argument('--mode', default='sim',
                        choices=['sim', 'live', 'serial', 'replay'],
                        help='Modo de operação (padrão: sim)')
    parser.add_argument('--replay', default='',
                        help='Arquivo .avx-stream para replay')
    parser.add_argument('--serial', default='/dev/ttyUSB0',
                        help='Porta serial (padrão: /dev/ttyUSB0)')
    parser.add_argument('--headless', action='store_true',
                        help='Sem interface gráfica (apenas terminal)')

    args = parser.parse_args()

    if args.comando == 'test':
        ok = rodar_testes()
        sys.exit(0 if ok else 1)

    if args.comando == 'info':
        mostrar_info()
        return

    if args.mode == 'replay' and not args.replay:
        parser.error('--mode replay requer --replay <arquivo.avx-stream>')

    if args.headless or not HAS_QT:
        rodar_headless(args.mode, args.replay, args.serial)
    else:
        rodar_com_ui(args.mode, args.replay, args.serial)


if __name__ == '__main__':
    main()
