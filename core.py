#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║     PYRUS LANGUAGE ENGINE — core.py  v0.2.0         ║
║     "A linguagem da pêra 🍐"                         ║
║     Zero dependências. Python 3.8+                   ║
║     Targets: Termux · Raspberry Pi · ESP32           ║
╚══════════════════════════════════════════════════════╝
"""

import sys
import threading
import time
import math as _math
import os

VERSION  = "0.2.0"
CODENAME = "Pear Seed"


# ══════════════════════════════════════════════════════
# 1. TIPOS DE TOKEN
# ══════════════════════════════════════════════════════

# Literais
TT_INT      = 'INT'
TT_FLOAT    = 'FLOAT'
TT_STRING   = 'STRING'
TT_IDENT    = 'IDENT'

# Aritmética
TT_PLUS     = 'PLUS'
TT_MINUS    = 'MINUS'
TT_STAR     = 'STAR'
TT_SLASH    = 'SLASH'
TT_PERCENT  = 'PERCENT'
TT_POWER    = 'POWER'

# Comparação / Atribuição
TT_EQ       = 'EQ'
TT_EQEQ     = 'EQEQ'
TT_NEQ      = 'NEQ'
TT_LT       = 'LT'
TT_GT       = 'GT'
TT_LTE      = 'LTE'
TT_GTE      = 'GTE'

# Delimitadores
TT_LPAREN   = 'LPAREN'
TT_RPAREN   = 'RPAREN'
TT_LBRACE   = 'LBRACE'
TT_RBRACE   = 'RBRACE'
TT_LBRACKET = 'LBRACKET'
TT_RBRACKET = 'RBRACKET'
TT_SEMI     = 'SEMI'
TT_COMMA    = 'COMMA'
TT_DOT      = 'DOT'
TT_COLON    = 'COLON'
TT_EOF      = 'EOF'

# Palavras-chave (cada uma vira seu próprio tipo)
TT_LET      = 'LET'
TT_FUNC     = 'FUNC'
TT_RETURN   = 'RETURN'
TT_IF       = 'IF'
TT_ELSE     = 'ELSE'
TT_WHILE    = 'WHILE'
TT_FOR      = 'FOR'
TT_IN       = 'IN'
TT_SPAWN    = 'SPAWN'
TT_TRUE     = 'TRUE'
TT_FALSE    = 'FALSE'
TT_NULL     = 'NULL'
TT_AND      = 'AND'
TT_OR       = 'OR'
TT_NOT      = 'NOT'
TT_IMPORT   = 'IMPORT'
TT_BREAK    = 'BREAK'
TT_CONTINUE = 'CONTINUE'

KEYWORDS = {
    'let': TT_LET, 'func': TT_FUNC, 'return': TT_RETURN,
    'if': TT_IF, 'else': TT_ELSE, 'while': TT_WHILE,
    'for': TT_FOR, 'in': TT_IN, 'spawn': TT_SPAWN,
    'true': TT_TRUE, 'false': TT_FALSE, 'null': TT_NULL,
    'and': TT_AND, 'or': TT_OR, 'not': TT_NOT,
    'import': TT_IMPORT, 'break': TT_BREAK, 'continue': TT_CONTINUE,
}


# ══════════════════════════════════════════════════════
# 2. TOKEN E ERROS
# ══════════════════════════════════════════════════════

class Token:
    __slots__ = ('type', 'value', 'line', 'col')

    def __init__(self, type, value, line=0, col=0):
        self.type  = type
        self.value = value
        self.line  = line
        self.col   = col

    def __repr__(self):
        return f'Token({self.type}, {repr(self.value)}, L{self.line}:C{self.col})'


class PyrusError(Exception):
    def __init__(self, msg, line=None):
        self.msg  = msg
        self.line = line
        super().__init__(str(self))

    def __str__(self):
        if self.line:
            return f"Linha {self.line}: {self.msg}"
        return self.msg


class LexError(PyrusError):     pass
class ParseError(PyrusError):   pass
class RuntimeErr(PyrusError):   pass


# Sinais de controle de fluxo (não são erros)
class _BreakSignal(Exception):    pass
class _ContinueSignal(Exception): pass
class _ReturnSignal(Exception):
    def __init__(self, value): self.value = value


# ══════════════════════════════════════════════════════
# 3. TOKENIZADOR (Lexer)
# ══════════════════════════════════════════════════════

def tokenize(source):
    """
    Converte código-fonte Pyrus em uma lista de Tokens.
    Não usa dependências externas.
    """
    tokens = []
    i      = 0
    line   = 1
    col    = 1
    n      = len(source)

    while i < n:
        sc = col          # coluna de início do token atual
        c  = source[i]

        # ── Espaços em branco
        if c in ' \t\r':
            col += 4 if c == '\t' else 1
            i += 1
            continue

        # ── Nova linha
        if c == '\n':
            line += 1
            col   = 1
            i    += 1
            continue

        # ── Comentário de linha: // ...
        if c == '/' and i + 1 < n and source[i + 1] == '/':
            while i < n and source[i] != '\n':
                i += 1
            continue

        # ── String: "..."
        if c == '"':
            i   += 1
            col += 1
            s    = []
            while i < n and source[i] != '"':
                if source[i] == '\n':
                    raise LexError("String não pode conter quebra de linha — feche com '\"'", line)
                if source[i] == '\\' and i + 1 < n:
                    i   += 1
                    col += 1
                    esc  = source[i]
                    s.append({'n': '\n', 't': '\t', 'r': '\r',
                               '"': '"', '\\': '\\'}.get(esc, '\\' + esc))
                else:
                    s.append(source[i])
                i   += 1
                col += 1
            if i >= n:
                raise LexError("String não fechada — falta '\"' no final", line)
            i   += 1     # consome o " de fechamento
            col += 1
            tokens.append(Token(TT_STRING, ''.join(s), line, sc))
            continue

        # ── Número: inteiro ou float
        if c.isdigit():
            num      = []
            is_float = False
            while i < n and (source[i].isdigit() or
                              (source[i] == '.' and not is_float)):
                if source[i] == '.':
                    # próximo char precisa ser dígito, senão é acesso de atributo
                    if i + 1 < n and source[i + 1].isdigit():
                        is_float = True
                    else:
                        break
                num.append(source[i])
                i   += 1
                col += 1
            val = float(''.join(num)) if is_float else int(''.join(num))
            tokens.append(Token(TT_FLOAT if is_float else TT_INT, val, line, sc))
            continue

        # ── Identificador ou palavra-chave
        if c.isalpha() or c == '_':
            ident = []
            while i < n and (source[i].isalnum() or source[i] == '_'):
                ident.append(source[i])
                i   += 1
                col += 1
            word = ''.join(ident)
            tt   = KEYWORDS.get(word, TT_IDENT)
            tokens.append(Token(tt, word, line, sc))
            continue

        # ── Operadores de dois caracteres
        two = source[i:i + 2]
        two_map = {
            '**': TT_POWER, '==': TT_EQEQ, '!=': TT_NEQ,
            '<=': TT_LTE,   '>=': TT_GTE,
        }
        if two in two_map:
            tokens.append(Token(two_map[two], two, line, sc))
            i   += 2
            col += 2
            continue

        # ── Operadores e pontuação de um caractere
        one_map = {
            '+': TT_PLUS,  '-': TT_MINUS,   '*': TT_STAR,
            '/': TT_SLASH, '%': TT_PERCENT, '=': TT_EQ,
            '<': TT_LT,    '>': TT_GT,
            '(': TT_LPAREN,  ')': TT_RPAREN,
            '{': TT_LBRACE,  '}': TT_RBRACE,
            '[': TT_LBRACKET,']': TT_RBRACKET,
            ';': TT_SEMI,  ',': TT_COMMA,
            '.': TT_DOT,   ':': TT_COLON,
        }
        if c in one_map:
            tokens.append(Token(one_map[c], c, line, sc))
            i   += 1
            col += 1
            continue

        raise LexError(f"Caractere inválido: '{c}' (ASCII {ord(c)})", line)

    tokens.append(Token(TT_EOF, None, line, col))
    return tokens


# ══════════════════════════════════════════════════════
# 4. NÓS DA AST (Árvore Sintática Abstrata)
# ══════════════════════════════════════════════════════

class Node: pass

# ── Statements (declarações)
class Program(Node):
    def __init__(self, stmts):              self.stmts = stmts

class Block(Node):
    def __init__(self, stmts):              self.stmts = stmts

class LetStmt(Node):
    def __init__(self, name, expr, line=None):
        self.name = name; self.expr = expr; self.line = line

class AssignStmt(Node):
    def __init__(self, target, expr, line=None):
        self.target = target; self.expr = expr; self.line = line

class FuncStmt(Node):
    def __init__(self, name, params, body, line=None):
        self.name = name; self.params = params
        self.body = body; self.line = line

class ReturnStmt(Node):
    def __init__(self, expr, line=None):
        self.expr = expr; self.line = line

class IfStmt(Node):
    def __init__(self, cond, then, else_, line=None):
        self.cond = cond; self.then = then
        self.else_ = else_; self.line = line

class WhileStmt(Node):
    def __init__(self, cond, body, line=None):
        self.cond = cond; self.body = body; self.line = line

class ForStmt(Node):
    def __init__(self, var, iterable, body, line=None):
        self.var = var; self.iterable = iterable
        self.body = body; self.line = line

class SpawnStmt(Node):
    def __init__(self, expr, line=None):
        self.expr = expr; self.line = line

class ImportStmt(Node):
    def __init__(self, path, line=None):
        self.path = path; self.line = line

class BreakStmt(Node):
    def __init__(self, line=None): self.line = line

class ContinueStmt(Node):
    def __init__(self, line=None): self.line = line

class ExprStmt(Node):
    def __init__(self, expr, line=None):
        self.expr = expr; self.line = line

# ── Expressões
class NumLit(Node):
    def __init__(self, value): self.value = value

class StrLit(Node):
    def __init__(self, value): self.value = value

class BoolLit(Node):
    def __init__(self, value): self.value = value

class NullLit(Node): pass

class ListLit(Node):
    def __init__(self, items): self.items = items

class DictLit(Node):
    def __init__(self, pairs): self.pairs = pairs   # list of (key_node, val_node)

class VarRef(Node):
    def __init__(self, name, line=None):
        self.name = name; self.line = line

class BinOp(Node):
    def __init__(self, op, left, right, line=None):
        self.op = op; self.left = left
        self.right = right; self.line = line

class UnaryOp(Node):
    def __init__(self, op, expr):
        self.op = op; self.expr = expr

class CallExpr(Node):
    def __init__(self, callee, args, line=None):
        self.callee = callee; self.args = args; self.line = line

class IndexExpr(Node):
    def __init__(self, obj, key, line=None):
        self.obj = obj; self.key = key; self.line = line

class AttrExpr(Node):
    def __init__(self, obj, attr, line=None):
        self.obj = obj; self.attr = attr; self.line = line

class FuncExpr(Node):   # função anônima / lambda
    def __init__(self, params, body):
        self.params = params; self.body = body


# ══════════════════════════════════════════════════════
# 5. PARSER (Descendente Recursivo)
# ══════════════════════════════════════════════════════

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    # ── Helpers
    def cur(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def expect(self, tt, msg=None):
        tok = self.cur()
        if tok.type != tt:
            got = repr(tok.value) if tok.value is not None else tok.type
            err = msg or f"Esperado '{tt}', encontrado {got}"
            raise ParseError(err, tok.line)
        return self.advance()

    def match(self, *types):
        if self.cur().type in types:
            return self.advance()
        return None

    # ── Ponto de entrada
    def parse(self):
        stmts = []
        while self.cur().type != TT_EOF:
            stmts.append(self.parse_stmt())
        return Program(stmts)

    # ── Dispatch de statements
    def parse_stmt(self):
        t = self.cur()

        if t.type == TT_LET:      return self.parse_let()
        if t.type == TT_FUNC:     return self.parse_func()
        if t.type == TT_RETURN:   return self.parse_return()
        if t.type == TT_IF:       return self.parse_if()
        if t.type == TT_WHILE:    return self.parse_while()
        if t.type == TT_FOR:      return self.parse_for()
        if t.type == TT_SPAWN:    return self.parse_spawn()
        if t.type == TT_IMPORT:   return self.parse_import()

        if t.type == TT_BREAK:
            self.advance()
            self.expect(TT_SEMI, "Esperado ';' após 'break'")
            return BreakStmt(t.line)

        if t.type == TT_CONTINUE:
            self.advance()
            self.expect(TT_SEMI, "Esperado ';' após 'continue'")
            return ContinueStmt(t.line)

        if t.type == TT_IDENT:
            return self.parse_assign_or_expr()

        return self.parse_expr_stmt()

    def parse_assign_or_expr(self):
        """
        Resolve a ambiguidade entre:
          x = expr;           → AssignStmt
          x.attr = expr;      → AssignStmt em AttrExpr
          x[key] = expr;      → AssignStmt em IndexExpr
          func_call(args);    → ExprStmt
        """
        line = self.cur().line
        expr = self.parse_expr()

        if self.cur().type == TT_EQ:
            self.advance()
            rhs = self.parse_expr()
            self.expect(TT_SEMI, "Esperado ';' após atribuição")
            return AssignStmt(expr, rhs, line)

        self.expect(TT_SEMI, f"Esperado ';' no final da expressão (linha {line})")
        return ExprStmt(expr, line)

    def parse_expr_stmt(self):
        line = self.cur().line
        expr = self.parse_expr()
        self.expect(TT_SEMI, "Esperado ';' no final da expressão")
        return ExprStmt(expr, line)

    # ── Statements específicos
    def parse_let(self):
        line = self.cur().line
        self.advance()
        name = self.expect(TT_IDENT, "Esperado nome da variável após 'let'").value
        self.expect(TT_EQ, "Esperado '=' após o nome da variável")
        expr = self.parse_expr()
        self.expect(TT_SEMI, "Esperado ';' após declaração 'let'")
        return LetStmt(name, expr, line)

    def parse_func(self):
        line = self.cur().line
        self.advance()
        name = self.expect(TT_IDENT, "Esperado nome da função").value
        self.expect(TT_LPAREN, "Esperado '(' após o nome da função")
        params = self._parse_params()
        self.expect(TT_RPAREN, "Esperado ')' após parâmetros")
        body = self.parse_block()
        return FuncStmt(name, params, body, line)

    def _parse_params(self):
        params = []
        if self.cur().type != TT_RPAREN:
            params.append(self.expect(TT_IDENT, "Esperado nome de parâmetro").value)
            while self.match(TT_COMMA):
                params.append(self.expect(TT_IDENT, "Esperado nome de parâmetro").value)
        return params

    def parse_return(self):
        line = self.cur().line
        self.advance()
        if self.cur().type == TT_SEMI:
            self.advance()
            return ReturnStmt(NullLit(), line)
        expr = self.parse_expr()
        self.expect(TT_SEMI, "Esperado ';' após 'return'")
        return ReturnStmt(expr, line)

    def parse_if(self):
        line = self.cur().line
        self.advance()
        cond = self.parse_expr()
        then = self.parse_block()
        else_ = None
        if self.cur().type == TT_ELSE:
            self.advance()
            if self.cur().type == TT_IF:
                else_ = self.parse_if()       # cadeia else if
            else:
                else_ = self.parse_block()
        return IfStmt(cond, then, else_, line)

    def parse_while(self):
        line = self.cur().line
        self.advance()
        cond = self.parse_expr()
        body = self.parse_block()
        return WhileStmt(cond, body, line)

    def parse_for(self):
        line = self.cur().line
        self.advance()
        var = self.expect(TT_IDENT, "Esperado variável após 'for'").value
        self.expect(TT_IN, "Esperado 'in' após a variável do 'for'")
        iterable = self.parse_expr()
        body     = self.parse_block()
        return ForStmt(var, iterable, body, line)

    def parse_spawn(self):
        line = self.cur().line
        self.advance()
        expr = self.parse_expr()
        self.expect(TT_SEMI, "Esperado ';' após 'spawn'")
        return SpawnStmt(expr, line)

    def parse_import(self):
        line = self.cur().line
        self.advance()
        path = self.expect(TT_STRING,
                           "Esperado caminho do arquivo (string) após 'import'").value
        self.expect(TT_SEMI, "Esperado ';' após 'import'")
        return ImportStmt(path, line)

    def parse_block(self):
        self.expect(TT_LBRACE, "Esperado '{' para iniciar bloco")
        stmts = []
        while self.cur().type not in (TT_RBRACE, TT_EOF):
            stmts.append(self.parse_stmt())
        self.expect(TT_RBRACE, "Esperado '}' para fechar bloco")
        return Block(stmts)

    # ── Expressões (escalonamento de precedência)

    def parse_expr(self):   return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.cur().type == TT_OR:
            op = self.advance()
            left = BinOp('or', left, self.parse_and(), op.line)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.cur().type == TT_AND:
            op = self.advance()
            left = BinOp('and', left, self.parse_not(), op.line)
        return left

    def parse_not(self):
        if self.cur().type == TT_NOT:
            self.advance()
            return UnaryOp('not', self.parse_not())
        return self.parse_cmp()

    def parse_cmp(self):
        left = self.parse_add()
        _map = {TT_EQEQ: '==', TT_NEQ: '!=',
                TT_LT: '<',    TT_GT: '>',
                TT_LTE: '<=',  TT_GTE: '>='}
        while self.cur().type in _map:
            op = self.advance()
            left = BinOp(_map[op.type], left, self.parse_add(), op.line)
        return left

    def parse_add(self):
        left = self.parse_mul()
        while self.cur().type in (TT_PLUS, TT_MINUS):
            op = self.advance()
            left = BinOp(op.value, left, self.parse_mul(), op.line)
        return left

    def parse_mul(self):
        left = self.parse_power()
        while self.cur().type in (TT_STAR, TT_SLASH, TT_PERCENT):
            op = self.advance()
            left = BinOp(op.value, left, self.parse_power(), op.line)
        return left

    def parse_power(self):
        base = self.parse_unary()
        if self.cur().type == TT_POWER:
            op  = self.advance()
            exp = self.parse_power()    # direita-associativo
            return BinOp('**', base, exp, op.line)
        return base

    def parse_unary(self):
        if self.cur().type == TT_MINUS:
            self.advance()
            return UnaryOp('-', self.parse_unary())
        if self.cur().type == TT_NOT:
            self.advance()
            return UnaryOp('not', self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        """Handles: obj.attr  obj[key]  obj(args)  — encadeados."""
        node = self.parse_primary()
        while True:
            t = self.cur()
            if t.type == TT_DOT:
                self.advance()
                attr = self.expect(TT_IDENT, "Esperado nome de atributo após '.'")
                node = AttrExpr(node, attr.value, t.line)

            elif t.type == TT_LBRACKET:
                self.advance()
                key = self.parse_expr()
                self.expect(TT_RBRACKET, "Esperado ']' após índice")
                node = IndexExpr(node, key, t.line)

            elif t.type == TT_LPAREN:
                self.advance()
                args = []
                if self.cur().type != TT_RPAREN:
                    args.append(self.parse_expr())
                    while self.match(TT_COMMA):
                        if self.cur().type == TT_RPAREN:
                            break
                        args.append(self.parse_expr())
                self.expect(TT_RPAREN, "Esperado ')' após argumentos")
                node = CallExpr(node, args, t.line)
            else:
                break
        return node

    def parse_primary(self):
        t = self.cur()

        if t.type == TT_INT:     self.advance(); return NumLit(t.value)
        if t.type == TT_FLOAT:   self.advance(); return NumLit(t.value)
        if t.type == TT_STRING:  self.advance(); return StrLit(t.value)
        if t.type == TT_TRUE:    self.advance(); return BoolLit(True)
        if t.type == TT_FALSE:   self.advance(); return BoolLit(False)
        if t.type == TT_NULL:    self.advance(); return NullLit()
        if t.type == TT_IDENT:   self.advance(); return VarRef(t.value, t.line)

        # Expressão agrupada: (expr)
        if t.type == TT_LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TT_RPAREN, "Esperado ')' para fechar expressão")
            return expr

        # Lista: [expr, ...]
        if t.type == TT_LBRACKET:
            self.advance()
            items = []
            if self.cur().type != TT_RBRACKET:
                items.append(self.parse_expr())
                while self.match(TT_COMMA):
                    if self.cur().type == TT_RBRACKET:
                        break
                    items.append(self.parse_expr())
            self.expect(TT_RBRACKET, "Esperado ']' para fechar lista")
            return ListLit(items)

        # Dicionário: {"chave": valor, ...}
        if t.type == TT_LBRACE:
            return self._parse_dict()

        # Função anônima: func(params) { body }
        if t.type == TT_FUNC:
            self.advance()
            self.expect(TT_LPAREN, "Esperado '(' após 'func'")
            params = self._parse_params()
            self.expect(TT_RPAREN, "Esperado ')'")
            body = self.parse_block()
            return FuncExpr(params, body)

        raise ParseError(
            f"Expressão inesperada: '{t.value or t.type}' — verifique a sintaxe",
            t.line)

    def _parse_dict(self):
        line = self.cur().line
        self.expect(TT_LBRACE)
        pairs = []
        while self.cur().type != TT_RBRACE:
            if self.cur().type == TT_EOF:
                raise ParseError("Dicionário não fechado — falta '}'", line)
            k = self.parse_expr()
            self.expect(TT_COLON, "Esperado ':' após chave do dicionário")
            v = self.parse_expr()
            pairs.append((k, v))
            if self.cur().type != TT_RBRACE:
                self.expect(TT_COMMA, "Esperado ',' ou '}' no dicionário")
        self.expect(TT_RBRACE, "Esperado '}' para fechar dicionário")
        return DictLit(pairs)


# ══════════════════════════════════════════════════════
# 6. AMBIENTE (Escopos Léxicos)
# ══════════════════════════════════════════════════════

class Environment:
    def __init__(self, parent=None):
        self.vars   = {}
        self.parent = parent

    def get(self, name, line=None):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name, line)
        raise RuntimeErr(
            f"Variável '{name}' não foi declarada. "
            f"Use 'let {name} = ...' para declará-la.", line)

    def set(self, name, value):
        """Declara no escopo atual (sombreamento permitido)."""
        self.vars[name] = value

    def assign(self, name, value, line=None):
        """Reatribui uma variável existente, subindo na cadeia de escopos."""
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent:
            self.parent.assign(name, value, line)
            return
        raise RuntimeErr(
            f"Variável '{name}' não declarada — use 'let {name} = ...' antes de atribuir.",
            line)


# ══════════════════════════════════════════════════════
# 7. OBJETOS EM TEMPO DE EXECUÇÃO
# ══════════════════════════════════════════════════════

class PyrusFunction:
    def __init__(self, name, params, body, closure):
        self.name    = name
        self.params  = params
        self.body    = body
        self.closure = closure

    def __repr__(self):
        return f"<func {self.name or 'anonima'}({', '.join(self.params)})>"


class PyrusBuiltin:
    def __init__(self, name, fn):
        self.name = name
        self.fn   = fn

    def __repr__(self):
        return f"<builtin {self.name}>"


class PyrusModule:
    def __init__(self, name):
        self.name  = name
        self._attrs = {}

    def set(self, k, v):
        self._attrs[k] = v

    def get(self, k, line=None):
        if k in self._attrs:
            return self._attrs[k]
        raise RuntimeErr(f"Módulo '{self.name}' não possui '{k}'", line)

    def __repr__(self):
        return f"<module {self.name}>"


# ══════════════════════════════════════════════════════
# 8. MÓDULOS DE HARDWARE EMBUTIDOS
# ══════════════════════════════════════════════════════

def _make_gpio():
    """
    Módulo GPIO — controle de pinos digitais e analógicos.
    Em hardware real (ESP32/RPi), substitua as funções por
    chamadas à biblioteca nativa (machine.Pin, RPi.GPIO, etc).
    """
    m     = PyrusModule('gpio')
    _pins = {}

    def setup(pin, mode):
        _pins[int(pin)] = {'mode': str(mode).lower(), 'value': 0}
        print(f"[GPIO] Pino {int(pin)} → modo '{mode}'")
        return None

    def write(pin, val):
        p = int(pin)
        if p not in _pins:
            _pins[p] = {'mode': 'out', 'value': 0}
        _pins[p]['value'] = int(val)
        state = "HIGH" if int(val) else "LOW"
        print(f"[GPIO] Pino {p} = {state} ({int(val)})")
        return None

    def read(pin):
        p = int(pin)
        return _pins[p]['value'] if p in _pins else 0

    def pwm(pin, frequency, duty):
        print(f"[GPIO] PWM Pino {int(pin)} | {frequency}Hz | duty={duty}%")
        return None

    def analog_read(pin):
        import random
        val = round(random.uniform(0.0, 3.3), 4)
        print(f"[GPIO] ADC Pino {int(pin)} → {val}V")
        return val

    def digital_toggle(pin):
        p = int(pin)
        cur = _pins.get(p, {}).get('value', 0)
        write(p, 1 - cur)
        return None

    for name, fn in [
        ('setup', setup), ('write', write), ('read', read),
        ('pwm', pwm), ('analog_read', analog_read),
        ('toggle', digital_toggle),
    ]:
        m.set(name, PyrusBuiltin(name, fn))
    return m


def _make_serial():
    """Módulo Serial — UART / RS232."""
    m = PyrusModule('serial')

    def begin(baud=9600):
        print(f"[Serial] Iniciado @ {int(baud)} baud")
        return None

    def write(data):
        print(f"[Serial] TX ► {_pyu_str(data)}")
        return None

    def writeln(data):
        print(f"[Serial] TX ► {_pyu_str(data)}\\n")
        return None

    def read():
        return input("[Serial] RX ◄ ")

    def available():
        return 0

    def flush():
        return None

    for name, fn in [
        ('begin', begin), ('write', write), ('writeln', writeln),
        ('read', read), ('available', available), ('flush', flush),
    ]:
        m.set(name, PyrusBuiltin(name, fn))
    return m


def _make_udp():
    """Módulo UDP — comunicação de rede."""
    m = PyrusModule('udp')

    def send(host, port, data):
        print(f"[UDP] → {host}:{int(port)}  \"{_pyu_str(data)}\"")
        return None

    def broadcast(port, data):
        print(f"[UDP] BROADCAST :{int(port)}  \"{_pyu_str(data)}\"")
        return None

    def listen(port):
        print(f"[UDP] Escutando na porta {int(port)}")
        return None

    def recv():
        return input("[UDP] Recv ◄ ")

    for name, fn in [
        ('send', send), ('broadcast', broadcast),
        ('listen', listen), ('recv', recv),
    ]:
        m.set(name, PyrusBuiltin(name, fn))
    return m


def _make_http():
    """Módulo HTTP — requisições web básicas."""
    m = PyrusModule('http')

    def get(url):
        print(f"[HTTP] GET {url}")
        return '{"status":"ok","data":null}'

    def post(url, body="{}"):
        print(f"[HTTP] POST {url}  body={_pyu_str(body)}")
        return '{"status":"ok"}'

    def status():
        return 200

    for name, fn in [('get', get), ('post', post), ('status', status)]:
        m.set(name, PyrusBuiltin(name, fn))
    return m


def _make_math_module():
    """Módulo Math — funções matemáticas."""
    m = PyrusModule('math')

    # Constantes
    m.set('pi', _math.pi)
    m.set('e',  _math.e)
    m.set('tau', _math.tau)
    m.set('inf', float('inf'))

    # Funções
    fns = {
        'sqrt':    _math.sqrt,
        'sin':     _math.sin,
        'cos':     _math.cos,
        'tan':     _math.tan,
        'asin':    _math.asin,
        'acos':    _math.acos,
        'atan':    _math.atan,
        'atan2':   _math.atan2,
        'log':     _math.log,
        'log2':    _math.log2,
        'log10':   _math.log10,
        'floor':   lambda x: int(_math.floor(x)),
        'ceil':    lambda x: int(_math.ceil(x)),
        'abs':     abs,
        'pow':     lambda x, y: x ** y,
        'round':   round,
        'radians': _math.radians,
        'degrees': _math.degrees,
        'hypot':   _math.hypot,
        'clamp':   lambda x, mn, mx: max(mn, min(mx, x)),
        'lerp':    lambda a, b, t: a + (b - a) * t,
        'map_range': lambda x, a1, a2, b1, b2: b1 + (x - a1) * (b2 - b1) / (a2 - a1),
    }
    for name, fn in fns.items():
        m.set(name, PyrusBuiltin(name, fn))
    return m


# ══════════════════════════════════════════════════════
# 9. FUNÇÕES AUXILIARES
# ══════════════════════════════════════════════════════

def _pyu_str(v):
    """Converte qualquer valor Pyrus para string legível."""
    if v is None:             return "null"
    if isinstance(v, bool):   return "true" if v else "false"
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e15:
            return f"{int(v)}.0"
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_pyu_str(i) for i in v) + "]"
    if isinstance(v, dict):
        pairs = ", ".join(f'"{k}": {_pyu_str(val)}' for k, val in v.items())
        return "{" + pairs + "}"
    return str(v)


def _pyu_truthy(v):
    """Retorna True se o valor é considerado verdadeiro em Pyrus."""
    if v is None:             return False
    if isinstance(v, bool):   return v
    if isinstance(v, (int, float)): return v != 0
    if isinstance(v, str):    return len(v) > 0
    if isinstance(v, (list, dict)): return len(v) > 0
    return True


def _type_name(v):
    """Retorna o nome do tipo Pyrus de um valor."""
    if v is None:                  return "null"
    if isinstance(v, bool):        return "bool"
    if isinstance(v, int):         return "int"
    if isinstance(v, float):       return "float"
    if isinstance(v, str):         return "string"
    if isinstance(v, list):        return "list"
    if isinstance(v, dict):        return "dict"
    if isinstance(v, PyrusFunction):  return "func"
    if isinstance(v, PyrusBuiltin):   return "builtin"
    if isinstance(v, PyrusModule):    return "module"
    return "unknown"


# ══════════════════════════════════════════════════════
# 10. INTERPRETADOR (Tree-Walker)
# ══════════════════════════════════════════════════════

class Interpreter:
    def __init__(self, source_path=None):
        self.source_path = source_path
        self.globals     = self._make_globals()

    # ── Cria o ambiente global com todos os builtins
    def _make_globals(self):
        env = Environment()

        def B(name, fn):
            env.set(name, PyrusBuiltin(name, fn))

        # ── I/O
        def _print(*args):
            print(' '.join(_pyu_str(a) for a in args))
            return None

        def _println(*args):
            print(' '.join(_pyu_str(a) for a in args))
            return None

        def _input(prompt=''):
            return input(_pyu_str(prompt))

        def _eprint(*args):
            print(' '.join(_pyu_str(a) for a in args), file=sys.stderr)
            return None

        # ── Conversão de tipos
        def _int(x):
            if isinstance(x, bool): return 1 if x else 0
            try: return int(x)
            except: raise RuntimeErr(f"Não é possível converter '{_pyu_str(x)}' para int")

        def _float(x):
            try: return float(x)
            except: raise RuntimeErr(f"Não é possível converter '{_pyu_str(x)}' para float")

        def _str(x): return _pyu_str(x)
        def _bool(x): return _pyu_truthy(x)
        def _type(x): return _type_name(x)

        # ── Operações de sequência
        def _len(x):
            if isinstance(x, (str, list, dict)): return len(x)
            raise RuntimeErr(f"len() não suporta '{_type_name(x)}'")

        def _range(*args):
            a = [int(x) for x in args]
            if len(a) == 1: return list(range(a[0]))
            if len(a) == 2: return list(range(a[0], a[1]))
            if len(a) == 3: return list(range(a[0], a[1], a[2]))
            raise RuntimeErr("range() aceita 1, 2 ou 3 argumentos")

        def _append(lst, item):
            if not isinstance(lst, list): raise RuntimeErr("append() requer lista")
            lst.append(item); return None

        def _push(lst, item):
            if not isinstance(lst, list): raise RuntimeErr("push() requer lista")
            lst.append(item); return None

        def _pop(lst):
            if not isinstance(lst, list) or not lst:
                raise RuntimeErr("pop() requer lista não vazia")
            return lst.pop()

        def _keys(d):
            if not isinstance(d, dict): raise RuntimeErr("keys() requer dict")
            return list(d.keys())

        def _values(d):
            if not isinstance(d, dict): raise RuntimeErr("values() requer dict")
            return list(d.values())

        def _has(obj, key):
            if isinstance(obj, (dict, list, str)): return key in obj
            raise RuntimeErr("has() requer lista, dict ou string")

        def _join(lst, sep=''):
            if not isinstance(lst, list): raise RuntimeErr("join() requer lista")
            return str(sep).join(_pyu_str(x) for x in lst)

        def _split(s, sep=' '):
            return str(s).split(str(sep))

        def _sort(lst):
            if not isinstance(lst, list): raise RuntimeErr("sort() requer lista")
            lst.sort(); return None

        def _reverse(lst):
            if not isinstance(lst, list): raise RuntimeErr("reverse() requer lista")
            lst.reverse(); return None

        def _slice(lst, start, end=None):
            if not isinstance(lst, (list, str)):
                raise RuntimeErr("slice() requer lista ou string")
            return lst[int(start):] if end is None else lst[int(start):int(end)]

        # ── Math atalhos globais
        def _sqrt(x):  return _math.sqrt(float(x))
        def _abs(x):   return abs(x)
        def _floor(x): return int(_math.floor(float(x)))
        def _ceil(x):  return int(_math.ceil(float(x)))
        def _round(x, n=0): return round(float(x), int(n))
        def _pow(x, y): return x ** y

        def _max(*args):
            if len(args) == 1 and isinstance(args[0], list): return max(args[0])
            return max(args)

        def _min(*args):
            if len(args) == 1 and isinstance(args[0], list): return min(args[0])
            return min(args)

        # ── String helpers globais
        def _upper(s): return str(s).upper()
        def _lower(s): return str(s).lower()
        def _trim(s):  return str(s).strip()

        def _replace(s, old, new):
            return str(s).replace(str(old), str(new))

        def _contains(s, sub):
            return str(sub) in str(s)

        def _format(template, *args):
            result = str(template)
            for arg in args:
                result = result.replace('{}', _pyu_str(arg), 1)
            return result

        # ── Sistema
        def _sleep(s):  time.sleep(float(s)); return None
        def _clock():   return time.time()
        def _millis():  return int(time.time() * 1000)
        def _exit(code=0): sys.exit(int(code))

        def _assert(cond, msg="Assertion failed"):
            if not _pyu_truthy(cond):
                raise RuntimeErr(f"assert falhou: {_pyu_str(msg)}")
            return None

        def _panic(msg="panic!"):
            raise RuntimeErr(f"PANIC: {_pyu_str(msg)}")

        # ── Registra todos os builtins
        builtins = {
            # I/O
            'print': _print, 'println': _println,
            'input': _input, 'eprint': _eprint,
            # Tipos
            'int': _int, 'float': _float, 'str': _str,
            'bool': _bool, 'type': _type,
            # Sequências
            'len': _len, 'range': _range,
            'append': _append, 'push': _push, 'pop': _pop,
            'keys': _keys, 'values': _values, 'has': _has,
            'join': _join, 'split': _split,
            'sort': _sort, 'reverse': _reverse, 'slice': _slice,
            # Math
            'sqrt': _sqrt, 'abs': _abs, 'floor': _floor,
            'ceil': _ceil, 'round': _round, 'pow': _pow,
            'max': _max, 'min': _min,
            # Strings
            'upper': _upper, 'lower': _lower, 'trim': _trim,
            'replace': _replace, 'contains': _contains,
            'format': _format,
            # Sistema
            'sleep': _sleep, 'clock': _clock,
            'millis': _millis, 'exit': _exit,
            'assert': _assert, 'panic': _panic,
        }
        for name, fn in builtins.items():
            B(name, fn)

        # ── Módulos de hardware
        env.set('gpio',   _make_gpio())
        env.set('serial', _make_serial())
        env.set('udp',    _make_udp())
        env.set('http',   _make_http())
        env.set('math',   _make_math_module())

        return env

    # ── Executa um nó statement
    def execute(self, node, env):
        if isinstance(node, Program):
            for stmt in node.stmts:
                self.execute(stmt, env)

        elif isinstance(node, Block):
            local = Environment(env)
            for stmt in node.stmts:
                self.execute(stmt, local)

        elif isinstance(node, LetStmt):
            value = self.eval_expr(node.expr, env)
            env.set(node.name, value)

        elif isinstance(node, AssignStmt):
            value  = self.eval_expr(node.expr, env)
            target = node.target

            if isinstance(target, VarRef):
                env.assign(target.name, value, node.line)

            elif isinstance(target, IndexExpr):
                obj = self.eval_expr(target.obj, env)
                key = self.eval_expr(target.key, env)
                if isinstance(obj, list):
                    idx = int(key)
                    if not (-len(obj) <= idx < len(obj)):
                        raise RuntimeErr(
                            f"Índice {idx} fora do range (tamanho {len(obj)})",
                            node.line)
                    obj[idx] = value
                elif isinstance(obj, dict):
                    obj[key] = value
                else:
                    raise RuntimeErr(
                        f"Tipo '{_type_name(obj)}' não suporta atribuição por índice",
                        node.line)

            elif isinstance(target, AttrExpr):
                obj = self.eval_expr(target.obj, env)
                if isinstance(obj, PyrusModule):
                    obj.set(target.attr, value)
                elif isinstance(obj, dict):
                    obj[target.attr] = value
                else:
                    raise RuntimeErr(
                        f"Não é possível atribuir atributo em '{_type_name(obj)}'",
                        node.line)
            else:
                raise RuntimeErr("Alvo de atribuição inválido", node.line)

        elif isinstance(node, FuncStmt):
            fn = PyrusFunction(node.name, node.params, node.body, env)
            env.set(node.name, fn)

        elif isinstance(node, ReturnStmt):
            raise _ReturnSignal(self.eval_expr(node.expr, env))

        elif isinstance(node, IfStmt):
            cond = self.eval_expr(node.cond, env)
            if _pyu_truthy(cond):
                self.execute(node.then, env)
            elif node.else_ is not None:
                self.execute(node.else_, env)

        elif isinstance(node, WhileStmt):
            while _pyu_truthy(self.eval_expr(node.cond, env)):
                try:
                    self.execute(node.body, env)
                except _BreakSignal:
                    break
                except _ContinueSignal:
                    continue

        elif isinstance(node, ForStmt):
            iterable = self.eval_expr(node.iterable, env)
            if not isinstance(iterable, (list, str)):
                raise RuntimeErr(
                    f"'for' requer lista ou string, não '{_type_name(iterable)}'",
                    node.line)
            for item in iterable:
                loop_env = Environment(env)
                loop_env.set(node.var, item)
                try:
                    self.execute(node.body, loop_env)
                except _BreakSignal:
                    break
                except _ContinueSignal:
                    continue

        elif isinstance(node, SpawnStmt):
            expr = node.expr
            def _thread_fn():
                try:
                    self.eval_expr(expr, env)
                except Exception as e:
                    print(f"[spawn] Erro em thread: {e}", file=sys.stderr)
            t = threading.Thread(target=_thread_fn, daemon=True)
            t.start()

        elif isinstance(node, ImportStmt):
            path = node.path
            if not os.path.isabs(path) and self.source_path:
                path = os.path.join(os.path.dirname(self.source_path), path)
            if not os.path.exists(path):
                raise RuntimeErr(f"Arquivo não encontrado: '{path}'", node.line)
            with open(path, 'r', encoding='utf-8') as f:
                src = f.read()
            # Compartilha o ambiente global (importação flat)
            run_code(src, source_path=path, env=self.globals)

        elif isinstance(node, BreakStmt):
            raise _BreakSignal()

        elif isinstance(node, ContinueStmt):
            raise _ContinueSignal()

        elif isinstance(node, ExprStmt):
            self.eval_expr(node.expr, env)

        elif isinstance(node, IfStmt):
            pass    # já tratado acima

        else:
            raise RuntimeErr(f"Nó AST desconhecido: {type(node).__name__}")

    # ── Avalia uma expressão e retorna o valor
    def eval_expr(self, node, env):
        if isinstance(node, NumLit):  return node.value
        if isinstance(node, StrLit):  return node.value
        if isinstance(node, BoolLit): return node.value
        if isinstance(node, NullLit): return None

        if isinstance(node, ListLit):
            return [self.eval_expr(item, env) for item in node.items]

        if isinstance(node, DictLit):
            d = {}
            for k_node, v_node in node.pairs:
                k = self.eval_expr(k_node, env)
                v = self.eval_expr(v_node, env)
                d[k] = v
            return d

        if isinstance(node, VarRef):
            return env.get(node.name, node.line)

        if isinstance(node, BinOp):
            return self._eval_binop(node, env)

        if isinstance(node, UnaryOp):
            val = self.eval_expr(node.expr, env)
            if node.op == '-':
                if isinstance(val, (int, float)): return -val
                raise RuntimeErr(f"Operador '-' não se aplica a '{_type_name(val)}'")
            if node.op == 'not':
                return not _pyu_truthy(val)
            raise RuntimeErr(f"Operador unário desconhecido: '{node.op}'")

        if isinstance(node, CallExpr):
            return self._eval_call(node, env)

        if isinstance(node, IndexExpr):
            return self._eval_index(node, env)

        if isinstance(node, AttrExpr):
            obj = self.eval_expr(node.obj, env)
            return self._get_attr(obj, node.attr, node.line)

        if isinstance(node, FuncExpr):
            return PyrusFunction(None, node.params, node.body, env)

        raise RuntimeErr(f"Expressão desconhecida: {type(node).__name__}")

    def _eval_index(self, node, env):
        obj = self.eval_expr(node.obj, env)
        key = self.eval_expr(node.key, env)
        if isinstance(obj, list):
            idx = int(key)
            if not (-len(obj) <= idx < len(obj)):
                raise RuntimeErr(
                    f"Índice {idx} fora do range (lista tem {len(obj)} elementos)",
                    node.line)
            return obj[idx]
        if isinstance(obj, dict):
            if key not in obj:
                raise RuntimeErr(
                    f"Chave '{_pyu_str(key)}' não encontrada no dicionário",
                    node.line)
            return obj[key]
        if isinstance(obj, str):
            idx = int(key)
            if not (-len(obj) <= idx < len(obj)):
                raise RuntimeErr(f"Índice {idx} fora do range da string", node.line)
            return obj[idx]
        raise RuntimeErr(
            f"Tipo '{_type_name(obj)}' não suporta indexação por '[]'", node.line)

    def _get_attr(self, obj, attr, line=None):
        """
        Resolve acesso a atributos/métodos em módulos, strings, listas e dicts.
        """
        # Módulo Pyrus
        if isinstance(obj, PyrusModule):
            return obj.get(attr, line)

        # Métodos de String
        if isinstance(obj, str):
            smap = {
                'len':         lambda: len(obj),
                'upper':       lambda: obj.upper(),
                'lower':       lambda: obj.lower(),
                'trim':        lambda: obj.strip(),
                'split':       lambda sep=' ': obj.split(str(sep)),
                'replace':     lambda old, new: obj.replace(str(old), str(new)),
                'contains':    lambda sub: str(sub) in obj,
                'starts_with': lambda pre: obj.startswith(str(pre)),
                'ends_with':   lambda suf: obj.endswith(str(suf)),
                'to_int':      lambda: int(obj),
                'to_float':    lambda: float(obj),
                'repeat':      lambda n: obj * int(n),
            }
            if attr in smap:
                return PyrusBuiltin(attr, smap[attr])
            raise RuntimeErr(f"String não possui método '{attr}'", line)

        # Métodos de Lista
        if isinstance(obj, list):
            lmap = {
                'len':     lambda: len(obj),
                'push':    lambda item: (obj.append(item), None)[1],
                'append':  lambda item: (obj.append(item), None)[1],
                'pop':     lambda: obj.pop(),
                'insert':  lambda idx, item: (obj.insert(int(idx), item), None)[1],
                'remove':  lambda item: (obj.remove(item) if item in obj else None),
                'has':     lambda item: item in obj,
                'join':    lambda sep='': sep.join(_pyu_str(x) for x in obj),
                'sort':    lambda: (obj.sort(), None)[1],
                'reverse': lambda: (obj.reverse(), None)[1],
                'slice':   lambda s, e=None: obj[int(s):] if e is None else obj[int(s):int(e)],
                'index':   lambda item: obj.index(item) if item in obj else -1,
                'copy':    lambda: list(obj),
                'clear':   lambda: (obj.clear(), None)[1],
                'first':   lambda: obj[0] if obj else None,
                'last':    lambda: obj[-1] if obj else None,
                'sum':     lambda: sum(obj),
                'count':   lambda item: obj.count(item),
            }
            if attr in lmap:
                return PyrusBuiltin(attr, lmap[attr])
            raise RuntimeErr(f"Lista não possui método '{attr}'", line)

        # Métodos de Dicionário
        if isinstance(obj, dict):
            dmap = {
                'len':    lambda: len(obj),
                'keys':   lambda: list(obj.keys()),
                'values': lambda: list(obj.values()),
                'has':    lambda key: key in obj,
                'get':    lambda key, default=None: obj.get(key, default),
                'set':    lambda key, val: (obj.update({key: val}), None)[1],
                'remove': lambda key: obj.pop(key, None),
                'clear':  lambda: (obj.clear(), None)[1],
                'copy':   lambda: dict(obj),
            }
            if attr in dmap:
                return PyrusBuiltin(attr, dmap[attr])
            if attr in obj:
                return obj[attr]
            raise RuntimeErr(f"Dicionário não possui '{attr}'", line)

        raise RuntimeErr(
            f"Tipo '{_type_name(obj)}' não possui atributos", line)

    def _eval_call(self, node, env):
        func = self.eval_expr(node.callee, env)
        args = [self.eval_expr(a, env) for a in node.args]
        return self._call_func(func, args, node.line)

    def _call_func(self, func, args, line=None):
        if hasattr(func, "fn") and callable(getattr(func, "fn", None)):
            try:
                return func.fn(*args)
            except RuntimeErr:
                raise
            except TypeError as e:
                raise RuntimeErr(
                    f"Chamada inválida para '{func.name}': "
                    f"argumentos errados ({e})", line)
            except Exception as e:
                raise RuntimeErr(f"Erro em '{func.name}': {e}", line)

        if isinstance(func, PyrusFunction):
            if len(args) != len(func.params):
                raise RuntimeErr(
                    f"Função '{func.name or 'anonima'}' esperava "
                    f"{len(func.params)} argumento(s), recebeu {len(args)}",
                    line)
            call_env = Environment(func.closure)
            for param, arg in zip(func.params, args):
                call_env.set(param, arg)
            try:
                self.execute(func.body, call_env)
                return None
            except _ReturnSignal as ret:
                return ret.value

        raise RuntimeErr(
            f"'{_pyu_str(func)}' não é uma função chamável "
            f"(tipo: {_type_name(func)})", line)

    def _eval_binop(self, node, env):
        op = node.op

        # Curto-circuito para operadores booleanos
        if op == 'and':
            left = self.eval_expr(node.left, env)
            return left if not _pyu_truthy(left) else self.eval_expr(node.right, env)
        if op == 'or':
            left = self.eval_expr(node.left, env)
            return left if _pyu_truthy(left) else self.eval_expr(node.right, env)

        left  = self.eval_expr(node.left, env)
        right = self.eval_expr(node.right, env)
        ln    = node.line

        if op == '+':
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            # Concatenação de strings (coerção automática)
            if isinstance(left, str) or isinstance(right, str):
                return _pyu_str(left) + _pyu_str(right)
            # Concatenação de listas
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            raise RuntimeErr(
                f"Operador '+' não suporta '{_type_name(left)}' + '{_type_name(right)}'", ln)

        if op == '-':
            self._require_nums('-', left, right, ln)
            return left - right

        if op == '*':
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left * right
            if isinstance(left, str) and isinstance(right, int):
                return left * right
            if isinstance(left, list) and isinstance(right, int):
                return left * right
            raise RuntimeErr(
                f"Operador '*' não suporta '{_type_name(left)}' * '{_type_name(right)}'", ln)

        if op == '/':
            self._require_nums('/', left, right, ln)
            if right == 0:
                raise RuntimeErr("Divisão por zero", ln)
            r = left / right
            if isinstance(left, int) and isinstance(right, int) and r == int(r):
                return int(r)
            return r

        if op == '%':
            self._require_nums('%', left, right, ln)
            if right == 0:
                raise RuntimeErr("Módulo por zero", ln)
            return left % right

        if op == '**':
            self._require_nums('**', left, right, ln)
            return left ** right

        if op == '==': return left == right
        if op == '!=': return left != right

        if op in ('<', '>', '<=', '>='):
            self._require_ord(op, left, right, ln)
            if op == '<':  return left < right
            if op == '>':  return left > right
            if op == '<=': return left <= right
            if op == '>=': return left >= right

        raise RuntimeErr(f"Operador '{op}' desconhecido", ln)

    def _require_nums(self, op, a, b, line):
        if not isinstance(a, (int, float)):
            raise RuntimeErr(
                f"Operador '{op}' requer número, não '{_type_name(a)}'", line)
        if not isinstance(b, (int, float)):
            raise RuntimeErr(
                f"Operador '{op}' requer número, não '{_type_name(b)}'", line)

    def _require_ord(self, op, a, b, line):
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))) and \
           not (isinstance(a, str) and isinstance(b, str)):
            raise RuntimeErr(
                f"Operador '{op}' não pode comparar '{_type_name(a)}' com '{_type_name(b)}'",
                line)


# ══════════════════════════════════════════════════════
# 11. API PÚBLICA
# ══════════════════════════════════════════════════════

def run_code(source, source_path=None, env=None):
    """
    Compila e executa código-fonte Pyrus.
    Retorna a instância do interpretador em sucesso, None em falha.
    """
    try:
        tokens  = tokenize(source)
        program = Parser(tokens).parse()
        interp  = Interpreter(source_path)
        if env is not None:
            interp.globals = env
        interp.execute(program, interp.globals)
        return interp

    except (LexError, ParseError, RuntimeErr) as e:
        print(f"\n❌  {type(e).__name__.replace('Err','Error')}: {e}", file=sys.stderr)
        return None

    except _BreakSignal:
        print("❌  'break' fora de loop", file=sys.stderr)
        return None
    except _ContinueSignal:
        print("❌  'continue' fora de loop", file=sys.stderr)
        return None
    except _ReturnSignal:
        print("❌  'return' fora de função", file=sys.stderr)
        return None
    except KeyboardInterrupt:
        print("\n[Pyrus] Interrompido pelo usuário (Ctrl+C)")
        return None
    except SystemExit:
        raise   # propaga exit() para o processo pai
    except Exception as e:
        print(f"❌  Erro interno: {e}", file=sys.stderr)
        return None


def run_file(path):
    """Executa um arquivo .pyu pelo caminho."""
    if not os.path.exists(path):
        print(f"❌  Arquivo não encontrado: '{path}'", file=sys.stderr)
        return False
    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()
    return run_code(source, source_path=path) is not None
