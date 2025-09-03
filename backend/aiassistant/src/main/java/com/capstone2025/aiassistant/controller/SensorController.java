// src/main/java/com/capstone2025/aiassistant/controller/SensorController.java
package com.capstone2025.aiassistant.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.capstone2025.aiassistant.dto.Co2Response;
import com.capstone2025.aiassistant.service.SensorService;

import lombok.RequiredArgsConstructor; //수정됨

@RestController
@RequestMapping("/sensors")
@RequiredArgsConstructor //수정됨: final 필드용 생성자 자동 생성
public class SensorController {

    private final SensorService sensorService; //수정됨

    @GetMapping("/co2")
    public Co2Response co2() {
        return sensorService.readCo2Once();
    }
}
