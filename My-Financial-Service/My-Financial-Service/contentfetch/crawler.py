from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import time
import re

def fetch_toss_comments(company_name: str, limit: int = 20, max_scroll: int = 8):
    """
    Toss Invest 커뮤니티의 게시글(댓글 성격의 본문) 텍스트를 최대 `limit`개 수집.
    순서:
      1) 메인 접속
      2) '/' 로 검색창 포커스 → 회사명 입력 후 ENTER
      3) /order URL에서 종목 코드 추출
      4) /community 이동
      5) 피드 무한스크롤하며 텍스트 수집
    """
    # --------------- 브라우저 옵션 ---------------
    opts = Options()
    # 필요 시 headless 해제하고 확인
    # opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1200,900")
    # 약간의 안정성 옵션
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--lang=ko-KR")
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    wait = WebDriverWait(driver, 15)

    def _extract_stock_code_from_url(url: str):
        # https://www.tossinvest.com/stocks/{code}/order
        parts = [p for p in url.split("/") if p]
        if "stocks" in parts:
            idx = parts.index("stocks")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        return None

    def _strip_noise(text: str) -> str:
        # 좋아요/댓글/공유/시간 같은 메타 텍스트 제거에 도움 되는 간단한 필터링
        t = text.strip()
        # 너무 짧은 것 제외
        if len(t) < 5:
            return ""
        # 숫자만 있는 카운트류 제외
        if re.fullmatch(r"[0-9]+", t):
            return ""
        # 흔한 메타 단어가 전부인 줄 제외
        meta_keywords = ["좋아요", "댓글", "공유", "팔로우", "팔로잉"]
        if any(kw in t for kw in meta_keywords) and len(t) <= 6:
            return ""
        return t

    def _extract_texts_from_feed(driver):
        """
        커뮤니티 피드에서 보이는 카드들로부터 텍스트를 수집.
        - 우선 카드(anchor) 요소를 잡고 후손 p/span/div 텍스트를 모음
        - 보조로 article 블록의 p를 긁는 fallback
        """
        texts = []
        seen = set()

        # 카드 앵커(게시글 상세로 가는 링크) 후보
        card_selectors = [
            "a[href*='/community/posts/']",
            "article a[href*='/community/posts/']",
        ]
        # 카드 내부 본문 후보
        inner_text_selectors = [
            "p", "div", "span"
        ]

        for sel in card_selectors:
            cards = driver.find_elements(By.CSS_SELECTOR, sel)
            for card in cards:
                # 카드 자체 텍스트
                raw = card.text or ""
                t = _strip_noise(raw)
                if t and t not in seen:
                    texts.append(t)
                    seen.add(t)
                # 카드 후손에서 한 번 더 시도 (문단 단위)
                for inner in inner_text_selectors:
                    for node in card.find_elements(By.CSS_SELECTOR, inner):
                        raw2 = node.text or ""
                        t2 = _strip_noise(raw2)
                        if t2 and t2 not in seen:
                            texts.append(t2)
                            seen.add(t2)

        # 보조: article 블록에서 p만 긁기 (UI가 바뀌었을 때 대비)
        if len(texts) < 5:
            articles = driver.find_elements(By.TAG_NAME, "article")
            for art in articles:
                for p in art.find_elements(By.TAG_NAME, "p"):
                    t = _strip_noise(p.text or "")
                    if t and t not in seen:
                        texts.append(t)
                        seen.add(t)

        return texts

    try:
        # 1) 사이트 접속
        driver.get("https://www.tossinvest.com/")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # (간혹 등장하는 배너/모달 대비: Esc, 또는 '닫기'류 버튼 클릭 시도)
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass

        # 2) 검색창 활성화 → 회사 검색 (ENTER)
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys("/")  # 토스 인베스트의 퀵 서치
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='검색어를 입력해주세요']"))
        )
        search_input.click()
        search_input.clear()
        search_input.send_keys(company_name)
        search_input.send_keys(Keys.ENTER)

        # 3) /order 페이지 대기 및 종목 코드 추출
        wait.until(EC.url_contains("/order"))
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        current_url = driver.current_url
        stock_code = _extract_stock_code_from_url(current_url)

        if not stock_code:
            # 가끔 검색 후 바로 /order가 아닌 상세로 진입하는 경우 재시도
            time.sleep(1)
            current_url = driver.current_url
            stock_code = _extract_stock_code_from_url(current_url)

        if not stock_code:
            raise RuntimeError("종목 코드를 URL에서 추출하지 못했습니다.")

        # 4) 커뮤니티 페이지로 이동
        community_url = f"https://www.tossinvest.com/stocks/{stock_code}/community"
        driver.get(community_url)

        # 피드 로드 대기: main 및 피드 카드가 보일 때까지
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        # 초기 카드가 하나라도 보일 때까지 대기 (여러 후보 중 하나 충족)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/community/posts/'], article"))
            )
        except Exception:
            pass  # 셀렉터가 바뀐 경우 스크롤하며 탐색

        # 5) 무한 스크롤하며 텍스트 수집
        collected = []
        seen_texts = set()
        last_height = 0

        for _ in range(max_scroll):
            # 현재 보이는 카드들에서 텍스트 수집
            chunk = _extract_texts_from_feed(driver)
            for t in chunk:
                if t not in seen_texts:
                    collected.append({"text": t})
                    seen_texts.add(t)
            if len(collected) >= limit:
                break

            # 스크롤 다운
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(0.8)

            # 높이 변화 감지(간단 버전)
            new_height = driver.execute_script("return document.body.scrollHeight") or 0
            if new_height <= last_height:
                # 더 안 늘어나면 한 번 더 미세 스크롤
                driver.execute_script("window.scrollBy(0, 600);")
                time.sleep(0.6)
                newer_height = driver.execute_script("return document.body.scrollHeight") or 0
                if newer_height <= last_height:
                    break
                last_height = newer_height
            else:
                last_height = new_height

        # 부족할 경우, 마지막으로 광범위 휴리스틱 시도
        if len(collected) < limit:
            fallback = _extract_comments_heuristic(driver, limit=limit - len(collected))
            for item in fallback:
                t = item["text"]
                if t not in seen_texts:
                    collected.append({"text": t})
                    seen_texts.add(t)
                if len(collected) >= limit:
                    break

        return {
            "stock_code": stock_code,
            "comments": collected[:limit]
        }

    except Exception as e:
        import traceback
        print("fetch_toss_comments 에러:", traceback.format_exc())
        return {"stock_code": None, "comments": []}
    finally:
        driver.quit()


def _extract_comments_heuristic(driver, limit=50):
    """
    마지막 보루: 흔한 코멘트/본문 패턴 셀렉터를 순차 시도.
    """
    candidate_css = [
        "a[href*='/community/posts/'] p",
        "article p",
        "[class*='comment']",
        "[id*='comment']",
        ".comment, .comments, .cmt, .reply, .replies",
        ".comment-body, .comment-text, .reply-content",
        "li.comment, div.comment, article .comment",
        "section.comments",
        "p"
    ]
    seen = set()
    out = []

    def clean(txt: str) -> str:
        t = (txt or "").strip()
        if len(t) < 5:
            return ""
        if re.fullmatch(r"[0-9]+", t):
            return ""
        return t

    for sel in candidate_css:
        nodes = driver.find_elements(By.CSS_SELECTOR, sel)
        for n in nodes:
            try:
                t = clean(n.text)
                if t and t not in seen:
                    out.append({"text": t})
                    seen.add(t)
                    if len(out) >= limit:
                        return out
            except Exception:
                pass

        # 충분히 수집되면 바로 반환
        if len(out) >= max(5, limit // 3):
            return out[:limit]

    return out[:limit]
