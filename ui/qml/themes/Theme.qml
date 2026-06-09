// ui/qml/themes/Theme.qml
// Paleta industrial escura do FORM AVX
// Uma única fonte de verdade para todas as cores

pragma Singleton
import QtQuick 2.15

QtObject {
    readonly property color bg:      "#0a0d12"
    readonly property color panel:   "#111620"
    readonly property color bg3:     "#161d2b"
    readonly property color border:  "#1e2a3a"
    readonly property color text:    "#e2e8f0"
    readonly property color dim:     "#64748b"
    readonly property color accent:  "#7c3aed"
    readonly property color accent2: "#06b6d4"
    readonly property color green:   "#10b981"
    readonly property color amber:   "#f59e0b"
    readonly property color red:     "#ef4444"
    readonly property color orange:  "#f97316"

    readonly property string mono: "JetBrains Mono, Consolas, monospace"
}
