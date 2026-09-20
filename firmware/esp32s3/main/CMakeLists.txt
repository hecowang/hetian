idf_component_register(SRCS "main.c" "telemetry.c"
                       INCLUDE_DIRS "."
                       REQUIRES esp_wifi esp_event esp_netif nvs_flash esp_http_client json driver esp_timer)
