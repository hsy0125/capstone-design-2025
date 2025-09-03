package com.capstone2025.aiassistant;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration; // ★ DB 자동설정 끔

@SpringBootApplication(exclude = { DataSourceAutoConfiguration.class }) // ★ DB 자동설정 끔
public class AiassistantApplication {

	public static void main(String[] args) {
		SpringApplication.run(AiassistantApplication.class, args);
	}

}
