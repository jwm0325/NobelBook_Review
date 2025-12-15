import time
import pandas as pd
import urllib.parse
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
from book_list import NOBEL_MASTER_LIST


print("[최종 통합본] Yes24(클릭복구) + 교보(구글우회) + 알라딘")
options = uc.ChromeOptions()
driver = uc.Chrome(options=options)

print("브라우저 워밍업 (3초)...")

driver.get("https://www.google.com")
time.sleep(3)


def get_yes24_id(author, title):
    try:
        query = f"{author} {title}"
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.yes24.com/Product/Search?domain=ALL&query={encoded_query}"

        driver.get(url)
        time.sleep(2.5)

        target = None

        candidates = driver.find_elements(By.CSS_SELECTOR, "a.gd_name")
        if candidates:
            target = candidates[0]
        else:
            candidates = driver.find_elements(By.CSS_SELECTOR, "div.itemUnit a")
            if candidates:
                target = candidates[0]

        if target:
            target.click()
            time.sleep(2.5)

            curr_url = driver.current_url.lower()

            if "/goods/" in curr_url:
                return curr_url.split('/goods/')[-1].split('?')[0]
            else:
                driver.back()
                time.sleep(2)

    except Exception as e:
        print(f"  (Yes24 에러: {e})")
        pass
    return None



def get_aladin_id(author, title):
    try:
        query = f"{author} {title}"
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Book&SearchWord={encoded_query}"
        driver.get(url)
        time.sleep(1.5)
        links = driver.find_elements(By.CSS_SELECTOR, "a.bo3")
        if links:
            href = links[0].get_attribute('href')
            return href.split('ItemId=')[1].split('&')[0]
    except:
        pass
    return None



def get_kyobo_via_google(author, title):
    try:
        driver.get("https://www.google.com")
        time.sleep(1.5)

        search_box = driver.find_element(By.NAME, "q")
        search_box.clear()

        search_query = f"site:kyobobook.co.kr {author} {title}"
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)

        time.sleep(2.5)

        xpath = "//a[contains(@href, 'product.kyobobook.co.kr/detail/')]"
        links = driver.find_elements(By.XPATH, xpath)

        if links:
            first_link = links[0].get_attribute('href')
            if "/detail/" in first_link:
                return first_link.split('/detail/')[-1].split('?')[0]

    except Exception as e:
        print(f"  (Kyobo 우회 에러: {e})")

    return None


# --- 메인 실행 ---
book_ids = []
print("\n수집 시작\n")
print("-" * 60)

for data in NOBEL_MASTER_LIST:
    year = data["year"]
    author = data["author"]
    book_title = data["book"]

    if year == 2020: continue

    print(f"[{year}년] {author} - '{book_title}' 찾는 중...", end="", flush=True)

    y_id = get_yes24_id(author, book_title)
    a_id = get_aladin_id(author, book_title)
    k_id = get_kyobo_via_google(author, book_title)

    print(f"\n   ➜ Yes24: {y_id} | Aladin: {a_id} | Kyobo: {k_id}")
    print("-" * 60)

    book_ids.append({
        "year": year,
        "author": author,
        "book_title": book_title,
        "yes24_id": y_id,
        "aladin_id": a_id,
        "kyobo_id": k_id
    })

    time.sleep(2.5)

# --- 저장 ---
print("\n 저장 중...")
df = pd.DataFrame(book_ids)
df.to_csv("book_id.csv", index=False, encoding="utf-8-sig")
print(" 작업 완료! 'book_id.csv' 확인하세요.")

try:
    driver.quit()
except:
    pass