# 🛸 FORM AVX

**Ground Control Station para drones — feita em Pyrus 🍐**

[![Status](https://img.shields.io/badge/status-alpha%20v0.1-orange)](https://github.com/Security-Labor/form-avx)
[![Linguagem](https://img.shields.io/badge/core-Pyrus%20v0.2.0-8b5cf6)](https://github.com/Security-Labor/pyrus)
[![Plataforma](https://img.shields.io/badge/roda%20em-Linux%20%7C%20Termux%20%7C%20Windows-blue)](.)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)](LICENSE)

---

Esse projeto nasceu de uma pergunta simples: por que toda Ground Control Station
disponível é pesada, fechada ou depende de uma pilha enorme de dependências que
quebra no Termux?

O FORM AVX é a minha resposta. Uma GCS tática construída do zero sobre a
[linguagem Pyrus](https://github.com/Security-Labor/pyrus) — que eu também
desenvolvo — com foco em ser leve, entendível e modificável por qualquer pessoa
com Python instalado.

Não é um produto acabado. É um projeto que estou construindo em público,
um commit de cada vez.

---

## O que ele faz

- Recebe telemetria MAVLink via UDP ou Serial em tempo real
- Grava logs de voo em formato binário `.avx-stream` (64 bytes por registro, acesso O(1))
- Exibe HUD de atitude com horizonte artificial, altitude, velocidade e heading
- Plota a posição do drone em mapa tático com trilha de voo
- Reproduz voos gravados em modo replay (1x, 2x, 4x)
- Aceita plugins `.pyu` para estender o sistema sem mexer no core
- Tem um simulador embutido pra desenvolver sem precisar de drone nenhum

---

## Estrutura real do projeto

```
form-avx/
│
├── avx.py                      ← ponto de entrada único. tudo começa aqui
│
├── core.py                     ← interpretador Pyrus (zero dependências)
├── pyrus.py                    ← CLI da linguagem
├── lexer.py                    ← análise léxica
│
├── core/
│   ├── main.pyu                ← inicializa todos os subsistemas
│   ├── event_bus.pyu           ← barramento pub/sub interno
│   ├── storage.pyu             ← gravação de logs .avx-stream
│   ├── mission.pyu             ← upload de waypoints MAVLink
│   ├── replay.pyu              ← reprodutor de voos gravados
│   └── plugin_loader.pyu       ← carrega plugins da pasta plugins/
│
├── telemetry/
│   ├── mavlink_bridge.pyu      ← parser MAVLink UDP e Serial
│   └── simulator.pyu           ← telemetria falsa para desenvolvimento
│
├── avx_ext/
│   ├── __init__.py
│   └── avx_builtins.py         ← extensões Python: struct, binary I/O, storage
│
├── ui/
│   ├── main.py                 ← launcher PyQt6 (opcional)
│   ├── ui_bridge.py            ← QObject bridge Python ↔ QML
│   └── qml/
│       ├── main.qml
│       ├── components/
│       │   ├── HudOverlay.qml
│       │   ├── TacticalMap.qml
│       │   ├── TelemetryCard.qml
│       │   ├── BatteryIndicator.qml
│       │   ├── SignalIndicator.qml
│       │   └── AlertBanner.qml
│       └── themes/
│           └── Theme.qml
│
├── plugins/
│   └── exemplo_altitude_monitor.pyu
│
├── tests/
│   ├── test_mavlink.pyu
│   └── test_storage.pyu
│
└── logs/
    └── *.avx-stream
```

---

## Instalação

Python 3.8+ é tudo que você precisa para o Core.
PyQt6 é necessário apenas se você quiser a interface gráfica.

```bash
git clone https://github.com/Security-Labor/form-avx
cd form-avx

# Interface gráfica (opcional)
pip install PyQt6
```

**No Termux:**

```bash
pkg install python git
git clone https://github.com/Security-Labor/form-avx
cd form-avx
pip install PyQt6   # opcional
```

---

## Como rodar

Tudo passa pelo `avx.py`. É o único ponto de entrada.

```bash
# Simulador — sem drone, sem hardware, funciona agora
python avx.py --mode sim

# Simulador sem interface gráfica (só terminal, zero dependências)
python avx.py --mode sim --headless

# Drone real via UDP (MAVLink padrão porta 14550)
python avx.py --mode live

# Drone via cabo serial
python avx.py --mode serial --serial /dev/ttyUSB0

# Replay de um voo gravado
python avx.py --mode replay --replay logs/voo_1748000000.avx-stream

# Rodar os testes
python avx.py test

# Informações do sistema
python avx.py info
```

Se o PyQt6 não estiver instalado, o `avx.py` cai automaticamente para modo
`--headless` sem reclamar.

---

## Testes

Os testes são escritos em Pyrus e rodam sem nenhum framework externo:

```bash
python avx.py test
```

Saída esperada:

```
══════════════════════════════════════════════════
Rodando: test_mavlink.pyu
══════════════════════════════════════════════════
  ✅ GPS lat Maceió
  ✅ GPS lon Maceió
  ✅ Altitude mm→m
  ✅ Tensão mV→V
  ✅ rad→grau 180°
  ✅ rad→grau -45°
  ✅ Magic byte válido
  ✅ Magic byte inválido

══════════════════════════════════════════════════
Rodando: test_storage.pyu
══════════════════════════════════════════════════
  ✅ Total de registros após 2 gravações
  ✅ Registro 0 — lat
  ✅ Registro 0 — lon
  ✅ Registro 0 — alt
  ✅ Registro 0 — speed
  ✅ Registro 1 — lat
  ✅ Registro 1 — alt
  ✅ Índice fora do range retorna null
  ✅ Timestamp do registro 0
  ✅ Total após append
  ✅ Registro 2 — lat

Arquivos OK: 2 | Com erro: 0
```

---

## Formato .avx-stream

Cada registro é exatamente 64 bytes. Binário puro, append-only, sem cabeçalho.

```
Offset 0x00 – 0x07  │  uint64   │  timestamp        │  Microssegundos Unix
Offset 0x08 – 0x0F  │  float64  │  latitude         │  Graus decimais WGS84
Offset 0x10 – 0x17  │  float64  │  longitude        │  Graus decimais WGS84
Offset 0x18 – 0x1B  │  float32  │  altitude         │  Metros rel. decolagem
Offset 0x1C – 0x1F  │  float32  │  speed            │  m/s
Offset 0x20 – 0x23  │  float32  │  pitch            │  Radianos
Offset 0x24 – 0x27  │  float32  │  roll             │  Radianos
Offset 0x28 – 0x2B  │  float32  │  yaw              │  Radianos
Offset 0x2C – 0x2F  │  float32  │  battery_voltage  │  Volts
Offset 0x30 – 0x33  │  float32  │  signal_quality   │  0.0 a 1.0
Offset 0x34 – 0x37  │  float32  │  climb            │  m/s
Offset 0x38 – 0x3F  │  uint8[8] │  reserved         │  Reservado
```

Buscar qualquer registro é O(1):

```python
offset          = indice * 64
total_registros = tamanho_arquivo // 64
```

---

## Criando um plugin

Qualquer arquivo `.pyu` na pasta `plugins/` é carregado automaticamente.
Três funções obrigatórias:

```rust
// plugins/meu_plugin.pyu

func on_plugin_load() {
    print("[MeuPlugin] Carregado.");
}

func on_telemetry_packet(pacote) {
    if pacote["alt"] > 100.0 {
        print("[MeuPlugin] Altitude alta: " + str(pacote["alt"]) + "m");
    }
}

func on_plugin_unload() {
    print("[MeuPlugin] Descarregado.");
}
```

Salva em `plugins/` e reinicia. Pronto.

---

## Como o Core e a UI se comunicam

O Core roda em thread separada executando Pyrus.
A UI roda na thread principal do Qt.
Eles se comunicam por uma `queue.Queue` Python thread-safe.

O Core publica dicionários na fila a cada pacote de telemetria.
A UI drena essa fila a 60Hz via `QTimer` e atualiza as propriedades QML.

Do ponto de vista da UI, drone ao vivo, simulador e replay são idênticos.
O barramento é o mesmo nos três casos.

---

## Por que Pyrus?

Porque eu desenvolvo as duas coisas. O FORM AVX é a prova de que a Pyrus
serve para algo real.

O parser MAVLink, o gravador de logs, a lógica de missão, o replay — tudo
em `.pyu`. A interface só renderiza. Quando o compilador da Pyrus chegar
(v0.6+), esse mesmo código gera binários nativos. A sintaxe não muda.

---

## Roadmap

| Versão | O que vem | Status |
|--------|-----------|--------|
| v0.1 | Core MAVLink, storage, simulador, HUD, mapa, replay | 🔨 Em desenvolvimento |
| v0.2 | Controles de replay na UI, planejador de missão clicável | 📋 Planejado |
| v0.3 | Sistema de plugins estável com API documentada | 📋 Planejado |
| v0.4 | Suporte a múltiplos drones simultâneos | 📋 Planejado |
| v1.0 | Core compilado nativamente via Pyrus v0.6+ | 🎯 Meta |

---

## Contribuindo

Issues, pull requests e feedback são bem-vindos.

Se você tem um drone e quer testar a conexão MAVLink real, isso já é uma
contribuição enorme. O `mavlink_bridge.pyu` precisa de testes com hardware
real e suporte a mais tipos de mensagem.

---

## Tecnologias

- **[Pyrus v0.2.0](https://github.com/Security-Labor/pyrus)** — linguagem do Core
- **Python 3.8+** — runtime
- **PyQt6** — interface gráfica (opcional)
- **MAVLink v1** — protocolo de telemetria
- **OpenStreetMap** — tiles de mapa

---

## Licença

MIT. Usa, modifica, distribui. Só mantém o crédito.

---

**Feito em Alagoas, Brasil. 🇧🇷🍐**

*Ferramentas de drone deveriam funcionar no Termux do celular,
não só no MacBook com assinatura de tudo.*
