// ui/qml/components/SignalIndicator.qml
import QtQuick 2.15

Item {
    property real qualidade: 100.0
    height: 36

    readonly property color cor: {
        if (qualidade > 70) return "#10b981"
        if (qualidade > 30) return "#f59e0b"
        return "#ef4444"
    }

    Rectangle {
        anchors.fill: parent
        color: "#161d2b"; radius: 6; border.color: "#1e2a3a"

        Row {
            anchors { left: parent.left; verticalCenter: parent.verticalCenter; leftMargin: 8 }
            spacing: 8

            Text {
                text:  "SINAL"
                color: "#64748b"
                font { family: "monospace"; pixelSize: 9 }
                anchors.verticalCenter: parent.verticalCenter
            }

            // Barrinhas de sinal (tipo celular)
            Row {
                spacing: 3
                anchors.verticalCenter: parent.verticalCenter
                Repeater {
                    model: 5
                    Rectangle {
                        width:  5
                        height: 6 + index * 4
                        radius: 2
                        anchors.bottom: parent.bottom
                        color: (index < Math.ceil(qualidade / 20))
                               ? cor : "#1e2a3a"
                    }
                }
            }

            Text {
                text:  qualidade.toFixed(0) + "%"
                color: cor
                font { family: "monospace"; pixelSize: 11; bold: true }
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
}


// ─────────────────────────────────────────────────────
// ui/qml/components/AlertBanner.qml
// Banner de alerta que aparece no topo da área central
