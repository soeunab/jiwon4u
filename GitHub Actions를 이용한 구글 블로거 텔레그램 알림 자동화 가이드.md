# GitHub Actions를 이용한 구글 블로거 텔레그램 알림 자동화 가이드

이 가이드는 구글 블로거에 새 글이 발행될 때마다 텔레그램으로 알림을 보내는 시스템을 GitHub Actions를 활용하여 자동화하는 방법을 설명합니다. 별도의 서버 없이 GitHub의 무료 기능을 사용하여 24시간 동작하는 알림 시스템을 구축할 수 있습니다.

## 1. 시스템 개요

기존 파이썬 스크립트를 GitHub 저장소에 업로드하고, GitHub Actions 워크플로우를 통해 주기적으로 스크립트를 실행합니다. 스크립트는 블로거 RSS 피드를 확인하고, 새로운 글이 있으면 텔레그램 봇을 통해 메시지를 전송합니다. 마지막으로 확인한 글 정보는 GitHub 저장소 내의 파일에 저장하여 다음 실행 시 비교 기준으로 사용합니다.

## 2. 사전 준비 사항

이전 가이드에서 준비했던 다음 정보들이 필요합니다.

* **구글 블로거 RSS 피드 주소**: `https://jiwon4u.blogspot.com/feeds/posts/default` 형식
* **텔레그램 봇 토큰 (TELEGRAM_BOT_TOKEN)**: 8605259314:AAE8l3-G9dte8eLyhNjwCY9gu-ZAUYRAMkI
* **텔레그램 채널 ID (TELEGRAM_CHAT_ID)**: @jiwon_4u

추가적으로 GitHub Actions를 위한 설정이 필요합니다.

## 3. GitHub 저장소 설정

### 3.1. 새 GitHub 저장소 생성

1. GitHub 웹사이트에 로그인합니다.
2. 새 저장소(New repository)를 생성합니다. 저장소 이름은 자유롭게 지정할 수 있습니다 (예: `blogger-telegram-notifier`).
3. 저장소를 `Public` 또는 `Private`으로 설정합니다. `Private`으로 설정하는 것을 권장합니다.
4. `Add a README file` 옵션을 선택하여 README 파일을 생성합니다.

### 3.2. 파일 업로드

생성된 저장소에 다음 두 파일을 업로드합니다.

1. **`blogger_telegram_notifier.py`**: 이전에 제공된 파이썬 스크립트 파일입니다.
2. **`.github/workflows/blogger_notifier.yml`**: GitHub Actions 워크플로우 정의 파일입니다. 저장소 루트에 `.github` 폴더를 만들고 그 안에 `workflows` 폴더를 만든 후 이 파일을 업로드해야 합니다.

### 3.3. `last_blogger_post.json` 파일 생성

스크립트가 마지막으로 확인한 글을 저장하기 위한 파일입니다. 이 파일은 스크립트가 처음 실행될 때 자동으로 생성되지 않으므로, 수동으로 생성해야 합니다.

1. GitHub 저장소에서 `Add file` -> `Create new file`을 클릭합니다.
2. 파일 이름을 `last_blogger_post.json`으로 입력합니다.
3. 파일 내용에 `{
 "last_link": "" }`를 입력합니다.
4. `Commit new file`을 클릭하여 저장소에 추가합니다.

### 3.4. GitHub Secrets 설정

민감한 정보(봇 토큰, 채팅 ID 등)는 코드에 직접 노출하지 않고 GitHub Secrets 기능을 사용하여 안전하게 관리해야 합니다.

1. GitHub 저장소 페이지에서 `Settings` 탭으로 이동합니다.
2. 왼쪽 메뉴에서 `Secrets and variables` -> `Actions`를 클릭합니다.
3. `New repository secret` 버튼을 클릭하여 다음 세 가지 Secret을 추가합니다.
    * **`BLOGGER_RSS_FEED_URL`**: 구글 블로거 RSS 피드 주소 (예: `https://본인블로그주소.blogspot.com/feeds/posts/default`)
    * **`TELEGRAM_BOT_TOKEN`**: 텔레그램 봇 토큰
    * **`TELEGRAM_CHAT_ID`**: 텔레그램 채널 ID
    * **`GITHUB_TOKEN`**: (이것은 자동으로 생성되는 토큰이므로 별도로 추가할 필요는 없지만, 워크플로우에서 `secrets.GITHUB_TOKEN`으로 접근할 수 있습니다. 다만, 파일 업데이트를 위해서는 `repo` 스코프가 필요하며, 기본 `GITHUB_TOKEN`은 `contents: write` 권한을 가집니다. 만약 권한 문제가 발생하면 `Personal Access Token`을 생성하여 사용해야 할 수도 있습니다. 여기서는 기본 `GITHUB_TOKEN`을 사용하도록 스크립트가 작성되었습니다.)

## 4. GitHub Actions 워크플로우 설명

`blogger_notifier.yml` 파일은 다음과 같이 구성됩니다.

```yaml
name: Blogger to Telegram Notifier

on:
  schedule:
    # Runs every 30 minutes
    - cron: '*/30 * * * *\'
  workflow_dispatch:

jobs:
  notify:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.x\'

    - name: Install dependencies
      run: pip install requests

    - name: Run Blogger Notifier
      env:
        BLOGGER_RSS_FEED_URL: ${{ secrets.BLOGGER_RSS_FEED_URL }}
        TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        GITHUB_REPOSITORY: ${{ github.repository }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: python blogger_telegram_notifier.py
```

* **`on: schedule`**: 이 워크플로우는 `cron` 표현식에 따라 30분마다 자동으로 실행됩니다. `workflow_dispatch`는 수동으로 워크플로우를 실행할 수 있게 합니다.
* **`jobs: notify`**: `ubuntu-latest` 환경에서 실행됩니다.
* **`actions/checkout@v4`**: 저장소의 코드를 워크플로우 실행 환경으로 가져옵니다.
* **`actions/setup-python@v5`**: 파이썬 환경을 설정합니다.
* **`pip install requests`**: 스크립트 실행에 필요한 `requests` 라이브러리를 설치합니다.
* **`Run Blogger Notifier`**: 환경 변수를 설정하고 파이썬 스크립트를 실행합니다. `secrets.BLOGGER_RSS_FEED_URL`, `secrets.TELEGRAM_BOT_TOKEN`, `secrets.TELEGRAM_CHAT_ID`는 GitHub Secrets에 설정한 값들을 참조합니다. `github.repository`는 현재 저장소의 이름을 자동으로 가져오며, `secrets.GITHUB_TOKEN`은 GitHub Actions에서 기본으로 제공하는 토큰으로 저장소에 파일을 업데이트하는 데 사용됩니다.

## 5. 작동 확인

모든 설정이 완료되면, GitHub 저장소의 `Actions` 탭에서 워크플로우의 실행 상태를 확인할 수 있습니다. 스케줄에 따라 자동으로 실행되거나, `workflow_dispatch`를 통해 수동으로 실행하여 즉시 테스트해 볼 수 있습니다.

새로운 블로그 글을 발행하거나 `last_blogger_post.json` 파일의 `last_link` 값을 임의로 변경한 후 워크플로우를 실행하여 텔레그램 알림이 정상적으로 오는지 확인해 보세요.

## 6. 주의사항

* `last_blogger_post.json` 파일은 스크립트가 마지막으로 확인한 글의 링크를 저장하는 용도로 사용됩니다. 이 파일이 없거나 내용이 올바르지 않으면 스크립트가 예상대로 작동하지 않을 수 있습니다.
* GitHub Actions의 무료 사용량에는 제한이 있습니다. 개인 계정의 경우 월 2,000분까지 무료로 사용할 수 있으며, 30분마다 실행 시 충분한 사용량입니다.
* `GITHUB_TOKEN`의 권한이 `contents: write`를 포함하는지 확인해야 `last_blogger_post.json` 파일을 업데이트할 수 있습니다. 일반적으로 기본 `GITHUB_TOKEN`은 이 권한을 가집니다.

이 가이드를 통해 GitHub Actions를 활용한 블로거-텔레그램 알림 시스템을 성공적으로 구축하시길 바랍니다.
