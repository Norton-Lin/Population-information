import QtQuick 2.15
import QtQuick.Dialogs 1.2
import QtQuick.Controls 2.15

ApplicationWindow {
    id: root
    visible: true
    width: 1640
    height: 640
    maximumHeight: height
    maximumWidth: width
    minimumHeight: height
    minimumWidth: width
    title: "全球人口分布查询系统"

    Connections {
        target: client
    }

    Image {
        id: map
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.topMargin: 10
        anchors.leftMargin: 10
        width: parent.width - 400
        source: "./world_map.jpg"
        fillMode: Image.PreserveAspectFit
        MouseArea {
            id: mouse_area
            anchors.fill: parent
            onClicked: client.add_coordinate(mouseX / width * 1296000 - 648000, -(mouseY / height * 648000 - 324000))
        }
    }

    Column {
        anchors.top: parent.top
        anchors.left: map.right
        anchors.topMargin: 10
        anchors.leftMargin: 10
        height: map.height - 30
        width: 370

        Row {
            id: title
            height: 30
            Text {
                text: "经度"
                width: 150
                verticalAlignment: Text.AlignVCenter
            }
            Text {
                text: "纬度"
                width: 150
                verticalAlignment: Text.AlignVCenter
            }
            Text {
                text: ""
                width: 70
                verticalAlignment: Text.AlignVCenter
            }
        }

        ListView {
            id: list_view
            anchors.left: parent.left
            height: parent.height - 30
            width: parent.width
            model: client.get_coordinates
            clip: true

            delegate: Row {
                property int indexOfThisDelegate: index
                height: 30
                Text {
                    text: modelData.get_x_deg + "°" + modelData.get_x_min + "′" + modelData.get_x_sec + "″"
                    width: 150
                    verticalAlignment: Text.AlignVCenter
                }
                Text {
                    text: modelData.get_y_deg + "°" + modelData.get_y_min + "′" + modelData.get_y_sec + "″"
                    width: 150
                    verticalAlignment: Text.AlignVCenter
                }
                Button {
                    width: 70
                    height: 20
                    text: "移除"
                    font.pixelSize: 15
                    onClicked: client.delete_coordinate(index)
                }
            }
            onCountChanged: {
                list_view.positionViewAtEnd()
            }
            ScrollBar.vertical: ScrollBar {
                active: true
            }
        }

        Dialog {
            id: dialog
            title: "坐标添加"
            x:(parent.width-width)/2
            y:(parent.height-height)/2
            height: 200
            width: 400
            standardButtons: Dialog.Ok | Dialog.Cancel

            TextField {
                id: lon
                anchors.left: parent.left
                placeholderText: "请输入经度："
            }

            TextField {
                id: lat
                anchors.right: parent.right
                placeholderText: "请输入纬度："
            }

            onAccepted: client.add_coordinate(lon.text,lat.text)
            onRejected: console.log("Cancel clicked")
        }

        Row {
            id: button
            anchors.right: list_view.right
            width: 370
            height: 30

            Button {
                text: "查询"
                font.pixelSize: 15
                onClicked: client.query()
            }

            Text {
                text: ""
                width: 180
                verticalAlignment: Text.AlignVCenter
            }

            Button {
                font.pixelSize: 15
                text: "手动添加坐标"
                onClicked: dialog.open()
            }
        }
    }

    MessageDialog {
        id: tip
        icon: StandardIcon.Warning
    }

    function error(str) {
        tip.text = str
        tip.open()
    }
}