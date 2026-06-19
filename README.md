<div align="center">

<img src="assets/readme/hero.svg" width="100%" alt="Danim — 세상의 모든 여행이 연결되는 곳"/>

<br/>

**여행을 기록하고, 여행자와 연결되고, 새로운 여행을 발견하세요.**

<br/>

[![Python](https://img.shields.io/badge/Python_3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Django](https://img.shields.io/badge/Django_5-092E20?style=for-the-badge&logo=django&logoColor=white)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-316192?style=for-the-badge&logo=postgresql&logoColor=white)](#)
[![Redis](https://img.shields.io/badge/Redis_7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](#)
[![AWS](https://img.shields.io/badge/AWS-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](#)

<br/>

[🌍 서비스 바로가기](#) &nbsp;·&nbsp; [📖 API 문서](#) &nbsp;·&nbsp; [🐛 버그 제보](#) &nbsp;·&nbsp; [💬 피드백](#)

<br/>

</div>

---

<br/>

## 🤔 왜 다님인가요?

여행을 다녀와도 사진은 카메라 롤에만 잠들고, 좋았던 식당은 메모장에만 남아 있습니다.
인스타그램엔 올리기엔 너무 길고, 블로그는 쓰기엔 너무 번거롭습니다.

**다님은 이 공백을 채웁니다.**

| 기존의 불편함 | 다님의 해결 |
|---|---|
| 여행 기록이 사진첩에 흩어진다 | 일정·장소·사진을 한 곳에 구조화하여 기록 |
| 같은 지역 여행자를 찾기 어렵다 | 위치 기반 콘텐츠로 여행자끼리 자연스럽게 연결 |
| 좋은 여행지를 발견하기 어렵다 | 팔로우 피드와 여행지 태그로 새로운 장소 발견 |
| 여행 후기가 플랫폼에 갇힌다 | 내 기록이 내 것으로 남고 커뮤니티와 공유 |

<br/>

---

<br/>

## ✨ 핵심 기능

<br/>

> 다님은 여행의 모든 순간을 함께합니다.

<br/>

**📸 여행 기록**
일정, 장소, 사진을 하나의 게시글로 묶어 나만의 여행 아카이브를 만드세요.
위도·경도 기반 여행지 태그로 지도 위에 내 발자국을 남길 수 있습니다.

<br/>

**🗺️ 위치 기반 콘텐츠**
같은 도시, 같은 골목을 걸은 여행자의 기록을 만나보세요.
낯선 여행지에서 현지인보다 더 정확한 정보를 얻을 수 있습니다.

<br/>

**👥 여행자 커뮤니티**
마음이 맞는 여행자를 팔로우하고, 서로의 여행 스타일을 발견하세요.
배낭여행객부터 디지털 노마드까지, 모든 여행자를 위한 공간입니다.

<br/>

**💬 실시간 DM**
좋은 식당을 발견했나요? DM으로 바로 공유하세요.
WebSocket 기반 실시간 1:1 메시지로 여행 정보를 즉시 나눌 수 있습니다.

<br/>

**🔔 실시간 알림**
내 게시글에 좋아요·댓글이 달리거나, 새 팔로워가 생기면 즉시 알림을 받습니다.

<br/>

**🖼️ 사진 업로드**
AWS S3 Presigned URL 방식으로 고화질 여행 사진을 빠르게 업로드하세요.

<br/>

---

<br/>

## 🚶 유저 여정

<div align="center">

<img src="assets/readme/user-journey.svg" width="100%" alt="User Journey"/>

</div>

<br/>

---

<br/>

## 🏗️ 아키텍처

<div align="center">

<img src="assets/readme/architecture.svg" width="100%" alt="Architecture"/>

</div>

<br/>

### WebSocket 인증 흐름

<div align="center">

<img src="assets/readme/websocket-flow.svg" width="100%" alt="WebSocket Auth Flow"/>

</div>

<br/>

---

<br/>

## 🛠️ 기술 스택

### Backend
![Python](https://img.shields.io/badge/Python_3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django_5-092E20?style=flat-square&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/Django_REST_Framework-ff1709?style=flat-square&logo=django&logoColor=white)
![Channels](https://img.shields.io/badge/Django_Channels-092E20?style=flat-square&logo=django&logoColor=white)
![SimpleJWT](https://img.shields.io/badge/Simple_JWT-000000?style=flat-square&logo=jsonwebtokens&logoColor=white)
![uv](https://img.shields.io/badge/uv-DE5FE9?style=flat-square)

### Database & Cache
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-316192?style=flat-square&logo=postgresql&logoColor=white)
![pgvector](https://img.shields.io/badge/pgvector-316192?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis_7-DC382D?style=flat-square&logo=redis&logoColor=white)

### Infrastructure
![AWS EC2](https://img.shields.io/badge/AWS_EC2-FF9900?style=flat-square&logo=amazonec2&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS_S3-569A31?style=flat-square&logo=amazons3&logoColor=white)
![AWS RDS](https://img.shields.io/badge/AWS_RDS-527FFF?style=flat-square&logo=amazonrds&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=flat-square&logo=nginx&logoColor=white)

### DevOps & Monitoring
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![Sentry](https://img.shields.io/badge/Sentry-362D59?style=flat-square&logo=sentry&logoColor=white)

<br/>

---

<br/>

## 📸 스크린샷

<br/>

| 피드 | 게시글 상세 | DM |
|:---:|:---:|:---:|
| `이미지 준비 중` | `이미지 준비 중` | `이미지 준비 중` |

| 프로필 | 알림 | 검색 |
|:---:|:---:|:---:|
| `이미지 준비 중` | `이미지 준비 중` | `이미지 준비 중` |

<br/>

---

<br/>

## 🗺️ 로드맵

<div align="center">

<img src="assets/readme/roadmap.svg" width="100%" alt="Roadmap"/>

</div>

<br/>

---

<br/>

## 👩‍💻 팀

<br/>

> 다님은 여행을 사랑하는 개발자들이 만들고 있습니다.

<br/>

| 역할 | 이름 | GitHub |
|------|------|--------|
| | | |
| | | |
| | | |
| | | |
| | | |

<br/>

---

<br/>

## 📄 라이선스

이 프로젝트는 내부 서비스용으로 별도 라이선스를 적용하지 않습니다.
코드 무단 복제 및 배포를 금합니다.

<br/>

---

<br/>

## 📬 문의

서비스 관련 문의나 협업 제안은 아래로 연락주세요.

- 이메일: `cksdufqqpu@gmail.com`
- GitHub Issues: [danim-travel/danim-backend](../../issues)

<br/>

<div align="center">

<img src="assets/readme/footer.svg" width="100%" alt="footer"/>

*세상의 모든 여행이 다님과 함께합니다* ✈️

</div>
