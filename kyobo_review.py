import time
import pandas as pd
import requests
import json

INPUT_FILE = "book_id.csv"
OUTPUT_FILE = "kyobo_review.csv"
PAGES_TO_CRAWL = 50

HEADERS = {
    'accept': '*/*',
    'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'priority': 'u=1, i',
    'referer': 'https://product.kyobobook.co.kr/',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
}


cookie_string = 'ab_variant=A; b5dcbb5e99191a099429032ae16cffe3=f1ffb81a17b0282e5081a16d305a30cc; RB_PCID=1764036611560763968; _fwb=90aZQtdIs6gVlbuD3pF7X0.1764036611616; EG_GUID=ad117a01-2efd-489c-ad9d-0587d5fa0594; _ga=GA1.1.1327979528.1764036612; _fbp=fb.2.1764036611815.43835241711626848; _clck=145brt5%5E2%5Eg1b%5E0%5E2155; order.shipping.addr=03154K//%EC%84%9C%EC%9A%B8%EC%8B%9C%20%EC%A2%85%EB%A1%9C%EA%B5%AC%20%EC%A2%85%EB%A1%9C%201; spses.bb7d=*; _fcOM={"k":"5cc17cbe5e92e08929d7ed1d19998676b4138f6","i":"210.102.151.188.6528","r":1764036612589}; _fwb=219BPq4Yqqpai22MKnB4CjC.1764036657720; wpromo-banner=true; shtm=%EC%9D%B4%EC%83%81%EB%AC%B8%ED%95%99%EC%83%81%202021; recentSch=%uC774%uC0C1%uBB38%uD559%uC0C1%202021%24%5E%7C11.25%24%7C%uC774%uC0C1%uBB38%uD559%uC0C1%202022%24%5E%7C11.25%24%7C%uC774%uC0C1%uBB38%uD559%uC0C1%202023%24%5E%7C11.25%24%7C%uC774%uC0C1%uBB38%uD559%uC0C1%202024%24%5E%7C11.25%24%7C%uC774%uC0C1%uBB38%uD559%uC0C1%202025%24%5E%7C11.25%24%7C; RB_SSID=ANJOsBsHpn; rc-cont=[%22p|KOR|S000001913217%22%2C%22p|KOR|S000215787788%22%2C%22p|KOR|S000213024399%22%2C%22p|KOR|S000200899876%22%2C%22p|KOR|S000001068543%22%2C%22p|KOR|S000001068503%22]; wcs_bt=s_453f4415ebcb:1764036733; spid.bb7d=91231fee-7fef-4df7-bb93-49e7f993b610.1764036612.1.1764036734..a316cae4-3ded-4e35-a3b9-de0f9b6ec93b..9a04737c-bd35-4484-9cea-c480923d0cb3.1764036612315.20; _clsk=29hdws%5E1764036734143%5E16%5E1%5Ea.clarity.ms%2Fcollect; JSESSIONID=AD110277616B2A49EFFC1F5AFCA7513C; _ga_CQHKV7VZV7=GS2.1.s1764036611$o1$g1$t1764036818$j54$l0$h0'
COOKIES = {item.split('=')[0]: item.split('=', 1)[-1] for item in cookie_string.split('; ')}


base_url = "https://product.kyobobook.co.kr/api/review/list"


PARAMS = {
    'pageLimit': '10',
    'reviewSort': '001',
    'revwPatrCode': '000',
    'webToonYsno': 'N',
    'allYsno': 'N',
    'revwSummeryYn': 'Y',
}
# ----------------------------------------------------

all_reviews = []

try:
    print(f"'{INPUT_FILE}' 파일을 읽어옵니다...")
    df_books = pd.read_csv(INPUT_FILE)
    print(f"총 {len(df_books)}권의 책 정보를 찾았습니다.\n")

    for index, row in df_books.iterrows():
        year = row['year']
        author = row['author']
        book_title = row.get('book', row.get('book_title', '제목없음'))
        formatted_year_name = f"{year}: {book_title}"

        product_id = str(row['kyobo_id'])

        if pd.isna(
                product_id) or product_id == "None" or product_id == "nan" or not product_id or not product_id.startswith(
                'S'):
            print(f"[{formatted_year_name}] 교보문고 ID 없음/오류 (패스)")
            continue

        print("\n" + "=" * 50)
        print(f"▶ [{formatted_year_name}] (ID: {product_id}) 수집 시작...")
        print("=" * 50)

        HEADERS['referer'] = f"https://product.kyobobook.co.kr/detail/{product_id}"
        PARAMS['saleCmdtids'] = product_id
        PARAMS['saleCmdtid'] = product_id

        for page in range(1, PAGES_TO_CRAWL + 1):
            PARAMS['page'] = str(page)

            response = requests.get(base_url, params=PARAMS, cookies=COOKIES, headers=HEADERS)

            if response.status_code != 200:
                print(f"  [오류] 접속 실패 (코드: {response.status_code})")
                continue

            try:
                data = response.json()
                review_list = data.get('data', {}).get('reviewList', [])
            except:
                review_list = []

            if not review_list:
                print(f"  [끝] {page} 페이지에 더 이상 리뷰가 없습니다.")
                break

            count = 0
            for review in review_list:
                try:
                    content = review.get('revwCntt') or review.get('revwCntn') or ''
                    content = content.strip()

                    rating = review.get('revwRvgr', 0)

                    if content:
                        all_reviews.append({
                            "year": year,
                            "author" : author,
                            "book" : book_title,
                            "site": "Kyobo",
                            "star": rating,
                            "review": content
                        })
                        count += 1
                except Exception as e:
                    pass

            print(f"  - {page}페이지: {count}개 수집 완료")
            time.sleep(0.5)

except FileNotFoundError:
    print(f" 오류: '{INPUT_FILE}' 파일이 없습니다.")
except Exception as e:
    print(f" 크롤링 중 에러 발생: {e}")

# --- 저장 ---
print("\n" + "=" * 40)
print(f"최종 완료! 총 {len(all_reviews)}개의 리뷰를 수집했습니다.")

if all_reviews:
    df = pd.DataFrame(all_reviews)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f" '{OUTPUT_FILE}' 파일로 저장되었습니다.")
else:
    print("수집된 리뷰가 없습니다.")