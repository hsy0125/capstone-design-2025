package com.capstone2025.aiassistant.dto;

import java.util.List;
import java.util.Map;

public record ShopSearchResponse(
        List<Map<String, Object>> items
) {}