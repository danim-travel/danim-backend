# danim-backend
여행자들만을 위한 일정 공유 커뮤니티(SNS)

---

## 기술 스택
- **언어**: Python 3.13
- **프레임워크**: Django 6 + Django REST Framework
- **인증**: Simple JWT
- **DB**: PostgreSQL 16
- **캐시**: Redis 7
- **의존성 관리**: uv
- **인프라**: Docker, AWS EC2, AWS S3

---

## 브랜치 전략
```
main      → 실배포 브랜치 (직접 push 금지)
develop   → 개발 통합 브랜치 (직접 push 금지)
feat/기능명 → 개인 작업 브랜치
```
**작업 흐름**: `feat/기능명` → `develop` PR → 리뷰 후 머지 → `main` PR → 배포

---

## 커밋 메시지 컨벤션

> 자세한 내용은 [.github/COMMIT_CONVENTION.md](.github/COMMIT_CONVENTION.md) 참고

### 커밋 템플릿 설정 (최초 1회)
```bash
git config commit.template .github/commit_template.txt
```
설정 후 PyCharm 커밋 창에 템플릿이 자동으로 표시됩니다.
```
feat: 새로운 기능 추가
fix: 버그 수정
refactor: 코드 리팩토링
test: 테스트 코드
docs: 문서 수정
chore: 빌드, 설정 파일 수정
style: 코드 포맷팅 (기능 변경 없음)
```
**예시**
```
feat: 이메일 회원가입 API 구현
fix: 토큰 재발급 중복 발급 버그 수정
```

---

## 로컬 개발 환경 세팅

### 사전 준비
아래 두 가지가 설치되어 있어야 합니다.

**Docker Desktop**
[Docker Desktop 다운로드](https://www.docker.com/products/docker-desktop/) 에서 설치합니다.

**uv**
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

설치 확인:
```bash
docker --version
uv --version
```

---

### 1. 레포지토리 클론
```bash
git clone -b develop https://github.com/danim-travel/danim-backend.git
cd danim-backend
```

---

### 3. 의존성 설치
```bash
uv sync
```
`uv.lock` 기준으로 전체 패키지를 설치합니다. 팀원 전원 동일한 버전으로 설치됩니다.

---

### 4. 환경변수 설정
팀 채팅방에서 공유받은 `.env` 파일을 프로젝트 루트에 생성합니다.
```bash
cp .env.example .env
```
`.env` 파일을 열어서 아래 값들을 채워주세요. (실제 값은 팀장에게 요청)
```
SECRET_KEY=

DB_NAME=danim
DB_USER=danim
DB_PASSWORD=danim
DB_HOST=db
DB_PORT=5432

REDIS_URL=redis://redis:6379/1
REDIS_AUTH_URL=redis://redis:6379/2
```

---

### 5. Docker 실행
```bash
docker compose up --build
```
처음 실행 시 이미지 빌드로 시간이 걸립니다. 이후 실행부터는 빠릅니다.

아래 세 개가 모두 실행되면 정상입니다:
```
✔ Container danim-backend-db-1      Running
✔ Container danim-backend-redis-1   Running
✔ Container danim-backend-django-1  Running
```

---

### 6. DB 마이그레이션
새 터미널을 열고 아래 명령어를 실행합니다:
```bash
docker compose exec django uv run python manage.py migrate
```

---

### 7. 서버 확인
브라우저에서 아래 주소로 접속합니다:
- 서버 확인: `http://localhost:8000/hello/`
- API 문서: `http://localhost:8000/api/schema/swagger-ui/`

`{"hello": true}` 응답이 오면 정상입니다.

---

## 자주 쓰는 명령어

### Docker
```bash
# 실행 (백그라운드)
docker compose up -d

# 실행 (로그 보면서)
docker compose up

# 빌드 후 실행 (패키지 추가했을 때)
docker compose up --build

# 중지
docker compose down

# 로그 확인
docker compose logs django
```

### Django
```bash
# 마이그레이션 파일 생성 (모델 변경 후 로컬에서 실행 → 생성된 파일 깃에 커밋)
uv run python manage.py makemigrations

# 마이그레이션 적용 (각자 로컬 DB에 적용)
docker compose exec django uv run python manage.py migrate
```

### 패키지 추가
```bash
uv add 패키지명
```
추가 후 반드시 `pyproject.toml`과 `uv.lock`을 같이 커밋해주세요.  
다른 팀원들은 `docker compose up --build`로 동기화합니다.

---

## 개발 시작 전 체크리스트
- [ ] Docker Desktop 실행 중인지 확인
- [ ] `git pull origin develop` 으로 최신 코드 받기
- [ ] 패키지 변경 있으면 `docker compose up --build`
- [ ] 마이그레이션 변경 있으면 `migrate` 실행
