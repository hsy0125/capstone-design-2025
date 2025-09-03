package com.capstone2025.aiassistant.dto;

import java.time.Instant;
import java.util.Map;

// Co2 센서 - 뼈대 구축(임시)

public record Co2Response(
        double ppm,
        String ts,                // ISO-8601
        String state,             // normal | warning | alert
        Double temp,              // optional
        Double rh,                // optional
        Map<String, Integer> thresholds // optional
) {
    public static Co2Response of(double ppm, Double temp, Double rh, int normal, int warning) {
        String state = ppm < normal ? "normal" : (ppm < warning ? "warning" : "alert");
        return new Co2Response(
                ppm,
                Instant.now().toString(),
                state,
                temp,
                rh,
                Map.of("normal", normal, "warning", warning)
        );
    }
}