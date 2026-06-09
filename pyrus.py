#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  PYRUS CLI — pyrus.py  v0.2.0  "Pear Seed"                  ║
║  Uso:  python pyrus.py <comando> [args]                      ║
║  Targets: Linux · Termux · Raspberry Pi · Windows · macOS   ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import os
import time

# ── Adiciona o diretório do script ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import run_code, run_file, tokenize, VERSION, LexError
from lexer import analisar_tokens

# ── Cores ANSI (desabilitadas automaticamente se não for TTY)
_USE_COLOR = sys.stdout.isatty()

def C(code, txt):
    return f"{code}{txt}\033[0m" if _USE_COLOR else txt

def bold(txt):    return C('\033[1m', txt)
def green(txt):   return C('\033[92m', txt)
def yellow(txt):  return C('\033[93m', txt)
def magenta(txt): return C('\033[95m', txt)
def cyan(txt):    return C('\033[96m', txt)
def gray(txt):    return C('\033[90m', txt)
def red(txt):     return C('\033[91m', txt)
def dim(txt):     return C('\033[2m', txt)


# ══════════════════════════════════════════════════════
# BANNER
# ══════════════════════════════════════════════════════

BANNER = f"""
{bold(magenta('  ██████╗ ██╗   ██╗██████╗ ██╗   ██╗███████╗'))}
{bold(magenta('  ██╔══██╗╚██╗ ██╔╝██╔══██╗██║   ██║██╔════╝'))}
{bold(magenta('  ██████╔╝ ╚████╔╝ ██████╔╝██║   ██║███████╗'))}
{bold(magenta('  ██╔═══╝   ╚██╔╝  ██╔══██╗██║   ██║╚════██║'))}
{bold(magenta('  ██║        ██║   ██║  ██║╚██████╔╝███████║'))}
{bold(magenta('  ╚═╝        ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝'))}
  {cyan(f'v{VERSION}')}  {gray('"Pear Seed" 🍐')}  {dim('Feita em Alagoas, Brasil 🇧🇷')}
"""

HELP_TEXT = f"""
{bold('USO:')}
  {cyan('python pyrus.py')} {yellow('<comando>')} {gray('[argumentos]')}

{bold('COMANDOS:')}
  {yellow('run')}   {gray('<arquivo.pyu>')}    Executa um script Pyrus
  {yellow('lex')}   {gray('<arquivo.pyu>')}    Exibe a fita de tokens (análise léxica)
  {yellow('check')} {gray('<arquivo.pyu>')}    Valida sintaxe sem executar
  {yellow('repl')}                    Inicia o console interativo (REPL)
  {yellow('version')}                 Exibe versão e informações do sistema
  {yellow('help')}                    Mostra esta mensagem

{bold('EXEMPLOS:')}
  {dim('python pyrus.py run  meu_drone.pyu')}
  {dim('python pyrus.py lex  sensor.pyu')}
  {dim('python pyrus.py repl')}

{bold('SINTAXE RÁPIDA:')}
  {green('let')} x = 42{gray(';')}                          {gray('// declaração')}
  {green('let')} msg = {cyan('"olá"')}{gray(';')}                      {gray('// string')}
  {green('func')} soma{gray('(')}a, b{gray(')')} {gray('{')} {green('return')} a + b{gray(';')} {gray('}')}  {gray('// função')}
  {green('while')} x > 0 {gray('{')} x = x {gray('-')} 1{gray(';')} {gray('}')}            {gray('// loop')}
  {green('for')} n {green('in')} lista {gray('{')} print{gray('(')}n{gray(');')} {gray('}')}          {gray('// for-in')}
  {green('spawn')} tarefa{gray('();')}                       {gray('// thread')}
  gpio.write{gray('(')}2, 1{gray(');')}                      {gray('// hardware')}

{bold('SITE:')}    {cyan('https://github.com/Security-Labor/pyrus')}
{bold('DOCS:')}    {cyan('https://security-labor.github.io/pyrus')}
"""


# ══════════════════════════════════════════════════════
# REPL
# ══════════════════════════════════════════════════════

REPL_HELP = f"""
{bold('Comandos REPL especiais:')}
  {yellow('.help')}    Exibe esta ajuda
  {yellow('.clear')}   Limpa a tela
  {yellow('.env')}     Lista todas as variáveis declaradas
  {yellow('.reset')}   Reinicia o ambiente (apaga variáveis)
  {yellow('.lex')}     Mostra tokens da próxima linha digitada
  {yellow('.exit')}    Encerra o REPL  {gray('(ou Ctrl+C / Ctrl+D)')}
"""

def start_repl():
    from core import Interpreter, tokenize, Parser, Environment

    print(BANNER)
    print(f"  {bold('REPL interativo')} — {gray('Digite .help para ajuda, .exit para sair')}\n")

    interp    = Interpreter()
    env       = interp.globals
    hist_file = os.path.expanduser("~/.pyrus_history")
    lex_mode  = False          # quando True, mostra tokens em vez de executar

    # Histórico simples (compatível com Termux sem readline)
    history = []
    try:
        import readline
        readline.set_history_length(500)
        try:
            readline.read_history_file(hist_file)
        except FileNotFoundError:
            pass
        HAS_READLINE = True
    except ImportError:
        HAS_READLINE = False

    def save_history():
        if HAS_READLINE:
            try:
                import readline as rl
                rl.write_history_file(hist_file)
            except Exception:
                pass

    # Buffer para código multi-linha
    buf   = []
    depth = 0  # profundidade de chaves abertas

    while True:
        prompt = (
            gray('... ') if buf else
            (yellow('[lex] ') if lex_mode else magenta('>>> '))
        )
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print(f"\n{gray('Saindo do REPL. Até logo 🍐')}")
            save_history()
            break

        stripped = line.strip()

        # ── Comandos internos do REPL
        if not buf and stripped.startswith('.'):
            cmd = stripped.lower()

            if cmd == '.exit':
                print(gray('Saindo. Até logo 🍐'))
                save_history()
                break

            elif cmd == '.help':
                print(REPL_HELP)

            elif cmd == '.clear':
                os.system('cls' if os.name == 'nt' else 'clear')

            elif cmd == '.reset':
                interp = Interpreter()
                env    = interp.globals
                print(green('✅ Ambiente reiniciado.'))

            elif cmd == '.env':
                user_vars = {
                    k: v for k, v in env.vars.items()
                    if not callable(getattr(v, 'fn', None))
                    and not hasattr(v, '_attrs')
                }
                if not user_vars:
                    print(gray('(nenhuma variável declarada)'))
                else:
                    from core import _pyu_str, _type_name
                    print(bold('\nVariáveis no ambiente:'))
                    for k, v in user_vars.items():
                        print(f"  {cyan(k)}: {yellow(_type_name(v))} = {_pyu_str(v)}")
                    print()

            elif cmd == '.lex':
                lex_mode = not lex_mode
                state    = green('ATIVO') if lex_mode else red('INATIVO')
                print(f"Modo léxico: {state}")

            else:
                print(red(f"Comando desconhecido: '{stripped}'. Digite .help"))
            continue

        # ── Modo léxico
        if lex_mode:
            analisar_tokens(line)
            continue

        # ── Acumula linhas abertas (blocos com { sem })
        if stripped:
            history.append(line)
            buf.append(line)
            depth += line.count('{') - line.count('}')

        # Ainda dentro de um bloco, aguarda mais input
        if depth > 0:
            continue

        if not buf:
            continue

        # ── Executa o bloco acumulado
        source = '\n'.join(buf)
        buf    = []
        depth  = 0

        if not source.strip():
            continue

        run_code(source, env=env)

    save_history()


# ══════════════════════════════════════════════════════
# COMANDO: check (valida sintaxe)
# ══════════════════════════════════════════════════════

def check_file(path):
    if not os.path.exists(path):
        print(red(f"❌ Arquivo não encontrado: '{path}'"))
        return False
    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()
    from core import tokenize, Parser, LexError, ParseError
    try:
        tokens = tokenize(source)
        Parser(tokens).parse()
        print(green(f"✅ Sintaxe OK — '{path}'"))
        return True
    except (LexError, ParseError) as e:
        print(red(f"❌ Erro de sintaxe em '{path}': {e}"))
        return False


# ══════════════════════════════════════════════════════
# COMANDO: version
# ══════════════════════════════════════════════════════

def show_version():
    import platform
    print(BANNER)
    print(f"  {bold('Motor:')}     Pyrus v{VERSION} ({cyan('Pear Seed')})")
    print(f"  {bold('Python:')}    {sys.version.split()[0]}")
    print(f"  {bold('Plataforma:')} {platform.system()} {platform.machine()}")
    print(f"  {bold('Termux:')}    {'Sim' if 'TERMUX_VERSION' in os.environ else 'Não'}")
    print(f"  {bold('Arquitetura:')} Zero dependências externas (stdlib only)")
    print()


# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(BANNER)
        print(HELP_TEXT)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    # ── run <arquivo>
    if cmd == 'run':
        if len(sys.argv) < 3:
            print(red("❌ Uso: python pyrus.py run <arquivo.pyu>"))
            sys.exit(1)
        path = sys.argv[2]
        t0   = time.time()
        ok   = run_file(path)
        dt   = time.time() - t0
        if ok:
            print(dim(f"\n[Pyrus] Concluído em {dt:.3f}s"))
        sys.exit(0 if ok else 1)

    # ── lex <arquivo>
    elif cmd == 'lex':
        if len(sys.argv) < 3:
            print(red("❌ Uso: python pyrus.py lex <arquivo.pyu>"))
            sys.exit(1)
        path = sys.argv[2]
        if not os.path.exists(path):
            print(red(f"❌ Arquivo não encontrado: '{path}'"))
            sys.exit(1)
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        analisar_tokens(source)

    # ── check <arquivo>
    elif cmd == 'check':
        if len(sys.argv) < 3:
            print(red("❌ Uso: python pyrus.py check <arquivo.pyu>"))
            sys.exit(1)
        ok = check_file(sys.argv[2])
        sys.exit(0 if ok else 1)

    # ── repl
    elif cmd == 'repl':
        start_repl()

    # ── version
    elif cmd in ('version', '--version', '-v'):
        show_version()

    # ── help
    elif cmd in ('help', '--help', '-h'):
        print(BANNER)
        print(HELP_TEXT)

    else:
        print(red(f"❌ Comando desconhecido: '{cmd}'"))
        print(f"   Use {cyan('python pyrus.py help')} para ver os comandos disponíveis.")
        sys.exit(1)


if __name__ == '__main__':
    main()
