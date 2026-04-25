# Android Play Billing Wrapper

이 프로젝트는 주차관리 웹앱을 Google Play에 올리기 위한 Android WebView 래퍼입니다.

## 빌드 전 설정

1. Android Studio에서 `android/` 폴더를 엽니다.
2. Play Console 앱 패키지명을 `android/app/build.gradle`의 `applicationId`와 동일하게 맞춥니다.
3. Play Console에 다음 구독 상품을 만듭니다.
   - `parking_starter_monthly`
   - `parking_standard_monthly`
   - `parking_pro_monthly`
4. 상품 ID를 바꾸면 `android/app/build.gradle`의 `STARTER_PRODUCT_ID`, `STANDARD_PRODUCT_ID`, `PRO_PRODUCT_ID`와 서버 환경변수 `PARKING_GOOGLE_PLAY_PRODUCT_*`를 같이 바꿉니다.
5. 릴리스 서명 키는 저장소에 커밋하지 말고 Android Studio 또는 CI 비밀값으로 설정합니다.

## 릴리스 빌드 산출물

- Play Console 업로드용 AAB: `android/app/build/outputs/bundle/release/app-release.aab`
- 테스트 설치용 APK: `android/app/build/outputs/apk/release/app-release.apk`
- 로컬 서명 정보는 `android/keystore.properties`와 `android/parking-release.jks`에 저장되며 `.gitignore`로 제외됩니다. 이 두 파일을 잃어버리면 같은 앱의 후속 업데이트 서명이 불가능할 수 있으므로 별도로 백업해야 합니다.

명령줄 빌드:

```powershell
gradle --no-daemon :app:bundleRelease
gradle --no-daemon :app:assembleRelease
```

## 결제 흐름

1. Android 앱이 BillingClient로 구독 상품을 조회합니다.
2. 웹 관리자 화면의 요금제 카드에서 `Google Play 구독` 버튼을 누르면 Android 네이티브 결제 화면이 열립니다.
3. 구매가 완료되면 Android 앱이 구매 토큰을 웹 화면에 전달합니다.
4. 웹 화면은 서버 `/api/billing/google-play/verify`로 구매 토큰을 보내고, 서버가 Google Play Developer API로 검증한 뒤 요금제를 적용합니다.
