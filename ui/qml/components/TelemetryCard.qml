// ui/qml/components/TelemetryCard.qml
import QtQuick 2.15

Item {
    property string label: "---"
    property string value: "0"
    property color  cor:   "#e2e8f0"

    width:  parent ? parent.width : 180
    height: 42

    Rectangle {
        anchors.fill: parent
        color:        "#161d2b"
        border.color: "#1e2a3a"
        radius:       6
    }

    Column {
        anchors { left: parent.left; verticalCenter: parent.verticalCenter; leftMargin: 10 }
        spacing: 2
        Text {
            text:  label
            color: "#64748b"
            font { family: "monospace"; pixelSize: 9; letterSpacing: 1 }
        }
        Text {
            text:  value
            color: cor
            font { family: "monospace"; pixelSize: 15; bold: true }
        }
    }
}
