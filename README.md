# 🖊️ 시인 홈페이지

Flask + SQLite로 만든 시인 개인 홈페이지입니다.

---

## ⚡ 빠른 시작

```bash
# 1. 압축 해제 후 폴더 진입
cd poet_site

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 실행
python app.py
```

브라우저에서 **http://localhost:5000** 접속

---

## 🔑 관리자 접속

| 항목 | 값 |
|------|-----|
| URL | http://localhost:5000/admin/login |
| 초기 비밀번호 | `admin1234` |

> ⚠️ **운영 환경에서는 반드시 변경하세요!**
> ```bash
> export SECRET_KEY=랜덤한긴문자열
> export ADMIN_PASSWORD=강력한비밀번호
> python app.py
> ```

---

## 📋 기능 목록

### 공개 페이지

| 경로 | 설명 |
|------|------|
| `/` | 홈 — 히어로, 최근 시, 시집, 연혁 |
| `/works` | 작품/약력 전체 + 연혁·수상 탭 |
| `/poems` | 시 목록 (시집별 필터) |
| `/poem/<id>` | 시 상세 + 이전/다음 네비 |
| `/guestbook` | 방명록 (익명 등록·수정·삭제) |
| `/search?q=검색어` | 시 제목·내용 전문 검색 |

### 관리자 페이지

| 메뉴 | 기능 |
|------|------|
| 대시보드 | 통계 카드 + 최근 방명록 |
| 프로필 관리 | 이름·사진·약력·소개문구 |
| 연혁 관리 | 연혁/수상 추가·삭제 |
| 시집 관리 | 시집 추가(표지 이미지)·삭제 |
| 시 관리 | 등록·수정·삭제·공개/비공개 토글 |

---

## 🗂️ 파일 구조

```
poet_site/
├── app.py                    ← Flask 백엔드 (전체 로직)
├── requirements.txt
├── gunicorn.conf.py          ← 운영 서버 설정
├── Dockerfile
├── .env.example
├── static/
│   ├── css/style.css         ← 전체 스타일
│   ├── js/main.js            ← 인터랙션
│   └── uploads/              ← 업로드 이미지 (자동 생성)
└── templates/
    ├── layout.html           ← 공통 헤더·푸터
    ├── index.html            ← 홈
    ├── works.html            ← 작품/약력
    ← poems.html             ← 시 목록
    ├── poem_detail.html      ← 시 상세
    ├── guestbook.html        ← 방명록
    ├── search.html           ← 검색
    ├── 404.html / 500.html   ← 에러 페이지
    └── admin/                ← 관리자 (6개 파일)
```

---

## 🐳 도커로 실행 (선택)

```bash
docker build -t poet-site .
docker run -p 8000:8000 \
  -e SECRET_KEY=랜덤문자열 \
  -e ADMIN_PASSWORD=비밀번호 \
  -v $(pwd)/static/uploads:/app/static/uploads \
  -v $(pwd)/poet.db:/app/poet.db \
  poet-site
```

---

## 🎨 커스터마이징

### 색상 변경
`static/css/style.css` 파일 상단의 `:root` 변수 수정:
```css
--accent: #8B6F4E;      /* 포인트 색상 (현재: 브라운) */
--bg:     #FAFAF6;      /* 배경색 (현재: 따뜻한 흰색) */
```

### 폰트 변경
`:root`의 `--font-serif` / `--font-sans` 변수와
`<head>`의 Google Fonts 링크를 함께 수정하세요.

### 초기 데이터 수정
`app.py`의 `init_db()` 함수 안에서 기본 프로필·연혁·시·시집 데이터를 수정할 수 있습니다.
이미 DB가 생성된 경우 `poet.db`를 삭제 후 재시작하면 초기화됩니다.
