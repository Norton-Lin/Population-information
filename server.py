"""
 * @file server.py
 * @author LinZhi 2020211472
 * @brief
        人口数据查询系统服务端模块
        基于Sanic实现
 * @version 0.1
 * @date 2022-12-23
 * @copyright Copyright (c) 2022
"""

import asyncio
import math
import os
import logging
import numpy as np
from sanic import Sanic, json
from shapely import geometry
from shapely.errors import TopologicalError

app = Sanic("Population_Count")


@app.listener("before_server_start")
async def init_server(loop):
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    step = 10  # 将所有的块划分为10°*10°的小块进行处理，原大小为90°*90°
    start = 0
    stop = 90
    factor = 120
    for i in range(1, 9):
        with open(
            f"./gpw-v4-population-count-rev11_2020_30_sec_asc/gpw_v4_population_count_rev11_2020_30_sec_{i}.asc"
        ) as f:
            f.readline()
            f.readline()
            #   记录经度
            lon = int(float(f.readline().split()[1]))
            #   记录纬度
            lat = int(float(f.readline().split()[1])) + 90
            #   检查一个文件中所有块是否预处理完毕
            finished = True
            for lon_offset in range(start, stop, step):
                for lat_offset in range(start, stop, step):
                    if not os.path.exists(
                        f"./data/lon_{lon + lon_offset}_lat_{lat - lat_offset}.npy"
                    ):
                        finished = False
                        break
                if not finished:
                    break
            if finished:
                continue
            data = np.genfromtxt(
                f"./gpw-v4-population-count-rev11_2020_30_sec_asc/gpw_v4_population_count_rev11_2020_30_sec_{i}.asc",
                skip_header=6,
            )
            data[data == -9999] = np.nan  # 无效数据处理
            for lon_offset in range(start, stop, step):
                for lat_offset in range(start, stop, step):
                    if not os.path.exists(
                        f"./data/lon_{lon + lon_offset}_lat_{lat - lat_offset}.npy"
                    ):
                        np.save(
                            f"./data/lon_{lon + lon_offset}_lat_{lat - lat_offset}.npy",
                            data[
                                lat_offset * factor : (lat_offset + step) * factor,
                                lon_offset * factor : (lon_offset + step) * factor,
                            ],
                        )


@app.post("/Query")
async def Query(request):
    """

    :param request: 参数 GeoJson格式，多边形参数以角秒为单位传递
    :return:
    """
    try:
        param = request.json.get("coordinates")
        polygon = geometry.Polygon(param)
        lon_min, lat_min, lon_max, lat_max = polygon.bounds
        step = 10
        factor = 60 * 60
        unit = 30
        response = []
        total = 0
        tasks = []
        # 计算分块信息
        lon_min = math.floor(lon_min / factor / step) * step
        lat_min = math.floor(lat_min / factor / step) * step
        lon_max = math.ceil(lon_max / factor / step) * step
        lat_max = math.ceil(lat_max / factor / step) * step
        #   找到块
        for i in range(lon_min, lon_max, step):
            for j in range(lat_max, lat_min, -step):
                logging.info(f"Query block lon:{i},lat:{j}")
                tasks.append(
                    asyncio.create_task(get_message(i, j, polygon, step, factor, unit))
                )
        for task in tasks:
            first, second = await task
            response += first
            total += second
        return json({"response": response, "total": total})
    except KeyError:
        return json({}, status=400)
    except (ValueError, TopologicalError):
        return json({}, status=406)


async def get_message(lon, lat, polygon, step, factor, unit):
    """
    :param unit:
    :param lon: 经度
    :param lat: 纬度
    :param polygon: 多边形参数
    :param step: 经纬度块间距
    :param factor: 放缩因子 格-角秒
    :return: 坐标序列与人数
    """
    #   此时是角秒单位，而块单元以30角秒为单位
    lon_min, lat_min, lon_max, lat_max = polygon.bounds
    data = np.load(f"./data/lon_{lon}_lat_{lat}.npy")
    response = []
    total = 0
    lon_min = max(math.floor(lon_min / unit) * unit, lon * factor)
    lat_min = max(math.floor(lat_min / unit) * unit, (lat - step) * factor)
    lon_max = min(math.ceil(lon_max / unit) * unit, (lon + step) * factor)
    lat_max = min(math.ceil(lat_max / unit) * unit, lat * factor)
    for i in range(lon_min, lon_max, unit):
        for j in range(lat_max, lat_min, -unit):
            cell_polygon = geometry.Polygon(
                ((i, j), (i + unit, j), (i + unit, j - unit), (i, j - unit))
            ).intersection(
                polygon
            )  # 该cell和多边形的重合部分
            if cell_polygon.area > 0:  # 如果有重合
                x = int((lat * factor - j) / unit)
                y = int((i - lon * factor) / unit)
                response.append((i, j, cell_polygon.area / (unit * unit) * data[x, y]))
                if not np.isnan(response[-1][2]):
                    total += response[-1][2]
    return response, total


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8888)
