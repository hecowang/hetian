#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    bool armed;
    bool capture;
    double latitude;
    double longitude;
    float altitude_m;
    uint8_t battery_percent;
    char place_id[48];
} flight_telemetry_t;

bool telemetry_parse_line(const char *line, flight_telemetry_t *out);
