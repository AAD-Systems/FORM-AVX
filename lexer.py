#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║     PYRUS LEXER — lexer.py  v0.2.0                  ║
║     Análise léxica independente do interpretador     ║
║     Zero dependências externas                       ║
╚══════════════════════════════════════════════════════╝
"""

from core import tokenize, LexError, VERSION

# Cores ANSI para terminal (funciona em Termux, Linux, macOS)
_C = {
    'reset':   '\033[0m',
    'bold':    '\033[1m',
    'dim':     '\033[2m',
    'red':     '\033[91m',
    'green':   '\033[92m',
    'yellow':  '\033[93m',
    'blue':    '\033[94m',
    'magenta': '\033[95m',
    'cyan':    '\033[96m',
    'white':   '\033[97m',
    'gray':    '\033[90m',
}

# Cada tipo de token tem uma cor associada para leitura visual
TOKEN_COLORS = {
    # Literais
    'INT':    _C['cyan'],
    'FLOAT':  _C['cyan'],
    'STRING': _C['green'],
    'IDENT':  _C['white'],
    # Palavras-chave
    'LET': _C['magenta'], 'FUNC': _C['magenta'], 'RETURN': _C['magenta'],
    'IF':  _C['magenta'], 'ELSE': _C['magenta'],
    'WHILE': _C['magenta'], 'FOR': _C['magenta'], 'IN': _C['magenta'],
    'SPAWN': _C['magenta'], 'IMPORT': _C['magenta'],
    'BREAK': _C['magenta'], 'CONTINUE': _C['magenta'],
    'AND': _C['yellow'], 'OR': _C['yellow'], 'NOT': _C['yellow'],
    'TRUE': _C['cyan'], 'FALSE': _C['cyan'], 'NULL': _C['gray'],
    # Operadores
    'PLUS': _C['yellow'], 'MINUS': _C['yellow'],
    'STAR': _C['yellow'], 'SLASH': _C['yellow'], 'PERCENT': _C['yellow'],
    'POWER': _C['yellow'],
    'EQ': _C['yellow'], 'EQEQ': _C['yellow'], 'NEQ': _C['yellow'],
    'LT': _C['yellow'], 'GT': _C['yellow'],
    'LTE': _C['yellow'], 'GTE': _C['yellow'],
    # Pontuação
    'SEMI': _C['gray'], 'COMMA': _C['gray'], 'DOT': _C['gray'],
    'COLON': _C['gray'],
    'LPAREN': _C['gray'], 'RPAREN': _C['gray'],
    'LBRACE': _C['gray'], 'RBRACE': _C['gray'],
    'LBRACKET': _C['gray'], 'RBRACKET': _C['gray'],
    # EOF
    'EOF': _C['dim'],
}


def analisar_tokens(source: str, colorido: bool = True) -> list:
    """
    Tokeniza o código-fonte Pyrus e exibe a fita de tokens no terminal.
    Retorna a lista de tokens ou [] em caso de erro.
    """
    try:
        tokens = tokenize(source)
    except LexError as e:
        print(f"{_C['red']}❌ Erro Léxico: {e}{_C['reset']}")
        return []

    col_tipo  = 22
    col_valor = 26
    col_pos   = 14

    sep = _C['gray'] + '─' * (col_tipo + col_valor + col_pos + 6) + _C['reset']

    print(f"\n{_C['bold']}🔍 Análise Léxica — Pyrus v{VERSION}{_C['reset']}")
    print(sep)
    print(
        f"{_C['bold']}{'TIPO':<{col_tipo}}{'VALOR':<{col_valor}}{'POSIÇÃO'}{_C['reset']}"
    )
    print(sep)

    for tok in tokens:
        color = TOKEN_COLORS.get(tok.type, _C['white']) if colorido else ''
        reset = _C['reset'] if colorido else ''
        val   = repr(tok.value) if tok.value is not None else '—'
        pos   = f"L{tok.line}:C{tok.col}"
        print(f"{color}{tok.type:<{col_tipo}}{val:<{col_valor}}{pos}{reset}")

    print(sep)
    count = len(tokens) - 1   # exclui EOF da contagem
    print(
        f"{_C['green']}✅ {count} token(s) gerado(s) com sucesso.{_C['reset']}\n"
    )
    return tokens
