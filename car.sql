DROP TABLE IF EXISTS vehicles CASCADE;
CREATE TABLE vehicles (
    vehicle_id SERIAL PRIMARY KEY,   -- 고유아이디
    model_name VARCHAR(50) NOT NULL, -- 모델명
    year INT,                        -- 연식
    engine_type VARCHAR(50),         -- 엔진타입  (2종류)
    fuel_type VARCHAR(50),           -- 연료 종류 (엔진타입에 따라 달라짐)
    fuel_capacity VARCHAR(50),       -- 연료 용량 (엔진타입에 따라 달라짐)
    engine_oil VARCHAR(50),          -- 엔진 오일 (엔진타입에 따라 달라짐)
    coolant VARCHAR(50),             -- 냉각수 종류 (냉각수 용량 추가?)
    brake_fluid VARCHAR(50),         -- 브레이크 오일 규격
    tire_type VARCHAR(50),           -- 타이어규격 (에너지소비 효율 등급기준 높은거우선)
    recommended_tire_pressure VARCHAR(50),  -- 추천 공기앞
    wheel_size VARCHAR(50)           -- 휠사이즈
);

DROP TABLE IF EXISTS warning_lights CASCADE;  --경고등 에러
CREATE TABLE warning_lights (
    warning_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES vehicles(vehicle_id),
    warning_name VARCHAR(100),
    warning_desc TEXT,
    solution TEXT
);

DROP TABLE IF EXISTS em ergency_tips CASCADE;   -- 비상상황 응급조치
CREATE TABLE emergency_tips (
    tip_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES vehicles(vehicle_id),
    situation VARCHAR(500)
);

drop table if exists emergency_steps cascade;   -- 응급조치내용
CREATE TABLE emergency_steps (
    step_id SERIAL PRIMARY KEY,
    tip_id INT REFERENCES emergency_tips(tip_id) ON DELETE CASCADE,
    step_order INT,  -- 순서 지정
    step_desc TEXT   -- 단계별 설명
);

DROP TABLE IF EXISTS maintenance_guide CASCADE;  -- 유지보수 가이드
CREATE TABLE maintenance_guide (
    id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES vehicles(vehicle_id),
    item_name TEXT,     -- 항목이름
    action_type TEXT, -- '점검' or '교체'
    interval_km INTEGER,    --거리기준
    interval_month INTEGER,   -- 기간 기준
    note TEXT
);

DROP TABLE IF EXISTS sensor_events CASCADE;     --센서이벤트
CREATE TABLE sensor_events (
    event_id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES vehicles(vehicle_id),
    sensor_type VARCHAR(50),
    threshold FLOAT,
    event_message TEXT
);

INSERT INTO vehicles(model_name, year, engine_type,
                     fuel_type, fuel_capacity, engine_oil, coolant,
                     brake_fluid, tire_type, recommended_tire_pressure, wheel_size)
VALUES ('아반떼', 2025, 'Smartstream G1.6', '가솔린', '47L',
        'API SP 또는 ILSAC GF-6', '알루미늄 라디에이터용 인산염계 에틸렌 글리콜 부동액과 물 혼합액',
        'DOT-4*3', '195/65 R15 91H','앞:235(34), 뒤:215(31)','6.0Jx15');


INSERT INTO warning_lights(vehicle_id ,warning_name, warning_desc, solution)
VALUES ('1', '안전벨트 미착용 경고등', '안전벨트 경고등은 안전벨트를 착용하지 않은 상태에서 시동 ON되거나, 시동 ON 상태에서 안전벨트를' ||
        '풀면 6초 동안 경고음이 울리고 계속 경고등은 켜지고, 시속 20 km/h 이상이면 경고등이 깜박이면서 경고음도 함께 작동됩니다',
        '안전벨트 착용 확인' ),
       ('1', '에어백 경고등', ' 시동을 ON 하면, 경고등이 약 6초 동안 켜진 후 에어백 및 프리텐셔너 시트벨트 장치에 이상이 없으면 꺼집니다.' ||
        '시동을 ON 한 후 6초 동안 경고등이 켜지지 않거나, 6초 후에도 경고등이 꺼지지 않거나 주행 중에 경고등이 켜지면 에어백 및 프리텐셔너 시트벨트 장치에 이상이 있습니다',
        '당사 직영 하이테크센터나 블루핸즈에서 점검과 정비를 받으십시오.'),
       ('1', '브레이크 경고등', '주차 브레이크가 작동하거나 브레이크액이 부족할 때경고등이 켜집니다.',
        '브레이크액의 양을 점검한 후 부족하면 보충하십시오. 보충 후에도 브레이크 경고등이 계속 켜져 있을 경우에는 당사 직영 하이테크센터나 블루핸즈에서 점검을 받으십시오.'),
       ('1', 'ABS 경고등', '시동을 ON 하면 약 3초 동안 켜졌다가 꺼집니다. 3초 후에도 계속 경고등이 켜져 있으면 ABS 장치에 이상이 있습니다 ',
        '당사 직영 하이테크센터나 블루핸즈에서 점검과 정비를 받으십시오.'),
       ('1', 'EBD 경고등', '제동력의 전·후륜 배분 기능(EBD)도 작동하지 않기 때문에 급제동을 할 때 차가 불안정할 수 있습니다.',
        '당사 직영 하이테크센터나 블루핸즈에서 점검과 정비를 받으십시오.'),
       ('1', '전동 파워 스티어링 경고등', '시동을 ''ON'' 하면 약 3초 동안 켜졌다가 꺼집니다. 3초 후에도 계속 경고등이 켜져 있거나 ' ||
        '깜빡이면 전동 파워 스티어링 시스템에 이상', '당사 직영 하이테크센터나 블루핸즈에서 점검과 정비를 받으십시오.'),
       ('1', '연료부족 경고등', '연료의 잔류량이 적을 때 경고등이 켜집니다. 차량에 적용된 사양에 따라 팝업 메시지가 뜨고 연료 ' ||
        '경고등 색상이 흰색에서 노란색으로 변경됩니다.', '연료를 보충하십시오'),
       ('1', '과충전 경고등(LPG차량)', 'LPG 차량은 주유 시 LPG가 과충전되었을 경우 LPG 과충전 경고등이 빨간색으로 켜집니다.' ||
        '(85 % 충전 시 자동 차단됨, 과충전 방지 장치)','당사 직영 하이테크센터나 블루핸즈에서 점검과 정비를 받으십시오'),
       ('1','엔진 오일 압력 경고등', '엔진 오일이 부족하여 유압이 낮아지면 켜집니다.',
        '차를 안전하게 정차하고 엔진 오일양을 점검한 후 부족하면 보충하십시오.' ||
        '보충 후에도 경고등이 꺼지지 않으면 당사 직영 하이테크센터나 블루핸즈에서 점검을 받으십시오'),
       ('1','엔진 경고등', '시동을 ON 하면 약 3초 동안 켜졌다가 꺼집니다. 3초 후에도 계속 경고등이 켜져 있으면 엔진 제어장치, ' ||
        '연료 공급 장치 등에 이상이 있는 것입니다.', ' 당사 직영 하이테크센터나 블루핸즈에서 점검과 정비를 받으십시오. ' ||
        '또한, 일부 엔진 제어 장치에 이상이 있으면 시동이 걸리 않을 수도 있으니 이때에는 견인하십시오.'),
       ('1', '충전 경고등','드라이브 벨트가 끊어졌거나 충전 장치에 이상이 있을 때 경고등이 켜집니다',
        ' 배터리 충전 상태를 확인하고 드라이브 벨트나 충전 계통을 점검하십시오. 점검한 후에도 경고등이 꺼지지 않을 경우에는 ' ||
        '당사 직영 하이테크센터나 블루핸즈에서 점검을 받으 십시오'),
       ('1', '저압 타이어 경고등/TPMS 경고등', '시동을 ''ON'' 하면 약 3초 동안 켜졌다가 꺼집니다. ' ||
        '만약 경고등이 켜지지 않거나 일정 시간(약 1분) 깜빡인 후 켜지면 타이어 공기압 감지 시스템에 이상이 있는 것 입니다',
        ' 당사 직영 하이테크센터나 블루핸즈에서 점검을 받으십시오.'),
       ('1','전자식 파킹 브레이크(EPM) 경고등','저자식 파킹 브레이크 에 이상이 있으면 경고등이 켜집니다',
        '당사 짇영 하이테크센터나 블루핸즈에서 점검과 정비를 받으십시오.'),
       ('1','자동 정차 기능(AUTO HOLD) 표시등', '자동 정차 기능 상태에 따라 표시등 색상은 변경됩니다.' ||
        '• 흰색 : AUTO HOLD 버튼을 눌러 기능이 켜졌을 때 (준비 상태)' ||
        '• 녹색 : 주행 중에 브레이크 페달을 밟아 차량이 멈추면서 자동 정차 기능이 작동할 때 (다시 차량이 출발하면 흰색으로 변경됨)' ||
        '• 황색 : 자동 정차 기능에 이상이 있을 때', '황색일 경우 당사 직영 하이테크 센터나 블루핸즈에서 점검과 정비를 받으십시오.'),
       ('1', '전방 안전 경고등', '전방 충돌방지 보조의 전방 안전 기능의 상태에 따라 경고등 색상이 변경됩니다.' ||
        '• 시동을 ''ON'' 하면 주황색 경고등이 약 3초 동안 켜졌다가 꺼집니다.' ||
        '• 주황색: 전방 안전 미설정 또는 전방 충돌방지 보조 기능 이상/고장인 경우 계속 경고등이 켜집니다.' ||
        '• 빨간색: 전방 충돌방지 보조의 전방 안전 기능이 작동할 때 깜빡입니다.',
        '전방 안전 설정 후 센서 앞의 이물질을 제거해도 계속 경고등이 켜져 있으면, 당사 직영 하이테크 센터나 블루핸즈에서 점검을 받으십시오.'),
       ('1', '차로 안전 경고등', '차로 이탈 방지 보조의 상태에 따라 다음 색상의 차로 안전 경고등이 켜집니다.' ||
        '• 시동을 ''ON'' 하면 주황색 경고등이 약 3초 동안 켜졌다가 꺼집니다.' ||
        '• 회색: 준비 상태가 되면 회색으로 켜집니다.' ||
        '• 초록색: 작동할 수 있는 상태가 되면 초록색으로 켜집니다.' ||
        '• 초록색 깜빡임: 차로 이탈 방지 보조가 작동할 때 켜집니다.' ||
        '• 주황색: 차로 안전 미설정 또는 기능에 이상이 있는 경우 계속 경고등이 켜집니다. ',
        '차로 안전 설정 후 전방 카메라 앞의 이물질을 제거하여도 계속 경고등이 켜져 있으면, 당사 직영 하이테크센터나 블루핸즈에서 점검을 받으십시오'),
       ('1','부주의 운전 경고등', '운전자 주의 경고의 상태에 따라 표시등 색상이 변경됩니다.' ||
        '• 시동을 ''ON'' 하면 주황색 경고등이 약 3초 동안 켜졌다가 꺼집니다.' ||
        '• 주황색 켜짐: 전방 카메라 가림 또는 운전자 주의 경고 기능 이상/고장인 경우 계속 경고등이 켜집니다.' ||
        '• 주황색 깜빡임: 운전자의 휴식을 권유할 때 깜빡입니다.',
        '전방 카메라 앞의 이물질을 제거해도 경고등이 계속 켜져 있으면, 당사 직영 하이테크센터나 블루핸즈에서 점검과 정비를 받으십시오.'),
       ('1', '도로 결빙 경고등', '외기 온도가 약 4 ℃ 이하일 때 외기 온도 표시 및 결빙 경고등이 깜빡인 후 켜집니다.' ||
        '이때, 경고음도 1회 울립니다.',
        '사용자 설정 모드에서 도로 결빙 경고등 알림을 설정 또는 해제할 수 있습니다 (사용자 설정 → 편의 → 도로 결빙 알림 → 설정/해제).'),
       ('1','통합 경고등','통합 경고등은 차량 관련 경고가 필요한 상황이 1가지 이상 발생하면 켜집니다.' ||
                     '통합 경고등이 경고하는 상황은' ||
                     '• 전방 충돌방지 보조 고장' ||
                     '• 전방 충돌방지 보조 카메라 또는 레이더 가림' ||
                     '• 후측방 충돌방지 보조 고장' ||
                     '• 후측방 충돌방지 보조 레이더 가림' ||
                     '• 지능형 속도 제한 보조 고장' ||
                     '• 지능형 속도 제한 보조 카메라 가림' ||
                     '• LED 전조등 고장' ||
                     '• 하이빔 보조 고장' ||
                     '• 스마트 크루즈 컨트롤 고장' ||
                     '• 스마트 크루즈 컨트롤 레이더 가림' ||
                     '등이며, 차량 사양에 따라 표시되는 경고 상황은 달라질 수 있습니다','경고 상황이 해제되면 통합 경고등은 꺼집니다. '),
       ('1', '차체자세 제어장치 (ESC) 작동 표시등', '시동을 ''ON'' 하면 표시등이 켜지고 ESC 장치에 이상이 없으면 약 3초 후에 꺼집니다.' ||
        '운전 중에 ESC가 작동할 때는 작동하는 동안 깜빡입니다. 단, 작동 표시등이 꺼지지 않고 계속 켜지거나 주행 중에 켜질 경우 ESC 장치에 이상이 있는 것 입니다.',
        '당사 직영 하이테크센터나 블루핸즈에서 점검을 받으십시오.'),
       ('1', '키 확인 표시등 (스마트 키 장착 차량)', '스마트 키가 차 안에 있을 경우에 시동 버튼 ACC 또는 ON 상태에서는' ||
        '표시등이 수초 동안 켜져 시동을 걸 수 있음을 알려 줍니다.' ||
        '그러나 스마트 키가 차 안에 없을 경우에는 시동 버튼을 누르면 표시등이 수초 동안 깜빡이며 시동을 걸 수 없음을 알려 줍니다. 이때는 시동이 걸리지 않습니다.',''),
       ('1', '비상 경고등/ 방향지시등', '방향지시등과 비상 경고등이 깜빡이는 횟수가 이상하게 빠르거나 늦을 때는' ||
        '이상이 있을 수 있습니다', '전구의 단선이나 접지 불량일 수 있으므로 점검하십시오.'),
       ('1', '외장램프 단선 표시등', '외장램프에 이상이 있으면 표시등이 켜지며 관련 부품에 이상이 있으면 표시등이 깜빡입니다.',
        '당사 직영 하이테크센터나 블루핸즈에서 점검을 받으 십시오.'),
       ('1', 'LED 전조등 고장', '시동을 ON하면 약 3초 동안 켜졌다가 꺼집니다.' ||
        'LED 전조등에 이상이 있으면 표시등이 켜지며 관련부품에 이상이 있으면 표시등이 깜빡입니다.', '당사 직영 하이테크센터나 블루핸즈에서 점검을 받으 십시오.');

insert into emergency_tips(vehicle_id, situation)
values ('1','사고 또는 고장 시 행동 요령'),
       ('1','교차로/건널목에서 시동이 꺼진경우'),
       ('1','주행 중 펑크가 날 경우'),
       ('1','주행 중 시동이 꺼진 경우'),
       ('1','브레이크 제동력이 좋지 않을 경우'),
       ('1','주행 중 차량이 고장 난 경우'),
       ('1','시동 모터가 회전하지 않을 경우'),
       ('1','시동 모터는 회전하지만 시동이 걸리지 않을 경우'),
       ('1','비상시동(점프스타트)'),
       ('1','엔진과열'),
       ('1','타이어 응급 처치 키트'),
       ('1','차량 견인'),
       ('1','차량 화재 시'),
       ('1','폭설시 행동 요령');

insert into emergency_steps(tip_id, step_order, step_desc)
values('1','1','신속히 비상 경고등을 켜고 차량은 갓길로 이동하십시오.'),
      ('1','2','차량 뒤에 안전삼각대를 설치하십시오.'),
      ('1','3','운전자와 탑승자는 가드레일 밖 등 안전지대로 대피하십시오.'),
      ('1','4','경찰서(112), 소방서(119) 또는 한국도로공사(1588-2504)로 연락하여 도움을 받으십시오'),
      ('2','1','기어를 N(중립) 상태로 둡니다.'),
      ('2','2', '주위 사람들의 도움을받아 안전한장소까지 차를 밀어 이동시킵니다.'),
      ('3','1','비상 경고등을 켜고 스티어링 휠을 꼭 잡고 차를 도로 가장자리로 이동시키십시오.'),
      ('3','2','이때 차량의 솓고를 낮추기 위해서 브레이크 페달보다는 엔진 브레이크를 이용하십시오.'),
      ('3','3','속도가 떨어지면 가볍게 브레이크 페달을 밟아 정지하십시오.'),
      ('3','4','될 수 있으면 경사가 없는 평평한 장소에 차량을 정차시키고 타이어 응큽 처치 키트를 이용하여 타이어를 수리합니다.'),
      ('3','5', '주차 브레이크를 확실히 걸고 펑크 난 타이어의 대각선에 위치한 타이어 앞/뒤에 고임목을 받치십시오.'),
      ('4','1', '차량을 안전한 곳으로 이동하십시오'),
      ('4','2', '브레이크 작동 상태가 나빠지므로 평상시보다 브레이크 페달을 세게 밟으십시오.'),
      ('4','3', '파워 스티어링 장치가 작동하지 않아 스티어링 휠 조작력이 매우 무거워지므로 평소보다 강하게 돌리십시오'),
      ('5','1', '브레이크 페달을 완전히 밟고, 엔진 브레이크(기어 저단 변속)와 주차 브레이크를 함께 시영하여 속도를 줄여 안전한 장소에 정차한십시오.'),
      ('6','1', '도로변에 정차한 후 비상 경고등을 켜서 2차 사고를 방지하십시오.'),
      ('6','2', '고속도로나 자통차 전용 도로에서는 안전 삼각대를 차량 뒤편에 설치 하십시오.'),
      ('6','3', '직접 고장 난 곳을 점검하고 수리할 수 있는 경우, 다른 차량 통행에 주의하여 작업하십시오.'),
      ('7','1', '배터리가 방전되거나 배터리 단자의 연결 상태를 점검하십시오.'),
      ('7','2', '기어가 P(주차) 또는 N(중립) 상태인지 확인하십시오.'),
      ('8','1', '연료량을 점검하십시오.'),
      ('8','2', '계속해서 시동이 걸리지 않을 때는 긴급출동지원센터로 연학하여 응급조치를 받으십시오.'),
      ('9','1', '반드시 12V 배터리를 사용하여 점프 스타트 하십시오. 전압이 다른 배터리를 사용하면 배터리가 파열되거나 폭발할 수 있습니다.'),
      ('9','2', '방전된 차량의 모든 전기 장치를 끄십시오'),
      ('9','3', '엔진룸의 운전석 쪽에 있는 퓨즈 박스 커버를여십시오.'),
      ('9','4', '점프 게이블의 + 집게 한똑을 방전된 차량의 충전 단자(1)에 연결하고 + 집게 다른 한쪽을 다른 차량이나 보조 배터리의 + 단자(2)에 연결하십시오.'),
      ('9','5', '점프케이블의 - 집게 한쪽을 다른차량이나 보조 배터리의 - 단자(3)에 연결하고, - 집게 다른 한쪽을 방전된 차량의 - 충전 단자(4)에 연결하십시오.'),
      ('9','6', '다른 차량의 뱌터리에 연결하는 경우, 다른 차량의 시동을 걸어 몇분간 기다리십시오.'),
      ('9','7', '방전된 차량의 시동을 거십시오.'),
      ('9','8', '엔진 시동이 걸리면 - 충전 단자에 연결된 점프 케이블을 먼저 분리한 후 + 충전 단자에 연결된 점프 케이블을 분리하십시오.'),
      ('10','1', '비상 경고등을 켜고 도로 가장자리에 안전하게 정차한 후 P(주차)로 변속하고 파킹 브레이크를 거십시오.'),
      ('10','2', '에어컨이 켜져있는 경우, 에어컨을 끄십시오.'),
      ('10','3', '냉각수나 뜨거운 증기가 냉각수 보조 탱크에서 흘러 나오지 않는지 확인하십시오.'),
      ('10','4', '냉각수나 뜨거운 증기가 흘러 나오지 않으면, 엔진에 시동이 걸린 상태에서 엔진 후드를 열고 엔진 내부에 통풍이 잘 되도록 하여 엔진알 식히십시오.'),
      ('10','5', '엔진이 충분히 냉각되면 엔진 냉각수의 양 및 누수 여부를 점검하고, 라디에이터 호스 연결 부위, 히터 호스 연결 부위, 워터 펌프 등에 누수가 없으면 냉각수를 보충하십시오.'),
      ('11','1', '실런트(봉합제) 용기를 흔드십시오.'),
      ('11','2', '주입 호수(A)를 실런트 용기에 연결하여 고정하십시오.'),
      ('11','3', '실런트 용가를 컴프레서(B) 연결부위에 연결 후 고정시키십시오.'),
      ('11','4', '손상된 타이어의 휠 공기 주입구 캡을 풀어 주입 호스(2)를 휠 공기 주입구에 연결하여 고정하십시오.'),
      ('11','5', '컴프레서 전원이 꺼져 있는지 확인하십시오.'),
      ('11','6', '다용도 소켓 연결 커넥터 및 케이블(3)을 차량의 다용도 소켓에 연결하십시오'),
      ('11','7', '차량 시동을 거십시오.'),
      ('11','8', '컴프레서를 켜고 적정 타이어 공기압이 될 때까지 5~7분간 실런트(봉합제)를 주입하십시오.'),
      ('11','9', '컴프레서를 끄십시오.'),
      ('11','10', '실런트(봉합제) 주입 호스를 타이어 밸브에서 분리하십시오.'),
      ('11','11', '실런트(봉합제) 주입 후 즉시 주행 속도를 20 km/h 이상으로 주행거리 7~10 km 또는 10분 정도 주행하십시오'),
      ('11','12', '차량을 안전한 장소에 주차하십시오.'),
      ('11','13', '주입 호스(2)를 타이어 밸브에 바로 연결하십시오.'),
      ('11','14', '다용도 소켓 연결 커넥터 및 케이블을 차량의 다용도 소켓에 연결하십시오.'),
      ('11','15', '시동 ON 상태에서 다음과 같은 방법으로 타이어 공기압을 적정 공기압으로 조절하십시오.'),
      ('12','1', '타이어 응급 처치 키트에서 견인 후크를 꺼내십시오.'),
      ('12','2', '범퍼의 홀 커버를 눌러 홀 커버를 분리하십시오.'),
      ('12','3', '견인 후크를 홀에 넣어 오른쪽으로 끝까지 돌려 채결하십시오.'),
      ('12','4', '견인 후크에 로프를 확실히 고정시키십시오'),
      ('12','5', '기어를 N(중립)으로 변속하고, 스티어링 휠이 잠기지 않도록 시동을 ACC 상태로 두십시오.'),
      ('12','6', '주차 브레이크를 해제하십시오.'),
      ('12','7', '견인할 때 견인 차량의 운전자와 연락하면서 스티어링 휠을 잡고 견인 차량과 같은 방향으로 조향하십시오.'),
      ('13','1', '안전한 장소에 정차 하여 시동을 끄고 소화기등 으로 진화하십시오'),
      ('13','2', '진화 등의 응급 조치를 할 수 없는 상황인 경우, 사람들의 접근을 막고 소방서 및 경찰서에 연락하십시오.'),
      ('14','1', '라디오를 켜서 관련 방송을 청취하고, 필요하면 고속도로 안내 전화(1588-2504)의 안내를 받으십시오.'),
      ('14','2', '커브길, 고갯길, 교량 등에서는 감속하십시오.'),
      ('14','3', '차량을 방치하거나 갓길에 주차하지 마십시오. 제설 작업에 지장을 줄 수 있습니다'),
      ('14','4', '부득이하게 차량을 비워야 할 때는 반드시 연락처를 남겨 두십시오.'),
      ('14','5', '차량 간 안전거리를 확보하고 브레이크 사용을 자제하십시오.'),
      ('14','6', '수시로 차량 주변의 눈을 치워 배기관(머플러)이 막히지 않도록 하십시오.');

INSERT INTO maintenance_guide (vehicle_id, item_name, action_type, interval_km, interval_month, note)
VALUES(1, '엔진오일', '교체', 15000, 12, '가혹조건: 7500km or 6개월, 오일필터 동시 교체 권장'),
      (1, '냉각수', '교체', 210000, 120, '최초 10년 또는 210,000km 후 30,000km 또는 2년 주기'),
      (1, '브레이크액', '교체', 60000, 48, '정기적으로 점검 필요'),
      (1, '변속기 오일 (IVT)', '점검', NULL, NULL, '정기 점검, 필요 시 교체'),
      (1, '와셔액', '보충', NULL, NULL, '필요 시 수시 보충'),
      (1, '벨트 (구동 벨트)', '점검', 100000, NULL, '이상 시 교체'),
      (1, '주차 브레이크', '점검', 10000, NULL, '느슨함, 잡음 발생 시 정비'),
      (1, '연료필터', '점검', 60000, NULL, '디젤 차량 해당, 필요 시 교체'),
      (1, '에어클리너필터 (엔진)', '교체', 30000, NULL, '가혹조건: 15000km'),
      (1, '공조 에어필터 (캐빈)', '교체', 15000, 12, '가혹조건: 7500km or 6개월'),
      (1, '와이퍼 블레이드', '교체', NULL, 6, '6~12개월마다 점검 후 교체'),
      (1, '배터리', '점검', NULL, 36, '2~4년 사용 후 점검 및 교체'),
      (1, '타이어 공기압', '점검', NULL, 1, '월 1회 이상 권장'),
      (1, '타이어 마모', '점검', 50000, NULL, '트레드 마모선 기준, 편마모 확인'),
      (1, '퓨즈', '교체', NULL, NULL, '이상 발생 시 교체'),
      (1, '전구', '교체', NULL, NULL, '불량 시 동일 규격으로 교체');

select *
from emergency_steps;

CREATE TABLE chat_log (
                          id SERIAL PRIMARY KEY,
                          question TEXT NOT NULL,
                          answer TEXT NOT NULL,
                          car_model VARCHAR(50),
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE solution (
                          id SERIAL PRIMARY KEY,
                          question TEXT NOT NULL,
                          answer TEXT NOT NULL,
                          car_model TEXT NOT NULL,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

drop table solution;

CREATE TABLE solution (
                          id SERIAL PRIMARY KEY,
                          question TEXT NOT NULL,
                          answer TEXT NOT NULL,
                          car_model TEXT NOT NULL,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

select *
from solution;

delete
from solution
WHERE id = 5;