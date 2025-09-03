package com.capstone2025.aiassistant.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.capstone2025.aiassistant.dto.ShopLinkResponse;
import com.capstone2025.aiassistant.dto.ShopOrderRequest;
import com.capstone2025.aiassistant.dto.ShopSearchResponse;
import com.capstone2025.aiassistant.service.ShopService;

import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/shop")
@RequiredArgsConstructor //수정됨
public class ShopController {

    private final ShopService shopService; //수정됨

    // 추천 링크 1개
    @GetMapping("/recommend")
    public ShopLinkResponse recommend(@RequestParam String item) {
        return shopService.recommend(item);
    }

    // 카드 리스트(더미)
    @GetMapping("/search")
    public ShopSearchResponse search(@RequestParam String item) {
        return shopService.search(item);
    }

    // 주문(더미)
    @PostMapping("/order")
    public Object order(@RequestBody ShopOrderRequest request) {
        return shopService.order(request);
    }
}