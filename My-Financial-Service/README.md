# 💰 Financial Product Management Service

### 📖 Project Overview
사용자의 관심 금융 상품을 관리하고, 커뮤니티 기능을 제공하는 금융 포트폴리오 웹 서비스입니다.
Django의 인증 시스템과 데이터베이스 관계(1:N, N:M)를 활용하여 안정적인 백엔드를 구축하였으며, Bootstrap을 활용해 직관적인 UI를 구현했습니다.

### 🛠 Tech Stack
- **Backend**: Python 3.9, Django 4.2
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Collaboration**: Git, GitLab

### ✨ Key Features

#### 1. Authentication (회원 관리)
- Django built-in `User` 모델을 활용한 회원가입, 로그인, 로그아웃
- `@login_required` 데코레이터를 활용한 접근 권한 제어

#### 2. Financial Products (금융 상품 관리)
- 금융 상품 데이터 모델링 및 DB 저장
- 사용자별 '관심 상품' 담기 기능 (N:M 관계 구현)
- 나의 관심 상품 모아보기 페이지 구현

#### 3. Community (게시판)
- 게시글 작성, 조회, 수정, 삭제 (CRUD)
- 게시글에 대한 댓글 작성 및 삭제 기능
- 게시글 좋아요 기능 비동기 처리

#### 4. AI & UX
- 생성형 AI를 활용한 금융 상품 추천 보조 기능
- Bootstrap 5 기반의 반응형 레이아웃 및 디자인

---
*Developed during SSAFY 14th Software Project Track.*