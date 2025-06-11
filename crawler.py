import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import time
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# MongoDB 연결
client = MongoClient("mongodb+srv://PASSWORD")
db = client["news_politics"]
collection = db["2025.06.09"]

# Selenium 드라이버 세팅 (헤드리스 옵션 포함)
def get_selenium_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    return driver


def crawl_politics_news():
    print("🔍 정치 뉴스 크롤링 시작")
    
    headers = {'User-Agent': 'Mozilla/5.0'}

    # Selenium 드라이버 시작
    driver = get_selenium_driver()
    driver.get("https://news.naver.com/section/100")
    wait = WebDriverWait(driver, 10)

    # ⬇️ '더보기' 버튼 여러 번 클릭해서 기사 더 많이 로드
    MAX_CLICKS = 5 
    for i in range(MAX_CLICKS):
        try:
            more_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.section_more_inner._CONTENT_LIST_LOAD_MORE_BUTTON")))
            more_button.click()
            print(f"🟢 더보기 버튼 클릭: {i+1}회")
            time.sleep(2.5)
        except Exception:
            print("❌ 더보기 버튼 클릭 실패 또는 더 이상 없음")
            break

    # 📄 페이지 로딩 완료 후 soup 생성
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select('ul.sa_list > li.sa_item')
    
    # 맨 위 10개 건너뛰기 / 헤드라인 제거
    articles = articles[10:]

    print(f"✅ 총 기사 수 (더보기 클릭 후): {len(articles)}")

    count_saved = 0

    # Selenium 드라이버 시작
    driver = get_selenium_driver()

    try:
        for idx, article in enumerate(articles):
            if count_saved >= 115:
                break

            try:
                title_tag = article.select_one("a.sa_text_title")
                media_tag = article.select_one("span.press")

                if not title_tag:
                    continue

                title = title_tag.text.strip()
                href = title_tag['href']
                media = media_tag.text.strip() if media_tag else "언론사 없음"

                if collection.find_one({"URL": href}):
                    print(f"⏭ 중복된 기사: {title}")
                    continue

                # 기사 본문 요청 (requests)
                try:
                    news_res = requests.get(href, headers=headers, timeout=10)
                    news_res.raise_for_status()
                except requests.RequestException as e:
                    print(f"기사 요청 실패 ({href}): {e}")
                    continue

                news_soup = BeautifulSoup(news_res.text, "html.parser")

                # 본문
                body_tag = news_soup.select_one("#dic_area")
                body = body_tag.text.strip() if body_tag else "본문 없음"

                # 기자
                reporter_tag = news_soup.select_one(".byline")
                reporter = reporter_tag.text.strip() if reporter_tag else "기자 없음"

                # 날짜 (입력 날짜만 정확히 추출)
                date = None
                for bunch in news_soup.select("div.media_end_head_info_datestamp_bunch"):
                    em_tag = bunch.find("em", class_="media_end_head_info_datestamp_term")
                    if em_tag and em_tag.text.strip() == "입력":
                        date_span = bunch.find("span", class_="media_end_head_info_datestamp_time")
                        if date_span and date_span.has_attr("data-date-time"):
                            date = date_span["data-date-time"]
                            break

                if not date:
                    print(f"⏭ 날짜 정보 없음: {title}")
                    continue

                # 언론사 로고 alt로 업데이트
                logo_tag = news_soup.select_one("img.media_end_head_top_logo_img")
                if logo_tag and logo_tag.has_attr("alt"):
                    media = logo_tag['alt']

                # Selenium으로 공감수와 댓글수 가져오기
                driver.get(href)
                time.sleep(2)  # 페이지 렌더링 대기

                try:
                    like_elem = driver.find_element(By.CSS_SELECTOR, 'div._reactionModule span.u_likeit_text._count.num')
                    like_count = int(like_elem.text.strip().replace(',', ''))
                except Exception:
                    like_count = 0

                try:
                    comment_elem = driver.find_element(By.CSS_SELECTOR, 'a#comment_count')
                    comment_count = int(comment_elem.text.strip().replace(',', ''))
                except Exception:
                    comment_count = 0

                # 저장 데이터 생성
                data = {
                    "title": title,
                    "URL": href,
                    "media": media,
                    "body": body,
                    "reporter": reporter,
                    "date": date,
                    "like_count": like_count,
                    "comment_count": comment_count,
                    "crawled_at": datetime.now()
                }

                collection.insert_one(data)
                count_saved += 1
                print(f"{count_saved}. ✅ 저장됨: {title}")

                delay = random.uniform(4, 7)
                print(f"⏳ 대기 중... {delay:.2f}초")
                time.sleep(delay)

            except Exception as e:
                print(f"⚠️ 처리 중 에러 발생: {e}")
                continue
    finally:
        driver.quit()

    print(f"📦 최종 저장된 기사 수: {count_saved}")


if __name__ == "__main__":
    crawl_politics_news()
