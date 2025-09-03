package com.capstone2025.aiassistant.service;

import java.util.concurrent.ThreadLocalRandom;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.capstone2025.aiassistant.dto.Co2Response;

@Service
public class SensorService {

    @Value("${co2.thresholds.normal:800}")
    private int normalMax;

    @Value("${co2.thresholds.warning:1200}")
    private int warningMax;

    // TODO: 실제 센서 연결 시 이 메서드를 교체하거나 분리(Serial/Driver/HTTP 등)
    public Co2Response readCo2Once() {
        // 더미: 600~1400 사이 랜덤
        double ppm = ThreadLocalRandom.current().nextDouble(600, 1400);
        Double temp = 24.5;
        Double rh = 45.0;
        return Co2Response.of(ppm, temp, rh, normalMax, warningMax);
    }
}