# 논문 매일 구독 — GitHub Actions 버전 (완전 초보용 가이드)

GitHub가 매일 자동으로 클라우드에서 코드를 실행해서, 새 논문(제목·저자·초록)을 모아 당신의 메일로 보냅니다. **노트북을 켤 필요 없음, 결제 없음, API 키 없음.** GitHub 지식이 전혀 없어도 아래 순서대로 따라 하시면 됩니다.

수집 저널 (7종, ISSN 검증 완료):
- Computers & Education
- International Journal of Educational Technology in Higher Education
- Interactive Learning Environments
- Journal of Computer Assisted Learning
- Education and Information Technologies
- Journal of Research on Technology in Education
- Educational Technology & Society

---

## 0단계: 준비물 (2가지)

### A) GitHub 계정 만들기
1. https://github.com 접속 → "Sign up" 클릭
2. 이메일/비밀번호 입력하고 가입 완료

### B) Gmail 앱 비밀번호 만들기 (메일 발송용, 16자리)
> 일반 Gmail 비밀번호가 아닙니다. GitHub가 메일을 보낼 때 쓰는 전용 비밀번호입니다.
1. https://myaccount.google.com → 왼쪽 "보안"
2. "2단계 인증"이 안 켜져 있으면 먼저 켜기 (전화번호 인증 필요)
3. 2단계 인증 켠 후, 같은 보안 페이지에서 "앱 비밀번호" 검색/클릭
4. 앱 이름에 `paper-sub` 입력 → "만들기"
5. 화면에 나온 **16자리 비밀번호**를 메모해두기 (띄어쓰기 없이)

---

## 1단계: GitHub에 새 저장소(repository) 만들기

1. GitHub 로그인 후, 화면 오른쪽 위 **"+" 아이콘** → **"New repository"**
2. 설정:
   - **Repository name**: `paper-sub`
   - **Public** 선택 (공개 저장소는 Actions가 무료 무제한). 코드에 비밀번호는 없으니 안전합니다.
   - 나머지는 그대로 두고 **"Create repository"** 클릭

---

## 2단계: 코드 파일 올리기

1. 이 zip을 풀면 나오는 폴더(`paper-sub-github`) 안의 파일들을 확인합니다.
   파일 목록: `fetch.py`, `digest.py`, `mailer.py`, `config.yaml`, `requirements.txt`, `README.md`, `.gitignore`
2. GitHub 저장소 페이지에서 **"Add file"** → **"Upload files"**
3. zip 푼 폴더를 열고, 위 파일들을 **전부 드래그**해서 GitHub 점선 상자에 놓기
   (`.gitignore`는 숨김파일이라 Finder에 안 보일 수 있음 → 안 올려도 됩니다. 올리면 더 좋음.)
4. 아래 **"Commit changes"** 초록 버튼 클릭

---

## 3단계: GitHub Actions 자동실행 파일 만들기 (가장 중요)

이 파일이 "매일 실행"을 담당합니다.

1. 저장소 페이지에서 **"Add file"** → **"Create new file"**
2. **파일이름 칸**에 정확히 아래를 입력 (슬래시를 치면 자동으로 폴더가 만들어집니다):
   ```
   .github/workflows/daily.yml
   ```
3. 큰 입력칸에 **아래 내용을 전부 복사해서 붙여넣기**:

```yaml
name: Daily Paper Digest

on:
  schedule:
    - cron: "0 12 * * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  digest:
    runs-on: ubuntu-latest
    steps:
      - name: 코드 가져오기
        uses: actions/checkout@v4

      - name: Python 설치
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: 패키지 설치
        run: pip install -r requirements.txt

      - name: 논문 수집 및 메일 발송
        env:
          EMAIL_ENABLED: "true"
          SMTP_HOST: smtp.gmail.com
          SMTP_PORT: "587"
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
          SUBJECT_PREFIX: "[논문구독]"
        run: python digest.py config.yaml

      - name: 결과 저장소에 저장
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add seen_dois.txt digests/ 2>/dev/null || true
          git commit -m "digest $(date -u +%Y-%m-%d)" || echo "커밋할 변경사항 없음"
          git push || echo "푸시할 것 없음"
```

4. **"Commit changes"** 클릭

> 시간 변경: `cron: "0 12 * * *"` 에서 `12`가 UTC 12시(=미 동부 8시)입니다. 예를 들어 한국 시간 오전 9시로 바꾸려면 `0 0 * * *`(UTC 0시)로 수정하면 됩니다.

---

## 4단계: 메일 비밀번호를 GitHub에 안전하게 등록 (Secrets)

> 이 단계를 안 하면 메일이 안 갑니다. 비밀번호는 암호화되어 저장되고, 코드에 노출되지 않습니다.

1. 저장소 위쪽 **"Settings"** 탭 클릭
2. 왼쪽 메뉴 **"Secrets and variables"** → **"Actions"**
3. **"New repository secret"** 버튼 클릭해서 아래 3개를 각각 만듭니다:

   | Name (정확히) | Secret (값) |
   |---|---|
   | `SMTP_USER` | 본인 Gmail 주소 (예: jueunshin.us@gmail.com) |
   | `SMTP_PASSWORD` | 0단계에서 만든 16자리 앱 비밀번호 |
   | `EMAIL_TO` | 다이제스트를 받을 메일 주소 (보통 본인 Gmail) |

   - 각각 치고 **"Add secret"** 클릭 → 3개 모두 추가되었는지 확인

---

## 5단계: 지금 바로 테스트 실행 (매일 기다릴 필요 없이)

1. 저장소 위쪽 **"Actions"** 탭 클릭
2. 왼쪽 목록에서 **"Daily Paper Digest"** 클릭
3. 오른쪽 노란색 **"Run workflow"** 버튼 클릭 → 다시 **"Run workflow"** 클릭
4. 잠시 후 아래에 "Daily Paper Digest" 실행이 나타남 (빙글빙글 → 노란 점)
5. 1~2분 뒤 **초록 체크(✓)** 로 바뀌면 성공 → 메일함(스팸함도) 확인

> 빨간 X가 뜨면: 해당 실행 클릭 → "digest" 클릭 → 빨간 줄의 에러 메시지 확인 (아래 문제해결 참고)

---

## 6단계: 끝 — 매일 자동 실행

이제 매일 미 동부 시간 8시쯤 자동으로 실행되어 메일이 옵니다.
- Actions는 매일 자동 실행되지만, GitHub 사정으로 몇 분~수십 분 늦을 수 있습니다 (정상).
- 실행 결과(`digests/digest-날짜.md`)와 중복방지 기록(`seen_dois.txt`)이 저장소에 자동 저장되어, 같은 논문이 또 오지 않습니다. 저장소의 `digests` 폴더에서 과거 다이제스트도 볼 수 있습니다.

---

## 저널 추가/삭제 방법

나중에 저널을 바꾸고 싶으면:
1. 저장소에서 `config.yaml` 클릭 → 오른쪽 **연필 아이콘(✏️ Edit)**
2. `journals:` 아래 줄을 추가하거나 삭제
   - 형식: `  저널이름: "ISSN번호"` (들여쓰기 2칸 유지)
3. **"Commit changes"** 클릭 → 다음 실행부터 적용

ISSN은 해당 저널 홈페이지의 About 페이지에서 확인 가능합니다.

---

## 문제해결

- **메일이 안 와요**: ① Actions 탭에서 초록 ✓인지 확인 ② 4단계 Secrets 3개 정확히 등록했는지 확인 ③ Gmail 스팸함 확인 ④ 앱 비밀번호 16자리가 맞는지 확인 (계정 비밀번호 아님)
- **빨간 X, "Insufficient budget" (OpenAlex)**: OpenAlex 무료 하루 할당량을 같은 IP 공유로 소진한 경우. 다음 날 자동 복구됩니다. 다음 실행은 정상입니다.
- **"새 논문이 없습니다"**: 최근 며칠 새 논문이 없는 것. 정상입니다.
- **cron 시간이 이상해요**: 3단계의 `cron: "0 12 * * *"` 숫자를 바꾸세요. 형식: `분 시 * * *` (UTC 기준).
