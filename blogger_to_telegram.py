import os
import requests
import feedparser
import time

# 환경 변수에서 정보 가져오기 (GitHub Secrets에 저장할 거예요!)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BLOGGER_URL = os.getenv('BLOGGER_URL')

# 마지막으로 확인한 글의 날짜를 저장할 파일 이름
LAST_POST_FILE = 'last_post.txt'

def send_telegram_message(text):
    """텔레그램으로 메시지를 보내는 함수예요."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, data=payload)
    return response.json()

def check_blogger_updates():
    """블로거의 새로운 글을 확인하는 함수예요."""
    # RSS 피드 주소 만들기 (URL 끝에 /feeds/posts/default?alt=rss를 붙여요)
    feed_url = f"{BLOGGER_URL.rstrip('/')}/feeds/posts/default?alt=rss"
    feed = feedparser.parse(feed_url)
    
    if not feed.entries:
        print("글을 찾을 수 없어요. 주소를 확인해 보세요!")
        return

    # 가장 최신 글 가져오기
    latest_entry = feed.entries[0]
    latest_title = latest_entry.title
    latest_link = latest_entry.link
    latest_published = latest_entry.published

    # 이전에 보냈던 글인지 확인하기
    last_published = ""
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, 'r') as f:
            last_published = f.read().strip()

    if latest_published != last_published:
        # 새로운 글이 발견되었어요!
        print(f"새 글 발견!: {latest_title}")
        
        # 메시지 예쁘게 만들기
        message = f"🌟 <b>새 글이 올라왔어요!</b> 🌟\n\n" \
                  f"📝 제목: {latest_title}\n" \
                  f"🔗 확인하기: {latest_link}"
        
        # 텔레그램으로 보내기
        send_telegram_message(message)
        
        # 마지막 글 날짜 업데이트하기
        with open(LAST_POST_FILE, 'w') as f:
            f.write(latest_published)
    else:
        print("새로운 글이 없어요. 다음에 다시 확인해 볼게요! 😊")

if __name__ == "__main__":
    if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, BLOGGER_URL]):
        print("❌ 필요한 설정값이 없어요! GitHub Secrets를 확인해 주세요.")
    else:
        check_blogger_updates()
