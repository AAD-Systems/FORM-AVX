// ui/qml/components/TacticalMap.qml
// Mapa tático com trilha do voo e posição do drone
// Usa tiles OSM locais ou online como fallback

import QtQuick 2.15
import QtLocation 5.15
import QtPositioning 5.15

Item {
    id: mapa

    property real lat_drone: -9.6658
    property real lon_drone: -35.7350
    property real heading:   0.0

    // Trilha do voo (lista de coordenadas)
    property var trilha: []
    property int maxTrilha: 500

    // Atualiza trilha quando posição muda
    onLat_droneChanged: _atualizarTrilha()
    onLon_droneChanged: _atualizarTrilha()

    function _atualizarTrilha() {
        if (lat_drone === 0.0 && lon_drone === 0.0) return
        var nova = trilha.slice()
        nova.push(QtPositioning.coordinate(lat_drone, lon_drone))
        if (nova.length > maxTrilha) nova = nova.slice(nova.length - maxTrilha)
        trilha = nova
        poliTrilha.path = nova
    }

    Plugin {
        id:   mapPlugin
        name: "osm"
        PluginParameter {
            name:  "osm.mapping.providersrepository.disabled"
            value: "true"
        }
        // Tenta tiles locais primeiro
        PluginParameter {
            name:  "osm.mapping.cache.directory"
            value: Qt.resolvedUrl("../../assets/tiles")
        }
    }

    Map {
        id:           mapaQt
        anchors.fill: parent
        plugin:       mapPlugin
        center:       QtPositioning.coordinate(mapa.lat_drone, mapa.lon_drone)
        zoomLevel:    16
        color:        "#0a0d12"

        // Centraliza no drone
        onLat_droneChanged: {
            if (!travado) return
            mapaQt.center = QtPositioning.coordinate(mapa.lat_drone, mapa.lon_drone)
        }
        property bool travado: true

        // Trilha do voo
        MapPolyline {
            id:        poliTrilha
            line.color: "#7c3aed"
            line.width: 2
            path:      []
        }

        // Ícone do drone
        MapQuickItem {
            coordinate:       QtPositioning.coordinate(mapa.lat_drone, mapa.lon_drone)
            anchorPoint.x:    20
            anchorPoint.y:    20
            zoomLevel:        0

            sourceItem: Item {
                width: 40; height: 40

                Canvas {
                    anchors.fill: parent
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        ctx.save()
                        ctx.translate(20, 20)
                        ctx.rotate(mapa.heading * Math.PI / 180)

                        // Corpo do drone (triângulo apontando para cima = heading)
                        ctx.fillStyle   = "#f59e0b"
                        ctx.strokeStyle = "#0a0d12"
                        ctx.lineWidth   = 1.5
                        ctx.beginPath()
                        ctx.moveTo(0, -12)
                        ctx.lineTo(-8, 8)
                        ctx.lineTo(8,  8)
                        ctx.closePath()
                        ctx.fill()
                        ctx.stroke()

                        // Ponto central
                        ctx.fillStyle = "#0a0d12"
                        ctx.beginPath()
                        ctx.arc(0, 0, 3, 0, Math.PI * 2)
                        ctx.fill()

                        ctx.restore()
                    }

                    property real h: mapa.heading
                    onHChanged: requestPaint()
                }
            }
        }

        // Controles do mapa
        Rectangle {
            anchors { bottom: parent.bottom; right: parent.right; margins: 8 }
            color:        "#161d2b"
            border.color: "#1e2a3a"
            radius:       6
            width: 32; height: 80

            Column {
                anchors.centerIn: parent
                spacing: 4

                Text {
                    text:  "+"
                    color: "#e2e8f0"
                    font.pixelSize: 18
                    MouseArea {
                        anchors.fill: parent
                        onClicked: mapaQt.zoomLevel = Math.min(19, mapaQt.zoomLevel + 1)
                    }
                }
                Text {
                    text: "-"
                    color: "#e2e8f0"
                    font.pixelSize: 18
                    MouseArea {
                        anchors.fill: parent
                        onClicked: mapaQt.zoomLevel = Math.max(2, mapaQt.zoomLevel - 1)
                    }
                }
            }
        }

        // Botão de centralizar
        Rectangle {
            anchors { bottom: parent.bottom; left: parent.left; margins: 8 }
            color:        mapaQt.travado ? "#1a1a3a" : "#161d2b"
            border.color: mapaQt.travado ? "#7c3aed" : "#1e2a3a"
            radius: 6; width: 60; height: 24

            Text {
                anchors.centerIn: parent
                text:  mapaQt.travado ? "📍 FIXO" : "🔓 LIVRE"
                color: "#e2e8f0"
                font { family: "monospace"; pixelSize: 9 }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: mapaQt.travado = !mapaQt.travado
            }
        }

        // Coordenadas (canto superior esquerdo)
        Rectangle {
            anchors { top: parent.top; left: parent.left; margins: 6 }
            color: "transparent"

            Text {
                text: mapa.lat_drone.toFixed(6) + "  " + mapa.lon_drone.toFixed(6)
                color: "#64748b"
                font { family: "monospace"; pixelSize: 9 }
            }
        }
    }
}
