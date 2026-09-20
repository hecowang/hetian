#include <stdio.h>
#include <string.h>

#include "esp_event.h"
#include "esp_http_client.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_task_wdt.h"
#include "esp_wifi.h"
#include "nvs_flash.h"
#include "driver/uart.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/queue.h"
#include "freertos/task.h"

#include "telemetry.h"

#define UART_PORT UART_NUM_1
#define WIFI_READY BIT0
#define LINE_MAX 384

static const char *TAG = "hetian_edge";
static EventGroupHandle_t network_events;
static QueueHandle_t capture_queue;

static void wifi_event(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_START) esp_wifi_connect();
    else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        xEventGroupClearBits(network_events, WIFI_READY);
        esp_wifi_connect();
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        xEventGroupSetBits(network_events, WIFI_READY);
    }
}

static void wifi_init(void)
{
    network_events = xEventGroupCreate();
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t init = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&init));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, wifi_event, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_event, NULL));
    wifi_config_t cfg = {0};
    strlcpy((char *)cfg.sta.ssid, CONFIG_HETIAN_WIFI_SSID, sizeof(cfg.sta.ssid));
    strlcpy((char *)cfg.sta.password, CONFIG_HETIAN_WIFI_PASSWORD, sizeof(cfg.sta.password));
    cfg.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &cfg));
    ESP_ERROR_CHECK(esp_wifi_start());
}

static void uart_init(void)
{
    const uart_config_t cfg = {
        .baud_rate = CONFIG_HETIAN_UART_BAUD,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    ESP_ERROR_CHECK(uart_driver_install(UART_PORT, 2048, 0, 0, NULL, 0));
    ESP_ERROR_CHECK(uart_param_config(UART_PORT, &cfg));
    ESP_ERROR_CHECK(uart_set_pin(UART_PORT, CONFIG_HETIAN_UART_TX_GPIO,
                                 CONFIG_HETIAN_UART_RX_GPIO,
                                 UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
}

static void telemetry_task(void *arg)
{
    char line[LINE_MAX];
    size_t used = 0;
    uint8_t byte;
    while (true) {
        int n = uart_read_bytes(UART_PORT, &byte, 1, pdMS_TO_TICKS(250));
        if (n <= 0) continue;
        if (byte == '\n') {
            line[used] = '\0';
            flight_telemetry_t sample;
            if (telemetry_parse_line(line, &sample) && sample.armed && sample.capture) {
                if (xQueueSend(capture_queue, &sample, 0) != pdTRUE)
                    ESP_LOGW(TAG, "capture queue full; keeping flight control isolated");
            }
            used = 0;
        } else if (byte != '\r') {
            if (used < sizeof(line) - 1) line[used++] = (char)byte;
            else used = 0;
        }
    }
}

static esp_err_t post_capture_event(const flight_telemetry_t *sample)
{
    char json[512];
    snprintf(json, sizeof(json),
             "{\"device_id\":\"%s\",\"event\":\"capture_requested\","
             "\"place_id\":\"%s\",\"lat\":%.7f,\"lon\":%.7f,"
             "\"altitude_m\":%.2f,\"battery_percent\":%u}",
             CONFIG_HETIAN_DEVICE_ID, sample->place_id, sample->latitude,
             sample->longitude, sample->altitude_m, sample->battery_percent);
    esp_http_client_config_t cfg = {
        .url = CONFIG_HETIAN_API_URL,
        .method = HTTP_METHOD_POST,
        .timeout_ms = 10000,
    };
    esp_http_client_handle_t client = esp_http_client_init(&cfg);
    esp_http_client_set_header(client, "Content-Type", "application/json");
    esp_http_client_set_post_field(client, json, strlen(json));
    esp_err_t err = esp_http_client_perform(client);
    int status = err == ESP_OK ? esp_http_client_get_status_code(client) : 0;
    esp_http_client_cleanup(client);
    return err == ESP_OK && status >= 200 && status < 300 ? ESP_OK : ESP_FAIL;
}

static void capture_task(void *arg)
{
    flight_telemetry_t sample;
    while (xQueueReceive(capture_queue, &sample, portMAX_DELAY) == pdTRUE) {
        ESP_LOGI(TAG, "capture point=%s alt=%.1fm battery=%u%%",
                 sample.place_id, sample.altitude_m, sample.battery_percent);
        xEventGroupWaitBits(network_events, WIFI_READY, pdFALSE, pdTRUE, portMAX_DELAY);
        int backoff_seconds = 1;
        for (int attempt = 0; attempt < 5; ++attempt) {
            if (post_capture_event(&sample) == ESP_OK) break;
            vTaskDelay(pdMS_TO_TICKS(backoff_seconds * 1000));
            backoff_seconds *= 2;
        }
    }
}

void app_main(void)
{
    esp_err_t nvs = nvs_flash_init();
    if (nvs == ESP_ERR_NVS_NO_FREE_PAGES || nvs == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
    } else ESP_ERROR_CHECK(nvs);

    capture_queue = xQueueCreate(8, sizeof(flight_telemetry_t));
    configASSERT(capture_queue);
    wifi_init();
    uart_init();
    xTaskCreate(telemetry_task, "flight_rx", 4096, NULL, 12, NULL);
    xTaskCreate(capture_task, "capture", 6144, NULL, 8, NULL);
    ESP_LOGI(TAG, "Hometown Keeper edge module started");
}
