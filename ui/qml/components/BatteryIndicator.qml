// ui/qml/components/BatteryIndicator.qml
import QtQuick 2.15

Item {
    property real   percentual: 100.0
    property real   tensao:     4.2
    height: 52

    readonly property color barCor: {
        if (percentual > 50) return "#10b981"
        if (percentual > 20) return "#f59e0b"
        return "#ef4444"
    }

    Rectangle {
        anchors.fill: parent
        color:  "#161d2b"; radius: 6; border.color: "#1e2a3a"

        Column {
            anchors { fill: parent; margins: 8 }
            spacing: 4

            Row {
                spacing: 6
                Text {
                    text:  "BAT"
                    color: "#64748b"
                    font { family: "monospace"; pixelSize: 9 }
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text:  percentual.toFixed(1) + "%  " + tensao.toFixed(2) + "V"
                    color: barCor
                    font { family: "monospace"; pixelSize: 11; bold: true }
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            // Barra de progresso
            Rectangle {
                width: parent.width; height: 8; radius: 4
                color: "#0a0d12"
                Rectangle {
                    width:  parent.width * (percentual / 100)
                    height: parent.height; radius: 4
                    color:  barCor
                    Behavior on width { NumberAnimation { duration: 300 } }
                }
            }
        }
    }
}
