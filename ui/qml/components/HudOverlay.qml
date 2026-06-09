// ui/qml/components/HudOverlay.qml
// HUD de atitude — Horizonte artificial, altitude, velocidade, heading

import QtQuick 2.15

Item {
    id: hud

    property real pitch_rad:   0.0
    property real roll_rad:    0.0
    property real heading_deg: 0.0
    property real alt_m:       0.0
    property real speed_ms:    0.0

    // Conversões para graus
    readonly property real pitch_deg: pitch_rad * 57.2958
    readonly property real roll_deg:  roll_rad  * 57.2958

    // Fundo do HUD
    Rectangle {
        anchors.fill: parent
        color:        "#0d1520"
        border.color: "#1e2a3a"
        border.width: 1
    }

    // ── Horizonte artificial (Canvas) ─────────────────
    Canvas {
        id:            horizonte
        anchors.fill:  parent
        antialiasing:  true

        // Redesenha quando pitch ou roll mudam
        property real p: hud.pitch_deg
        property real r: hud.roll_deg
        onPChanged: requestPaint()
        onRChanged: requestPaint()

        onPaint: {
            var ctx = getContext("2d")
            var w   = width
            var h   = height
            var cx  = w / 2
            var cy  = h / 2

            ctx.clearRect(0, 0, w, h)

            // Salva estado e aplica rotação de roll
            ctx.save()
            ctx.translate(cx, cy)
            ctx.rotate(-r * Math.PI / 180)

            // Deslocamento vertical por pitch (10px por grau)
            var pitchOffset = p * 4.0

            // Céu
            ctx.fillStyle = "#0a2040"
            ctx.fillRect(-w, -h + pitchOffset, w * 2, h)

            // Terra
            ctx.fillStyle = "#2d1a00"
            ctx.fillRect(-w, pitchOffset, w * 2, h)

            // Linha de horizonte
            ctx.strokeStyle = "#10b981"
            ctx.lineWidth   = 2
            ctx.beginPath()
            ctx.moveTo(-w / 2, pitchOffset)
            ctx.lineTo( w / 2, pitchOffset)
            ctx.stroke()

            // Linhas de pitch (a cada 10 graus)
            ctx.strokeStyle = "rgba(255,255,255,0.4)"
            ctx.lineWidth   = 1
            ctx.font        = "10px monospace"
            ctx.fillStyle   = "rgba(255,255,255,0.6)"
            for (var deg = -30; deg <= 30; deg += 10) {
                if (deg === 0) continue
                var y  = pitchOffset - deg * 4.0
                var lw = (deg % 20 === 0) ? w * 0.15 : w * 0.08
                ctx.beginPath()
                ctx.moveTo(-lw, y)
                ctx.lineTo( lw, y)
                ctx.stroke()
                ctx.fillText(deg + "°", lw + 4, y + 4)
            }

            ctx.restore()

            // ── Mira central (fixa, não rotaciona)
            ctx.strokeStyle = "#10b981"
            ctx.lineWidth   = 2
            // Braço esquerdo
            ctx.beginPath(); ctx.moveTo(cx - 80, cy)
            ctx.lineTo(cx - 20, cy); ctx.stroke()
            // Braço direito
            ctx.beginPath(); ctx.moveTo(cx + 20, cy)
            ctx.lineTo(cx + 80, cy); ctx.stroke()
            // Centro
            ctx.beginPath()
            ctx.arc(cx, cy, 4, 0, Math.PI * 2)
            ctx.fillStyle = "#10b981"
            ctx.fill()

            // ── Indicador de roll (arco no topo)
            ctx.save()
            ctx.translate(cx, cy)
            ctx.strokeStyle = "#06b6d4"
            ctx.lineWidth   = 1.5
            ctx.beginPath()
            ctx.arc(0, 0, cy * 0.7, -Math.PI * 0.75, -Math.PI * 0.25)
            ctx.stroke()
            // Ponteiro de roll
            var rollRad = -hud.roll_rad
            var pr      = cy * 0.7
            ctx.beginPath()
            ctx.moveTo(Math.cos(rollRad - Math.PI/2) * (pr - 8),
                       Math.sin(rollRad - Math.PI/2) * (pr - 8))
            ctx.lineTo(Math.cos(rollRad - Math.PI/2) * (pr + 8),
                       Math.sin(rollRad - Math.PI/2) * (pr + 8))
            ctx.strokeStyle = "#f59e0b"
            ctx.lineWidth   = 2
            ctx.stroke()
            ctx.restore()
        }
    }

    // ── Altitude (direita) ────────────────────────────
    Rectangle {
        anchors { right: parent.right; verticalCenter: parent.verticalCenter }
        width:  64; height: 80
        color:  "transparent"

        Column {
            anchors.centerIn: parent
            spacing: 2

            Text {
                text:  "ALT"
                color: "#64748b"
                font { family: "monospace"; pixelSize: 9 }
                anchors.horizontalCenter: parent.horizontalCenter
            }
            Text {
                text:  hud.alt_m.toFixed(1)
                color: "#06b6d4"
                font { family: "monospace"; pixelSize: 20; bold: true }
                anchors.horizontalCenter: parent.horizontalCenter
            }
            Text {
                text:  "m"
                color: "#64748b"
                font { family: "monospace"; pixelSize: 10 }
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }

    // ── Velocidade (esquerda) ─────────────────────────
    Rectangle {
        anchors { left: parent.left; verticalCenter: parent.verticalCenter }
        width:  64; height: 80
        color:  "transparent"

        Column {
            anchors.centerIn: parent
            spacing: 2

            Text {
                text:  "SPD"
                color: "#64748b"
                font { family: "monospace"; pixelSize: 9 }
                anchors.horizontalCenter: parent.horizontalCenter
            }
            Text {
                text:  hud.speed_ms.toFixed(1)
                color: "#e2e8f0"
                font { family: "monospace"; pixelSize: 20; bold: true }
                anchors.horizontalCenter: parent.horizontalCenter
            }
            Text {
                text:  "m/s"
                color: "#64748b"
                font { family: "monospace"; pixelSize: 10 }
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }

    // ── Heading (topo centro) ─────────────────────────
    Rectangle {
        anchors { horizontalCenter: parent.horizontalCenter; top: parent.top }
        width: 90; height: 30
        color: "#161d2b"
        border.color: "#1e2a3a"
        radius: 4

        Text {
            anchors.centerIn: parent
            text:  hud.heading_deg.toFixed(0) + "°  " + _headingStr(hud.heading_deg)
            color: "#f59e0b"
            font { family: "monospace"; pixelSize: 13; bold: true }
        }

        function _headingStr(h) {
            if (h < 22.5  || h >= 337.5) return "N"
            if (h < 67.5)  return "NE"
            if (h < 112.5) return "L"
            if (h < 157.5) return "SE"
            if (h < 202.5) return "S"
            if (h < 247.5) return "SO"
            if (h < 292.5) return "O"
            return "NO"
        }
    }
}
