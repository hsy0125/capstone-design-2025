package com.capstone2025.aiassistant.dto;

public record ShopOrderRequest(
        String itemId,
        Integer qty,
        String addr
) {}