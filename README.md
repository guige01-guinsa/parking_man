# Apartment Parking Enforcement

1100세대 아파트 관리사무소를 위한 현장형 주차단속 시스템입니다. 스마트폰에서 번호판을 촬영하고, OCR로 번호판 후보를 추출한 뒤 등록차량 여부를 즉시 판단할 수 있습니다. 등록차량 원본은 지정 폴더의 Excel 파일에서 읽어와 로컬 DB로 동기화합니다.

## 왜 이렇게 구성했는가

- 현장 단속은 스마트폰 브라우저/PWA가 가장 빠르게 배포됩니다.
- Excel을 매번 직접 검색하는 방식보다, 서버가 지정 폴더를 읽어 DB로 동기화하는 방식이 빠르고 안정적입니다.
- 번호판 판독은 완전 자동보다 `OCR 보조 + 직원 최종 확인`이 실제 운영에서 오탐을 줄입니다.

## 추천 개발/운영 구성

- Backend: FastAPI + SQLite
- OCR: Tesseract OCR (`kor+eng`)
- Vehicle source: 지정 폴더의 `xlsx` / `xlsm`
- Frontend: 모바일 우선 반응형 웹 UI
- 배포: Windows PowerShell 실행 또는 Docker

## 빠른 시작

1. 환경파일 생성
   - `copy backend\.env.example backend\.env`
2. 등록차량 Excel 파일 배치
   - `backend\imports\` 폴더에 관리사무소 Excel 파일을 넣습니다.
3. 개발 서버 실행
   - `pwsh -File backend\run.ps1 -Reload`
4. 접속
   - `http://localhost:8011`

기본 계정:

- `admin / admin1234`
- `guard / guard1234`
- `viewer / viewer1234`

## Excel 컬럼 예시

다음 헤더를 자동 인식합니다. 한국어/영문 혼용도 일부 허용합니다.

- `차량번호`
- `동호수`
- `차주`
- `연락처`
- `상태`
- `시작일`
- `만료일`
- `비고`

## 더 좋은 운영 방법

- Excel은 원본 유지, 시스템은 주기 동기화: 실시간 조회는 DB에서 수행
- OCR 결과는 자동 확정하지 말고 현장 직원이 1회 확인
- 추후 확장:
  - 차단 차량 자동 경고음
  - 경비실 태블릿 대시보드
  - 무인 차단기/ANPR 카메라 연동

## 운영 메모

- 운영 배포 시에는 `backend/.env.production.example`를 기준으로 환경변수를 구성합니다.
- Docker 배포는 루트의 `docker-compose.yml`을 사용합니다.
- Excel 원본은 `backend/imports/`에 두고, 관리자 화면에서 다시 읽기를 실행하면 됩니다.
