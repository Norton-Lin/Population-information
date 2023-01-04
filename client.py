"""
 * @file client.py
 * @author LinZhi 2020211472
 * @brief
        人口数据查询系统客户端模块
        基于python、QT、QML实现
 * @version 0.1
 * @date 2022-12-23
 * @copyright Copyright (c) 2022
"""
import math
import sys
import requests
import logging
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from cartopy import crs, feature
from PyQt5.QtCore import QObject, pyqtProperty, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import QQmlApplicationEngine, QQmlListProperty


class Coordinate(QObject):
    def __init__(self, x: int, y: int, parent=None):
        super().__init__(parent)
        self.x = x
        self.y = y

    def __str__(self):
        return f"[{self.x},{self.y}]"

    @pyqtProperty(int, constant=True)
    def get_x_deg(self) -> int:
        return self.x // 3600

    @pyqtProperty(int, constant=True)
    def get_x_min(self) -> int:
        return self.x % 3600 // 60

    @pyqtProperty(int, constant=True)
    def get_x_sec(self) -> int:
        return self.x % 60

    @pyqtProperty(int, constant=True)
    def get_y_deg(self) -> int:
        return self.y // 3600

    @pyqtProperty(int, constant=True)
    def get_y_min(self) -> int:
        return self.y % 3600 // 60

    @pyqtProperty(int, constant=True)
    def get_y_sec(self) -> int:
        return self.y % 60


class Client(QObject):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.coordinates = []
        self.url = "http://127.0.0.1:8888/Query"

    coordinates_changed = pyqtSignal()

    @pyqtProperty(QQmlListProperty, notify=coordinates_changed)
    def get_coordinates(self) -> QQmlListProperty:
        return QQmlListProperty(Coordinate, self, self.coordinates)

    @pyqtSlot(int, int)
    def add_coordinate(self, x: int, y: int) -> None:
        self.coordinates.append(Coordinate(x, y))
        logging.info(f"Add coordinate lon: {x}, lat: {y}")
        self.coordinates_changed.emit()

    @pyqtSlot(int)
    def delete_coordinate(self, index: int) -> None:
        self.coordinates.pop(index)
        logging.info(f"delete coordinate index: {index}")
        self.coordinates_changed.emit()

    @pyqtSlot()
    def query(self) -> None:
        if len(self.coordinates) == 0:  # 消息为空
            return
        logging.info(f"Submit a query")
        req = requests.post(
            self.url,
            json={
                "type": "Polygon",
                "coordinates": [[it.x, it.y] for it in self.coordinates],
            },
        )
        if req.status_code == 406:
            root.error("坐标错误！查询范围应为凸多边形")
            return
        elif req.status_code != 200:
            root.error("服务器内部错误")
            return
        if len(req.json().get("response")) == 0:
            return
        data = np.array(req.json().get("response")).transpose((1, 0))
        extent = [
            math.floor(np.min(data[0]) / 3600),
            math.ceil(np.max(data[0]) / 3600),
            math.floor(np.min(data[1]) / 3600),
            math.ceil(np.max(data[1]) / 3600),
        ]  # 绘图范围
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection=crs.PlateCarree())
        ax.set_extent(extent, crs=crs.PlateCarree())  # 设置范围
        ax.add_feature(feature.LAND.with_scale("10m"))  # 图背景的陆地标识
        ax.add_feature(feature.COASTLINE.with_scale("10m"), lw=0.25)  # 图背景的海岸线标识
        ax.add_feature(feature.OCEAN.with_scale("10m"))  # 图背景的海洋标识
        ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
        norm = mpl.colors.LogNorm(vmin=1e0, vmax=1e7)
        im = ax.scatter(
            [i / 3600 for i in data[0]],
            [i / 3600 for i in data[1]],
            s=0.05,
            c=data[2],
            cmap="afmhot_r",
            norm=norm,
        )
        fig.colorbar(im, ax=ax)
        ax.title.set_text(
            f"Total population of the query area is {req.json().get('total'):.2f}"
        )
        plt.show()


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    client = Client()
    engine.rootContext().setContextProperty("client", client)
    engine.load("client.qml")
    root = engine.rootObjects()[0]
    app.exec()
