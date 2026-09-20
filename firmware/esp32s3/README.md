# ESP32-S3 故乡模组固件

ESP-IDF 5.3+ 原型。当前代码实现：

- UART 接收飞控遥测（开发阶段使用一行一个 JSON 的适配协议）。
- 仅在飞控已解锁且到达观察点时生成拍摄事件。
- FreeRTOS 队列隔离飞控接收与网络上报。
- Wi-Fi 重连、HTTPS JSON 上报、指数退避。
- NVS 保存设备配置；任务看门狗防止模组无响应。

相机和 MicroSD 驱动在下一硬件里程碑接入。当前 `capture_task` 生成元数据事件，接口已经为实际 JPEG 路径预留。

## 构建

```bash
cd firmware/esp32s3
idf.py set-target esp32s3
idf.py menuconfig
idf.py build
idf.py -p /dev/cu.usbmodemXXXX flash monitor
```

在 `Hometown Keeper` 菜单配置：Wi-Fi、服务端 URL、设备 ID、UART GPIO。生产环境不要把 Wi-Fi 密码或令牌提交进仓库；使用量产烧录或安全配置流程。

## 开发遥测协议

每行一个 JSON，由 USB-UART 或飞控适配器发送：

```json
{"armed":true,"lat":31.352,"lon":118.433,"alt_m":42.0,"battery":78,"place_id":"old-house","capture":true}
```

`capture=true` 只表示到达由飞控确认的拍摄点。正式版本会用 MAVLink 2 消息和任务序号替换这个适配层。
