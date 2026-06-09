"""
ui/ui_bridge.py
Bridge entre o Core Pyrus e a interface QML.

É um QObject com propriedades reativas.
Quando o Core publica telemetria, este bridge
atualiza as propriedades e o QML reage automaticamente.
"""

import queue
import math
from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QVariant


class AVXBridge(QObject):
    # ── Sinais emitidos quando dados mudam ────────────────
    telemetriaAtualizada  = pyqtSignal()
    alertaEmitido         = pyqtSignal(str, str)    # codigo, mensagem
    modoAlterado          = pyqtSignal(str)
    missaoAtualizada      = pyqtSignal()
    replayProgresso       = pyqtSignal(float)

    def __init__(self, fila: queue.Queue, parent=None):
        super().__init__(parent)
        self._fila = fila

        # Estado de telemetria
        self._lat              = 0.0
        self._lon              = 0.0
        self._alt              = 0.0
        self._speed            = 0.0
        self._pitch            = 0.0
        self._roll             = 0.0
        self._yaw              = 0.0
        self._battery_voltage  = 0.0
        self._signal_quality   = 0.0
        self._bateria_pct      = 0.0
        self._modo_voo         = "---"
        self._armed            = False
        self._climb            = 0.0

        # Estado do sistema
        self._status_sistema   = "OK"
        self._total_pacotes    = 0
        self._alerta_atual     = ""

    # ── Drena a fila a cada tick do QTimer ───────────────
    def atualizar(self):
        atualizado = False
        try:
            for _ in range(20):   # processa até 20 pacotes por frame
                pacote = self._fila.get_nowait()
                self._processar_pacote(pacote)
                atualizado = True
        except queue.Empty:
            pass

        if atualizado:
            self.telemetriaAtualizada.emit()

    def _processar_pacote(self, pacote):
        if not isinstance(pacote, dict):
            return

        tipo = pacote.get('tipo', '')

        if tipo == 'TELEMETRY' or tipo == 'REPLAY':
            self._lat             = pacote.get('lat',             self._lat)
            self._lon             = pacote.get('lon',             self._lon)
            self._alt             = pacote.get('alt',             self._alt)
            self._speed           = pacote.get('speed',           self._speed)
            self._pitch           = pacote.get('pitch',           self._pitch)
            self._roll            = pacote.get('roll',            self._roll)
            self._yaw             = pacote.get('yaw',             self._yaw)
            self._battery_voltage = pacote.get('battery_voltage', self._battery_voltage)
            self._signal_quality  = pacote.get('signal_quality',  self._signal_quality)
            self._bateria_pct     = pacote.get('bateria_pct',     self._bateria_pct)
            self._armed           = pacote.get('armed',           self._armed)
            self._climb           = pacote.get('climb',           self._climb)
            novo_modo = pacote.get('modo_voo', self._modo_voo)
            if novo_modo != self._modo_voo:
                self._modo_voo = novo_modo
                self.modoAlterado.emit(novo_modo)
            self._total_pacotes += 1

        elif tipo == 'SYSTEM_WARNING':
            codigo = pacote.get('codigo', 'UNKNOWN')
            self._status_sistema = 'AVISO'
            self.alertaEmitido.emit(codigo, self._descricao_alerta(codigo))

        elif tipo == 'SYSTEM_OK':
            self._status_sistema = 'OK'
            self.alertaEmitido.emit('', '')

        elif tipo == 'REPLAY_END':
            self.alertaEmitido.emit('REPLAY_END', 'Replay concluído')

    def _descricao_alerta(self, codigo):
        mensagens = {
            'TELEMETRY_LOST': 'Sinal perdido — sem telemetria há mais de 500ms',
            'SIM_ENDED':      'Simulação encerrada',
            'REPLAY_END':     'Replay concluído',
        }
        return mensagens.get(codigo, f'Alerta: {codigo}')

    # ── Propriedades expostas ao QML ──────────────────────
    @pyqtProperty(float, notify=telemetriaAtualizada)
    def lat(self): return self._lat

    @pyqtProperty(float, notify=telemetriaAtualizada)
    def lon(self): return self._lon

    @pyqtProperty(float, notify=telemetriaAtualizada)
    def alt(self): return round(self._alt, 1)

    @pyqtProperty(float, notify=telemetriaAtualizada)
    def speed(self): return round(self._speed, 1)

    @pyqtProperty(float, notify=telemetriaAtualizada)
    def pitch(self): return self._pitch

    @pyqtProperty(float, notify=telemetriaAtualizada)
    def roll(self): return self._roll

    @pyqtProperty(float, notify=telemetriaAtualizada)
    def yaw(self): return self._yaw

    @pyqtProperty(float, notify=telemetriaAtualizada)
    def batteryVoltage(self): return round(self._battery_voltage, 2)

    @pyqtProperty(float, notify=telemetriaAtualizada)
    def signalQuality(self): return round(self._signal_quality * 100, 0)

    @pyqtProperty(float, notify=telemetriaAtualizada)
    def bateriaPct(self): return round(self._bateria_pct, 1)

    @pyqtProperty(float, notify=telemetriaAtualizada)
    def climb(self): return round(self._climb, 1)

    @pyqtProperty(str, notify=modoAlterado)
    def modoVoo(self): return self._modo_voo

    @pyqtProperty(bool, notify=telemetriaAtualizada)
    def armed(self): return self._armed

    @pyqtProperty(str, notify=telemetriaAtualizada)
    def statusSistema(self): return self._status_sistema

    @pyqtProperty(int, notify=telemetriaAtualizada)
    def totalPacotes(self): return self._total_pacotes

    # Heading em graus (yaw em radianos → graus 0-360)
    @pyqtProperty(float, notify=telemetriaAtualizada)
    def heading(self):
        graus = math.degrees(self._yaw) % 360
        return round(graus, 1)

    # ── Slots chamáveis do QML ────────────────────────────
    @pyqtSlot(result=str)
    def versao(self):
        return "FORM AVX v0.1.0 — Pyrus 🍐"
