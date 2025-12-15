import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

INPUT_FILE = "book_id.csv"
OUTPUT_FILE = "yes24_review.csv"
PAGES_TO_CRAWL = 100

HEADERS = {
    'Accept': '*/',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Referer': 'https://www.yes24.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}

cookie_string = 'yes24_glbola_redirect=validationcheck=true|nation_id=south korea; ASP.NET_SessionId=3xy0bq0fckbntpedrciijxa3; USEPC=; _gcl_au=1.1.85898301.1763443054; _fbp=fb.1.1763443054035.401807269500555414; _ga=GA1.1.442525259.1763443054; _clck=1k7zg58%5E2%5Eg14%5E0%5E2148; PCID=17634430611937795694185; _fwb=136DdIuo2GWRbAuz0OhGSSD.1763443061197; ab.storage.deviceId.b0bae02d-84a6-48b3-96d0-498bd7843351=g%3A02bf94fb-ee9d-97d6-5dcc-c6733614201a%7Ce%3Aundefined%7Cc%3A1763443061215%7Cl%3A1763443061215; scrHistory=%uC774%uC0C1%uBB38%uD559%uC0C1; doroCheck=Y; RecentViewGoods=142763152; AICleanBotYn=Y; HTTP_REFERER=http://localhost:63342/; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%224SDtlN5I7x2kq14Lemi3%22%2C%22expiryDate%22%3A%222026-11-18T05%3A22%3A36.857Z%22%7D; wcs_bt=s_1b6883469aa6:1763443358; RecentViewInfo=NotCookie%3DY%26Interval%3D5%26ReloadTime%3DTue%2C%2018%20Nov%202025%2005%3A22%3A38%20GMT; ab.storage.sessionId.b0bae02d-84a6-48b3-96d0-498bd7843351=g%3A4c70cfc3-43c0-52ef-7805-eaef0740c879%7Ce%3A1763445158121%7Cc%3A1763443061213%7Cl%3A1763443358121; __rtbh.uid=%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22unknown%22%2C%22expiryDate%22%3A%222026-11-18T05%3A22%3A38.122Z%22%7D; _clsk=jfg7lv%5E1763443409349%5E5%E0%5Ea.clarity.ms%2Fcollect; _ga_FJT6RQ6VPQ=GS2.1.s1763443054$o1$g1$t1763443608$j41$l0$h0; _ga_Y6KMY9WWZ4G-FJT6RQ6VPQ=GS2.1.s1763443054$o1$g1$t1763443608$j41$l0$h0'
COOKIES = {item.split('=')[0]: item.split('=', 1)[-1] for item in cookie_string.split('; ')}

LIST_SELECTOR = "div.reviewInfoGrp"
STAR_SELECTOR = "span.review_rating"
TEXT_SELECTOR = "div.review_cont"
# -------------------------------------------------------------

all_reviews = []

try:
    print(f"'{INPUT_FILE}' 파일을 읽어옵니다...")
    df_books = pd.read_csv(INPUT_FILE)
    print(f"총 {len(df_books)}권의 책 정보를 찾았습니다.\n")

    for index, row in df_books.iterrows():
        year = row['year']

        book_title = row.get('book', row.get('book_title', '제목없음'))
        author = row['author']

        formatted_year_name = f"{year} {author} : {book_title}"

        product_id = str(row['yes24_id'])

        if pd.isna(product_id) or product_id == "None" or product_id == "nan" or not product_id:
            print(f"[{formatted_year_name}] Yes24 ID 없음 (패스)")
            continue

        if product_id.endswith('.0'):
            product_id = product_id.replace('.0', '')

        print("\n" + "=" * 50)
        print(f"▶ [{formatted_year_name}] (ID: {product_id}) 수집 시작...")
        print("=" * 50)

        HEADERS['Referer'] = f"https://www.yes24.com/product/goods/{product_id}"
        base_url = f"https://www.yes24.com/Product/CommunityModules/GoodsReviewList/{product_id}"
        params = {'Sort': '2', 'Type': 'ALL', 'DojungAfterBuy': '0'}

        for page in range(1, PAGES_TO_CRAWL + 1):
            params['PageNumber'] = str(page)
            params['_'] = str(int(time.time() * 1000))

            try:
                response = requests.get(base_url, params=params, cookies=COOKIES, headers=HEADERS)

                if response.status_code != 200:
                    print(f"  [오류] {page}페이지 접속 실패 (코드: {response.status_code})")
                    continue

                response.encoding = response.apparent_encoding
                soup = BeautifulSoup(response.text, "html.parser")
                review_list = soup.select(LIST_SELECTOR)

                if not review_list:
                    print(f"  [끝] {page} 페이지에 더 이상 리뷰가 없습니다.")
                    break

                count = 0
                for review in review_list:
                    try:
                        star_text = review.select_one(STAR_SELECTOR).get_text(strip=True)
                        raw_text = review.select_one(TEXT_SELECTOR).get_text(strip=True)

                        star = star_text.split('평점')[-1].split('점')[0]
                        text = raw_text.replace("더보기", "").strip()

                        if text:
                            all_reviews.append({
                                "year": year,
                                "author" : author,
                                "book" : book_title,
                                "site": "Yes24",
                                "star": star,
                                "review": text
                            })
                            count += 1
                    except:
                        pass

                print(f"  - {page}페이지: {count}개 수집 완료")

            except Exception as e:
                print(f"  - 에러 발생: {e}")

            time.sleep(0.5)

except FileNotFoundError:
    print(f" 오류: '{INPUT_FILE}' 파일이 없습니다. 파일명을 확인하세요.")
except Exception as e:
    print(f" 전체 에러: {e}")

# --- 저장 ---
print("\n" + "=" * 50)
print(f"최종 완료! 총 {len(all_reviews)}개의 리뷰를 수집했습니다.")

if all_reviews:
    df = pd.DataFrame(all_reviews)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"'{OUTPUT_FILE}' 파일로 저장되었습니다.")
else:
    print("수집된 리뷰가 0개입니다.")