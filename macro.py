import cv2
import numpy as np
import time
import os
import sys
from ppadb.client import Client as AdbClient

print("🚀 드래곤빌리지3 레이드 자동 매크로 시작...")

try:
    # 1. 파이썬과 LDPlayer 연결
    client = AdbClient(host="127.0.0.1", port=5037)
    client.remote_connect("127.0.0.1", 5555)
    devices = client.devices()
    if not devices:
        raise RuntimeError("연결된 기기가 없습니다. LDPlayer 실행 및 ADB 디버깅 설정을 확인하세요.")
    device = devices[0]
    print(f"✅ LDPlayer 연결 성공! (기기 ID: {device.serial})")
except Exception as e:
    print(f"❌ 연결 오류 발생: {e}")
    sys.exit()

# 2. 기준 이미지 9장 불러오기 (images 폴더 내부 경로 지정)
IMG_DIR = "images"

def load_img(filename):
    path = os.path.join(IMG_DIR, filename)
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"'{path}' 파일을 찾을 수 없습니다.")
    return img

try:
    img_refresh = load_img("refresh_btn.png")
    img_target = load_img("target.png")
    img_ready = load_img("ready_btn.png")
    img_battle = load_img("battle_btn.png")
    img_exit = load_img("exit_btn.png")
    img_potion_select = load_img("potion_select.png")
    img_potion_use = load_img("potion_use.png")
    img_x = load_img("x_btn.png")
    img_proceed = load_img("proceed_btn.png")
    print("✅ 기준 이미지 9장 로드 완료!")
except Exception as e:
    print(f"❌ 이미지 로드 오류: {e}")
    sys.exit()

# 3. 화면에서 이미지를 찾고 클릭하는 도우미 함수 (기본 정확도 0.85로 조정)
def find_and_click(screen_img, template_img, target_name, threshold=0.85):
    result = cv2.matchTemplate(screen_img, template_img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = template_img.shape[:2]
        center_x = max_loc[0] + (w // 2)
        center_y = max_loc[1] + (h // 2)
        
        device.input_tap(center_x, center_y)
        print(f"👉 [{target_name}] 클릭 완료! (일치율: {max_val*100:.1f}%)")
        return True
    return False

# 클릭하지 않고 화면에 이미지가 존재하는지만 확인하는 함수 (기본 정확도 0.85로 조정)
def check_exists(screen_img, template_img, threshold=0.85):
    result = cv2.matchTemplate(screen_img, template_img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val >= threshold

print("====================================")
print("▶ 무한 루프 감시를 시작합니다. (중지하려면 이 창을 끄세요)")
print("====================================")

# 4. 무한 반복 루프
while True:
    try:
        # 현재 화면 캡처
        screen_data = device.screencap()
        screen_img = cv2.imdecode(np.frombuffer(screen_data, np.uint8), cv2.IMREAD_COLOR)

        # 우선순위 1: '피로 회복제 사용' 최종 팝업의 [사용] 버튼 확인
        if find_and_click(screen_img, img_potion_use, "피로회복제 사용 확정"):
            time.sleep(2)
            print("👉 [피로도 회복 창 닫기] 화면 바깥 빈 공간 클릭!")
            device.input_tap(270, 900)
            time.sleep(2)
            continue

        # 우선순위 2: '피로도 회복' 메뉴 팝업의 [물약 1] 카드 버튼 확인
        elif find_and_click(screen_img, img_potion_select, "피로도 회복 메뉴 선택"):
            time.sleep(1.5)
            continue

        # 우선순위 3: 보주/젬 미장착 안내 팝업의 [이대로 진행] 버튼 확인
        elif find_and_click(screen_img, img_proceed, "보주/젬 미장착 이대로 진행"):
            time.sleep(2)
            continue

        # 우선순위 4: 전투 종료 후 결과창 '나가기(확인)' 버튼 확인
        elif find_and_click(screen_img, img_exit, "결과창 나가기"):
            time.sleep(3)
            continue
            
        # 우선순위 5: 덱 편성 화면 '전투' 버튼 확인
        elif find_and_click(screen_img, img_battle, "전투 시작 시도"):
            time.sleep(2)
            
            # 2초 뒤 화면을 다시 찍어서 상황 판단
            check_data = device.screencap()
            check_img = cv2.imdecode(np.frombuffer(check_data, np.uint8), cv2.IMREAD_COLOR)
            
            # 만약 보주/젬 미장착 팝업이 떴다면 즉시 '이대로 진행' 클릭 후 다시 2초 대기
            if find_and_click(check_img, img_proceed, "보주/젬 미장착 이대로 진행"):
                time.sleep(2)
                check_data = device.screencap()
                check_img = cv2.imdecode(np.frombuffer(check_data, np.uint8), cv2.IMREAD_COLOR)
            
            # 피로도 회복 창이 안 떴는데, 여전히 '전투' 버튼이 화면에 그대로 남아있다면? -> 종료된 레이드!
            if not check_exists(check_img, img_potion_select) and check_exists(check_img, img_battle):
                print("⚠️ 종료된 레이드 감지! X 버튼을 눌러 방을 나갑니다.")
                
                # 1차 탈출: 덱 편성 화면 우측 하단의 X 버튼 클릭
                if find_and_click(check_img, img_x, "편성 화면 나가기(X)"):
                    time.sleep(2)
                    
                    # 2차 탈출: 대기실 화면에서도 마저 나가기 위해 화면 다시 찍고 X 버튼 한 번 더 클릭
                    wait_data = device.screencap()
                    wait_img = cv2.imdecode(np.frombuffer(wait_data, np.uint8), cv2.IMREAD_COLOR)
                    find_and_click(wait_img, img_x, "대기실 나가기(X)")
                    time.sleep(2)
            continue
            
        # 우선순위 6: 대기실 '전투 준비' 버튼 확인
        elif find_and_click(screen_img, img_ready, "전투 준비"):
            time.sleep(2)
            continue
            
        # 우선순위 7: 레이드 목록 'SUMMONER' (target) 마크 확인 (배경 비침 감안하여 0.80 적용)
        elif find_and_click(screen_img, img_target, "레이드 방 진입", threshold=0.80):
            time.sleep(2)
            continue
            
        # 우선순위 8: 아무것도 없으면 '새로 고침' 버튼 클릭
        elif find_and_click(screen_img, img_refresh, "새로 고침"):
            print("⏳ 레이드 탐색 중... 5초 대기")
            time.sleep(5)
            continue

        # 전투 진행 중이거나 로딩 중일 때
        else:
            time.sleep(1.5)

    except Exception as e:
        print(f"⚠️ 루프 실행 중 오류 발생: {e}")
        time.sleep(2)
