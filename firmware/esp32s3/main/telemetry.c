#include "telemetry.h"

#include <string.h>
#include "cJSON.h"

bool telemetry_parse_line(const char *line, flight_telemetry_t *out)
{
    if (line == NULL || out == NULL) return false;
    cJSON *root = cJSON_Parse(line);
    if (root == NULL) return false;

    const cJSON *armed = cJSON_GetObjectItemCaseSensitive(root, "armed");
    const cJSON *capture = cJSON_GetObjectItemCaseSensitive(root, "capture");
    const cJSON *lat = cJSON_GetObjectItemCaseSensitive(root, "lat");
    const cJSON *lon = cJSON_GetObjectItemCaseSensitive(root, "lon");
    const cJSON *alt = cJSON_GetObjectItemCaseSensitive(root, "alt_m");
    const cJSON *battery = cJSON_GetObjectItemCaseSensitive(root, "battery");
    const cJSON *place = cJSON_GetObjectItemCaseSensitive(root, "place_id");

    bool valid = cJSON_IsBool(armed) && cJSON_IsBool(capture) &&
                 cJSON_IsNumber(lat) && cJSON_IsNumber(lon) &&
                 cJSON_IsNumber(alt) && cJSON_IsNumber(battery) &&
                 cJSON_IsString(place) && place->valuestring[0] != '\0';
    if (valid) {
        memset(out, 0, sizeof(*out));
        out->armed = cJSON_IsTrue(armed);
        out->capture = cJSON_IsTrue(capture);
        out->latitude = lat->valuedouble;
        out->longitude = lon->valuedouble;
        out->altitude_m = (float)alt->valuedouble;
        int pct = battery->valueint;
        out->battery_percent = (uint8_t)(pct < 0 ? 0 : pct > 100 ? 100 : pct);
        strlcpy(out->place_id, place->valuestring, sizeof(out->place_id));
    }
    cJSON_Delete(root);
    return valid;
}
