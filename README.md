# 🛸 FORM AVX

**Ground Control Station para drones — feita em Pyrus 🍐**

[![Status](https://img.shields.io/badge/status-alpha%20v0.1-orange)](https://github.com/AAD-Systems/FORM-AVX)
[![Pyrus](https://img.shields.io/badge/core-Pyrus%20v0.2.0-8b5cf6)](https://github.com/AAD-Systems/pyrus)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Termux%20%7C%20Windows-blue)](https://github.com/AAD-Systems/FORM-AVX)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

FORM AVX é uma Ground Control Station (GCS) tática construída do zero sobre a linguagem **Pyrus**.  
Leve, modular e projetada para rodar no **Termux** sem dependências pesadas.

✅ MAVLink via UDP/Serial · ✅ Logs binários `.avx-stream` · ✅ HUD com horizonte artificial  
✅ Mapa tático com trilha de voo · ✅ Replay de voos · ✅ Sistema de plugins

---

## 🚀 Instalação

```bash
git clone https://github.com/AAD-Systems/FORM-AVX
cd FORM-AVX
python avx.py --mode sim --headless
```

Para interface gráfica (opcional): pip install PyQt6

---

📖 Como usar

Modo Comando
Simulador (recomendado) python avx.py --mode sim
Apenas terminal python avx.py --mode sim --headless
Drone real (UDP) python avx.py --mode live
Drone real (Serial) python avx.py --mode serial --serial /dev/ttyUSB0
Replay de voo python avx.py --mode replay --replay logs/voo.avx-stream
Testes python avx.py test
Informações python avx.py info

---

🧩 Plugins

Crie um arquivo .pyu na pasta plugins/:

```rust
func on_plugin_load() { print("Plugin carregado"); }
func on_telemetry_packet(p) { print(p["alt"]); }
func on_plugin_unload() { print("Plugin descarregado"); }
```

---

📁 Estrutura

```
FORM-AVX/
├── avx.py              # Ponto de entrada
├── core.py             # Interpretador Pyrus
├── core/               # Lógica em Pyrus
├── telemetry/          # MAVLink + Simulador
├── ui/                 # Interface PyQt6/QML
├── plugins/            # Plugins .pyu
└── tests/              # Testes unitários
```

---

🗃️ Formato .avx-stream

Registros binários de 64 bytes, acesso O(1):

Offset Tipo Campo
0x00 uint64 timestamp
0x08 float64 latitude
0x10 float64 longitude
0x18 float32 altitude
0x1C float32 velocidade
0x20-0x3F - atitude, bateria, sinal

---

🗺️ Roadmap

Versão Features Status
v0.1 MAVLink, storage, HUD, mapa, replay 🔨 Em desenvolvimento
v0.2 Planejador de missão, controles de replay 📋 Planejado
v0.3 API de plugins estável 📋 Planejado
v1.0 Core compilado nativo 🎯 Meta

---

🤝 Contribuindo

Issues, PRs e feedback são bem-vindos.
Testes com hardware MAVLink real são especialmente úteis.

---

📄 Licença

MIT · Feito em Alagoas, Brasil 🇧🇷🍐