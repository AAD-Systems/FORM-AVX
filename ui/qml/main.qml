// ui/qml/main.qml
// Janela principal do FORM AVX
// Layout: HUD central, mapa tático, painel de telemetria lateral

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"
import "themes"

ApplicationWindow {
    id:         root
    title:      "FORM AVX — Ground Control Station 🍐"
    width:      1280
    height:     800
    visible:    true
    color:      Theme.bg

    // ── Atualiza título com status ────────────────────
    Connections {
        target: avx
        function onModoAlterado(modo) {
            root.title = "FORM AVX — " + modo
        }
        function onAlertaEmitido(codigo, msg) {
            if (codigo !== "") {
                bannerAlerta.texto  = msg
                bannerAlerta.codigo = codigo
                bannerAlerta.visivel = true
            } else {
                bannerAlerta.visivel = false
            }
        }
    }

    // ── Layout principal ──────────────────────────────
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ── Painel lateral esquerdo — Telemetria
        Rectangle {
            width:  220
            Layout.fillHeight: true
            color:  Theme.panel
            border.color: Theme.border
            border.width: 1

            ColumnLayout {
                anchors { fill: parent; margins: 12 }
                spacing: 10

                // Logo / cabeçalho
                Text {
                    text:  "🍐 FORM AVX"
                    color: Theme.accent
                    font { family: "monospace"; pixelSize: 18; bold: true }
                }
                Text {
                    text:  "v0.1.0 — " + avx.statusSistema
                    color: avx.statusSistema === "OK" ? Theme.green : Theme.amber
                    font { family: "monospace"; pixelSize: 11 }
                }

                Rectangle { height: 1; Layout.fillWidth: true; color: Theme.border }

                // Altitude
                TelemetryCard {
                    label: "ALTITUDE"
                    value: avx.alt + " m"
                    cor:   Theme.accent2
                }

                // Velocidade
                TelemetryCard {
                    label: "VELOCIDADE"
                    value: avx.speed + " m/s"
                    cor:   Theme.text
                }

                // Heading
                TelemetryCard {
                    label: "HEADING"
                    value: avx.heading + "°"
                    cor:   Theme.text
                }

                // Climb rate
                TelemetryCard {
                    label: "CLIMB"
                    value: (avx.climb >= 0 ? "+" : "") + avx.climb + " m/s"
                    cor:   avx.climb >= 0 ? Theme.green : Theme.red
                }

                Rectangle { height: 1; Layout.fillWidth: true; color: Theme.border }

                // Bateria
                BatteryIndicator {
                    Layout.fillWidth: true
                    percentual: avx.bateriaPct
                    tensao:     avx.batteryVoltage
                }

                // Sinal
                SignalIndicator {
                    Layout.fillWidth: true
                    qualidade: avx.signalQuality
                }

                Rectangle { height: 1; Layout.fillWidth: true; color: Theme.border }

                // Modo de voo
                Text {
                    text:  "MODO"
                    color: Theme.dim
                    font { family: "monospace"; pixelSize: 10 }
                }
                Text {
                    text:  avx.modoVoo
                    color: avx.armed ? Theme.red : Theme.green
                    font { family: "monospace"; pixelSize: 14; bold: true }
                }

                // ARMED indicator
                Rectangle {
                    Layout.fillWidth: true
                    height: 28
                    radius: 6
                    color:  avx.armed ? "#3d0000" : "#003d0a"
                    border.color: avx.armed ? Theme.red : Theme.green
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text:  avx.armed ? "⚡ ARMADO" : "✓ DESARMADO"
                        color: avx.armed ? Theme.red : Theme.green
                        font { family: "monospace"; pixelSize: 11; bold: true }
                    }
                }

                Item { Layout.fillHeight: true }

                // Pacotes recebidos (debug)
                Text {
                    text:  "PKT: " + avx.totalPacotes
                    color: Theme.dim
                    font { family: "monospace"; pixelSize: 9 }
                }
            }
        }

        // ── Área central — HUD + Mapa
        ColumnLayout {
            Layout.fillWidth:  true
            Layout.fillHeight: true
            spacing: 0

            // Banner de alerta (visível apenas em avisos)
            AlertBanner {
                id:              bannerAlerta
                Layout.fillWidth: true
                visible:         false
                property string texto:   ""
                property string codigo:  ""
                property bool   visivel: false
                onVisivelChanged: visible = visivel
            }

            // HUD de atitude
            HudOverlay {
                Layout.fillWidth:  true
                height:            280
                pitch_rad:  avx.pitch
                roll_rad:   avx.roll
                heading_deg: avx.heading
                alt_m:       avx.alt
                speed_ms:    avx.speed
            }

            // Mapa tático
            TacticalMap {
                Layout.fillWidth:  true
                Layout.fillHeight: true
                lat_drone: avx.lat
                lon_drone: avx.lon
                heading:   avx.heading
            }
        }
    }
}
