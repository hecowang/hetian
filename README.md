# 故乡守望 · Hometown Keeper

> 为长期在外生活的人，保存一个持续变化的故乡。

这不是农业巡检产品，而是一套“远程故乡陪伴”系统：无人机沿固定航线定期拍摄田野、老房子、树、村口和河流，形成长期影像档案；AI 负责筛选、变化检测、目标计数和“故乡日报”。

## MVP 闭环

1. 无人机或模拟器创建一次固定航线任务。
2. 按相同观察点上传照片和遥测信息。
3. Web 端按时间轴浏览故乡。
4. 选择同一观察点的两次记录进行前后对比。
5. AI 分析器生成变化摘要；当前内置可运行的演示分析器，后续可替换为 VLM/YOLO。

## 快速开始

需要 Python 3.11+。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

打开 <http://127.0.0.1:8000>。另一个终端运行：

```bash
python scripts/simulate_flight.py
```

## API

- `POST /api/missions`：创建巡飞任务
- `POST /api/observations`：上报观察记录与照片
- `GET /api/timeline`：获取时间轴
- `GET /api/places/{place_id}/compare`：同地点前后对比
- `GET /api/digest/latest`：最新“故乡日报”
- `GET /healthz`：健康检查

交互式文档位于 `/docs`。

## 产品路线

| 阶段 | 能力 | 主要硬件 |
|---|---|---|
| P0 演示 | 模拟航线、上传、时间轴、前后对比、摘要 | 本仓库即可运行 |
| P1 飞起来 | 自动航点巡飞、拍照、返航、人工换电 | PX4/ArduPilot + GPS + 相机 |
| P2 可远程 | 4G 遥测与上传、断点续传、边缘压缩 | RK3566/RK3588 + 4G |
| P3 可长期 | 无人机机场、自动充电、RTK 精准降落 | Dock + RTK + 气象站 |

真实飞行前必须遵守当地空域、实名登记、飞行许可、隐私与数据合规要求；MVP 推荐先在自有/获授权场地进行人工监护测试。

## 目录

```text
app/                 FastAPI 服务与 Web 页面
docs/                产品和设备接入设计
scripts/             巡飞模拟器
firmware/esp32s3/     ESP32-S3 智能伴随模组固件
tests/               API 测试
data/                 本地运行数据（不入库）
```

硬件首版建议使用“Pixhawk 飞控 + ESP32-S3 N16R8 伴随模组”，详见
[`docs/HARDWARE.md`](docs/HARDWARE.md)。ESP32-S3 固件的构建和烧录说明位于
[`firmware/esp32s3/README.md`](firmware/esp32s3/README.md)。

- [硬件连接示意图](docs/assets/hardware-connection.svg)
- [产品原型图与页面说明](docs/PROTOTYPE.md)

## License

Apache-2.0
