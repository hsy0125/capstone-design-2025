package com.capstone2025.aiassistant.service;

import java.util.List;
import java.util.Map;

import org.springframework.stereotype.Service;

import com.capstone2025.aiassistant.dto.ShopLinkResponse;
import com.capstone2025.aiassistant.dto.ShopOrderRequest;
import com.capstone2025.aiassistant.dto.ShopSearchResponse;

@Service
public class ShopService {

    //수정됨: 네이버 쇼핑 고정 URL
    private static final String NAVER_SHOPPING_URL = 
        "https://shopping.naver.com/ns/home?dtm_detail=main_text&dtm_source=naver_pcbs&dtm_medium=mktatrb_etc&dtm_campaign=2503-shopping-017&pcode=naver_pcbs_main_text&campaign_id=2503-shopping-017&channel_id=naver_pcbs&material=main_text&n_query=%EB%84%A4%EC%9D%B4%EB%B2%84%EC%87%BC%ED%95%91&NaPm=ct%3Dmf41k22q%7Cci%3DERdfcb9625-88cd-11f0-a82a-d6ecc9346497%7Ctr%3Dbrnd%7Chk%3De067bcbf122416ee3916c6fb5a87c6c1a4eda317%7Cnacn%3Dbp6bBswuZzCz";

    //수정됨: 어떤 item이 와도 네이버 쇼핑 링크로 통일
    public ShopLinkResponse recommend(String item) {
        return new ShopLinkResponse(
            "네이버 쇼핑 추천: " + item, //수정됨
            NAVER_SHOPPING_URL,        //수정됨
            "naver"                    //수정됨
        );
    }

    //수정됨: 검색 결과 더미도 모두 동일 링크 사용
    public ShopSearchResponse search(String item) {
        return new ShopSearchResponse(List.of(
            Map.of("title", "네이버 쇼핑 " + item + " A", "url", NAVER_SHOPPING_URL, "price", 39000),
            Map.of("title", "네이버 쇼핑 " + item + " B", "url", NAVER_SHOPPING_URL, "price", 49000),
            Map.of("title", "네이버 쇼핑 " + item + " C", "url", NAVER_SHOPPING_URL, "price", 59000)
        ));
    }

    //수정됨: 주문 더미 응답 문구만 조정
    public Map<String, String> order(ShopOrderRequest req) {
        return Map.of(
            "status", "ok",
            "message", "주문(더미)이 네이버 쇼핑 링크 기준으로 접수된 것으로 처리되었습니다." //수정됨
        );
    }
}