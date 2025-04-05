# Databricks notebook source
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from PIL import Image

s = Service('/tmp/chrome/latest/chromedriver_linux64/chromedriver')
options = webdriver.ChromeOptions()
options.binary_location = "/tmp/chrome/latest/chrome-linux/chrome"
# 한글 깨짐 방지 폰트 설정 --- 안됨
options.add_argument('--font-family=NanumGothic')
options.add_argument('headless')
options.add_argument('--disable-infobars')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--remote-debugging-port=9222')
options.add_argument('--homedir=/tmp/chrome/chrome-user-data-dir')
options.add_argument('--user-data-dir=/tmp/chrome/chrome-user-data-dir')
prefs = {"download.default_directory":"/tmp/chrome/chrome-user-data-di",
         "download.prompt_for_download":False
}
options.add_experimental_option("prefs",prefs)
driver = webdriver.Chrome(service=s, options=options)

# 사이트 시작 URL
base_url = "https://www.semas.or.kr/web/SUP01/SUP0103/SUP010301.kmdc"
driver.get(base_url)


# 저장 폴더 설정
SAVE_DIR = "/Volumes/bronze/crawling_semas/img"
os.makedirs(SAVE_DIR, exist_ok=True)


# 대분류 (depth 1) 가져오기
def get_category_links():
    links = []
    for i in range(1, 40): 
        try:
            element = driver.find_element(By.XPATH, f'//*[@id="content"]/div[1]/ul/li[{i}]/a')
            links.append(element.get_attribute("href"))
        except:
            pass
    return links

# 중분류 (depth 2) 가져오기 (각 대분류별로 탐색)
def get_subcategory_links(depth1_index):
    links = []
    for j in range(1, 10):  # 중분류 최대 20개까지 탐색
        try:
            element = driver.find_element(By.XPATH, f'//*[@id="content"]/div[1]/ul/li[{depth1_index+1}]/ul/li[{j}]/a')
            links.append(element.get_attribute("href"))
        except:
            pass
    return links

# 전체 캡처 후 특정 영역 크롭
def full_capture(save_path):
    # ✅ 챗봇 요소 숨기기
    try:
        chatbot_element = driver.find_element(By.XPATH, '/html/body/div[1]/footer/a')
        driver.execute_script("arguments[0].style.display='none';", chatbot_element)
    except:
        pass  # 챗봇이 없으면 무시
    
    # 전체 페이지 높이 가져오기
    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")

    # 전체 페이지 캡처를 위한 큰 이미지 생성
    stitched_image = Image.new('RGB', (driver.execute_script("return document.body.scrollWidth"), total_height))
    scroll_position = 0
    screenshot_count = 0

    while scroll_position < total_height:
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        time.sleep(0.5)  # 스크롤 후 로딩 대기

        screenshot_path = f"temp_screenshot_{screenshot_count}.png"
        driver.save_screenshot(screenshot_path)

        img = Image.open(screenshot_path)
        stitched_image.paste(img, (0, scroll_position))

        scroll_position += viewport_height
        screenshot_count += 1
        os.remove(screenshot_path)

    # 전체 캡처 저장
    full_screenshot_path = "full_page_capture.png"
    stitched_image.save(full_screenshot_path)

    # 특정 영역의 위치와 크기 가져오기
    content = driver.find_element(By.XPATH, '//*[@id="content"]/div[2]')
    rect = driver.execute_script("""
        var rect = arguments[0].getBoundingClientRect();
        return {x: rect.left, y: rect.top + window.scrollY, width: rect.width, height: rect.height};
    """, content)

    # 크롭 좌표 계산
    left = int(rect['x'])
    top = int(rect['y'])
    right = left + int(rect['width'])
    bottom = top + int(rect['height'])

    # 전체 이미지에서 영역 크롭
    full_img = Image.open(full_screenshot_path)
    cropped_img = full_img.crop((left, top, right, bottom))
    cropped_img.save(save_path)
    os.remove(full_screenshot_path)  # 전체 캡처 파일 삭제

# 크롤링 실행
depth1_links = get_category_links()
print(f"대분류 {len(depth1_links)}개 발견")

for idx1, link1 in enumerate(depth1_links):
    driver.get(link1)
    time.sleep(2)

    # 중분류 탐색
    depth2_links = get_subcategory_links(idx1)
    
    # 중분류가 없는 경우 현재 대분류만 저장
    if not depth2_links:
        depth2_links = [link1]

    for idx2, link2 in enumerate(depth2_links):
        driver.get(link2)
        time.sleep(2)

        # 파일명 설정
        try:
            title_element = driver.find_element(By.XPATH, '//*[@id="content"]/div[2]/div[1]/h3')
            file_name = title_element.text.strip().replace(" ", "_") + ".png"
        except:
            file_name = f"capture_{idx1+1}_{idx2+1}.png"

        save_path = os.path.join(SAVE_DIR, file_name)

        # 캡처 수행
        full_capture(save_path)
        print(f"저장 완료: {save_path}")

driver.quit()

