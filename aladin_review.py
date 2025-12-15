import time
import pandas as pd
import requests
from bs4 import BeautifulSoup


INPUT_FILE = "book_id.csv"
OUTPUT_FILE = "aladin_review.csv"
PAGES_TO_CRAWL = 25

HEADERS = {
    'Accept': '*/',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Referer': 'https://www.aladin.co.kr/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}

cookie_string = 'CheckSameSite4=IsValidSameSiteSet; AladdinUser=UID=-1348892644&SID=PZRt18fpu4ciAe5%2bwP6Hlg%3d%3d; AladdinUS=2aNgt2PryuT0zl%2fuEbq6hA%3d%3d&USA=0; _gcl_au=1.1.1254231033.1757643213; _fwb=132aDBhEmNvllkvdUsPFGBV.1757643213323; _ga=GA1.1.1306524516.1757643213; _BS_GUUID=ZyHwKrfZd2rVClqBXPJPehhNSlQRW5mWE4tovJoJ; _TRK_AUIDA_13987=0180c1f0eec23e0a508a0d4cbc3d570e:2; _TRK_ASID_13987=b050e67535e376e330432261b14650d5; _clck=x66pvn%5E2%5Eg14%5E0%5E2148; NA_CO=ct%3Dmi46mcgb%7Cci%3Dcheckout%7Ctr%3Ds%7Chk%3Dd62c5a665aead4f232bc12dec1be9d959258ea73%7Ctrx%3Dnull; refererURL=https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=358328336; _clsk=1nd29rl%5E1763446682923%5E6%E0%5Ea.clarity.ms%2Fcollect; _ga_VKYKBC0ZHH=GS2.1.s1763446076$o3$g1$t1763446797$j60$l0$h0; wcs_bt=s_1c519d64863a:1763446797|b78bdfda7ab45:1763446797'
COOKIES = {item.split('=')[0]: item.split('=', 1)[-1] for item in cookie_string.split('; ')}

PARAMS = {
    'pageCount': '10',
    'communitytype': 'CommentReview',
    'nemoType': '-1',
    'page': '1',
    'startNumber': '1',
    'endNumber': '10',
    'sort': '2',
    'BranchType': '1',
    'IsAjax': 'true',
    'pageType': '0',
}
base_url = "https://www.aladin.co.kr/ucl/shop/product/ajax/GetCommunityListAjax.aspx"

LIST_SELECTOR = "div.hundred_list"
STAR_SELECTOR = "div.HL_star"
TEXT_SELECTOR = 'span[id^="spnPaper"]:not([id*="Spoiler"])'

all_reviews = []

try:
    print(f"'{INPUT_FILE}' 파일을 읽어옵니다...")
    df_books = pd.read_csv(INPUT_FILE)
    print(f"총 {len(df_books)}권의 책 정보를 찾았습니다.\n")

    for index, row in df_books.iterrows():
        year = row['year']
        author = row['author']
        book_title = row.get('book', row.get('book_title', '제목없음'))
        formatted_year_name = f"{year} : {book_title}"
        product_id = str(row['aladin_id'])

        if pd.isna(product_id) or product_id == "None" or product_id == "nan" or not product_id:
            print(f"[{formatted_year_name}] 알라딘 ID 없음 (패스)")
            continue

        if product_id.endswith('.0'):
            product_id = product_id.replace('.0', '')

        print("\n" + "=" * 50)
        print(f"▶ [{formatted_year_name}] (ID: {product_id}) 수집 시작...")
        print("=" * 50)

        HEADERS['Referer'] = f"https://www.aladin.co.kr/shop/wproduct.aspx?ItemId={product_id}"
        PARAMS['itemId'] = product_id
        PARAMS['ProductItemId'] = product_id

        crawl_modes = [
            {'code': '1', 'name': '구매자'},
            {'code': '0', 'name': '전체'}
        ]

        for mode in crawl_modes:
            mode_code = mode['code']
            mode_name = mode['name']

            PARAMS['IsOrderer'] = mode_code
            print(f" [{mode_name} 리뷰] 모드로 수집 중...")

            for page in range(1, PAGES_TO_CRAWL + 1):
                PARAMS['page'] = str(page)
                PARAMS['startNumber'] = str((page - 1) * 10 + 1)
                PARAMS['endNumber'] = str(page * 10)

                try:
                    response = requests.get(base_url, params=PARAMS, cookies=COOKIES, headers=HEADERS)

                    if response.status_code != 200:
                        continue

                    response.encoding = response.apparent_encoding
                    soup = BeautifulSoup(response.text, "html.parser")
                    review_list = soup.select(LIST_SELECTOR)

                    if not review_list:
                        break

                    count = 0
                    for review in review_list:
                        try:
                            star_html = str(review.select_one(STAR_SELECTOR))
                            star_count = star_html.count("icon_star_on.png")
                            star = star_count * 2

                            text_element = review.select_one(TEXT_SELECTOR)
                            if text_element:
                                text = text_element.get_text(strip=True)
                                if text:
                                    all_reviews.append({
                                        "year": year,
                                        "author" : author,
                                        "book" : book_title,
                                        "site": "Aladin",
                                        "star": star,
                                        "review": text
                                    })
                                    count += 1
                        except:
                            pass

                    print(f"    - {page}페이지: {count}개 완료")
                    time.sleep(0.3)

                except:
                    pass

            # 모드 바뀔 때 잠시 대기
            time.sleep(0.5)

except FileNotFoundError:
    print(f" 오류: '{INPUT_FILE}' 파일이 없습니다.")
except Exception as e:
    print(f" 전체 에러: {e}")

# --- 저장 ---
print("\n" + "=" * 50)
print(f"최종 완료! 총 {len(all_reviews)}개의 리뷰를 수집했습니다.")

if all_reviews:
    df = pd.DataFrame(all_reviews)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f" '{OUTPUT_FILE}' 파일로 저장되었습니다.")
else:
    print("수집된 리뷰가 없습니다.")