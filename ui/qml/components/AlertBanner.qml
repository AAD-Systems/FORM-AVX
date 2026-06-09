// ui/qml/components/AlertBanner.qml
import QtQuick 2.15

Rectangle {
    property string texto:  ""
    property string codigo: ""

    height: 36
    color:  codigo === "TELEMETRY_LOST" ? "#3d1a00" : "#1a1a00"
    border.color: codigo === "TELEMETRY_LOST" ? "#ef4444" : "#f59e0b"

    Row {
        anchors { left: parent.left; verticalCenter: parent.verticalCenter; leftMargin: 12 }
        spacing: 8

        Text {
            text:  codigo === "TELEMETRY_LOST" ? "⚠️" : "ℹ️"
            font.pixelSize: 14
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text:  texto
            color: codigo === "TELEMETRY_LOST" ? "#ef4444" : "#f59e0b"
            font { family: "monospace"; pixelSize: 12; bold: true }
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    // Animação de piscar para alertas críticos
    SequentialAnimation on opacity {
        running:  codigo === "TELEMETRY_LOST"
        loops:    Animation.Infinite
        NumberAnimation { to: 0.4; duration: 600 }
        NumberAnimation { to: 1.0; duration: 600 }
    }
}
