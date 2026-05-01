from __future__ import annotations

import html
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs"
OUT = OUT_DIR / "google_play_release_guide_20260501.docx"
AAB = ROOT / "android" / "app" / "build" / "outputs" / "bundle" / "release" / "app-release.aab"


def esc(value: str) -> str:
    return html.escape(str(value), quote=False)


def paragraph(text: str = "", style: str | None = None, bold: bool = False) -> str:
    pstyle = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    b = "<w:b/>" if bold else ""
    return f"<w:p>{pstyle}<w:r><w:rPr>{b}</w:rPr><w:t>{esc(text)}</w:t></w:r></w:p>"


def bullet(text: str) -> str:
    return (
        "<w:p><w:pPr><w:pStyle w:val=\"ListBullet\"/>"
        "<w:numPr><w:ilvl w:val=\"0\"/><w:numId w:val=\"1\"/></w:numPr></w:pPr>"
        f"<w:r><w:t>{esc(text)}</w:t></w:r></w:p>"
    )


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def table(rows: list[list[str]], widths: list[int] | None = None) -> str:
    cols = len(rows[0]) if rows else 0
    if widths is None:
        widths = [9360 // max(cols, 1)] * cols
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    body = [
        '<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="9360" w:type="dxa"/>'
        '<w:tblBorders><w:top w:val="single" w:sz="4" w:color="D0D7DE"/>'
        '<w:left w:val="single" w:sz="4" w:color="D0D7DE"/>'
        '<w:bottom w:val="single" w:sz="4" w:color="D0D7DE"/>'
        '<w:right w:val="single" w:sz="4" w:color="D0D7DE"/>'
        '<w:insideH w:val="single" w:sz="4" w:color="D0D7DE"/>'
        '<w:insideV w:val="single" w:sz="4" w:color="D0D7DE"/></w:tblBorders></w:tblPr>'
        f"<w:tblGrid>{grid}</w:tblGrid>"
    ]
    for row_index, row in enumerate(rows):
        body.append("<w:tr>")
        for cell_index, cell in enumerate(row):
            fill = '<w:shd w:fill="EAF1EE"/>' if row_index == 0 else ""
            bold = "<w:b/>" if row_index == 0 or cell_index == 0 else ""
            width = widths[cell_index]
            body.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{fill}'
                '<w:tcMar><w:top w:w="120" w:type="dxa"/><w:left w:w="140" w:type="dxa"/>'
                '<w:bottom w:w="120" w:type="dxa"/><w:right w:w="140" w:type="dxa"/></w:tcMar></w:tcPr>'
                f"<w:p><w:r><w:rPr>{bold}</w:rPr><w:t>{esc(cell)}</w:t></w:r></w:p></w:tc>"
            )
        body.append("</w:tr>")
    body.append("</w:tbl>")
    return "".join(body)


def styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/><w:qFormat/>
    <w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Malgun Gothic"/><w:sz w:val="22"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:qFormat/>
    <w:pPr><w:spacing w:after="240"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="0B4F4A"/><w:sz w:val="36"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Subtitle">
    <w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/><w:qFormat/>
    <w:rPr><w:color w:val="5A676F"/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="0F766E"/><w:sz w:val="30"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="180" w:after="80"/><w:outlineLvl w:val="1"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="1A2328"/><w:sz w:val="26"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="ListBullet">
    <w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/><w:qFormat/>
    <w:pPr><w:ind w:left="720" w:hanging="360"/><w:spacing w:after="80"/></w:pPr>
  </w:style>
  <w:style w:type="table" w:styleId="TableGrid">
    <w:name w:val="Table Grid"/><w:basedOn w:val="TableNormal"/><w:uiPriority w:val="59"/><w:qFormat/>
  </w:style>
</w:styles>"""


def content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
</Types>"""


def rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""


def document_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>"""


def numbering_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="1">
    <w:multiLevelType w:val="hybridMultilevel"/>
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="bullet"/>
      <w:lvlText w:val="•"/>
      <w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>
      <w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/></w:rPr>
    </w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>
</w:numbering>"""


def doc_xml() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    aab_size = f"{AAB.stat().st_size:,} bytes" if AAB.exists() else "not found"
    parts: list[str] = []
    parts.append(paragraph("Google Play 출시 진행 문서", "Title"))
    parts.append(paragraph("아파트 주차단속 시스템 Android 앱 출시용 운영 절차서", "Subtitle"))
    parts.append(table([
        ["항목", "값"],
        ["작성일", now],
        ["패키지명", "com.parkingmanagement.app"],
        ["앱 버전", "versionName 1.0.0 / versionCode 1"],
        ["운영 서버", "https://parking-man.onrender.com"],
        ["개인정보 처리방침", "https://parking-man.onrender.com/privacy"],
        ["AAB 파일", str(AAB)],
        ["AAB SHA-256", "E035C62409F63A812309F50B5199C6F5FFE6B0AF1137042500C8591E43880FE7"],
        ["AAB 크기", aab_size],
        ["현재 Git 커밋", "5db6324eef75abd0aa3de9ecfee103096d5d660e"],
    ], [2600, 6760]))

    parts.append(paragraph("1. 현재 준비 완료 상태", "Heading1"))
    for item in [
        "Release AAB 생성 완료: android/app/build/outputs/bundle/release/app-release.aab",
        "Render 운영 서버 live 확인 완료: /health 200 OK",
        "로그인 화면, 개인정보 처리방침, 데이터 삭제 안내 페이지 운영 URL 확인 완료",
        "Android targetSdk 35, minSdk 23, usesCleartextTraffic=false",
        "앱 권한: INTERNET, CAMERA",
        "Google Play Billing 상품 ID: parking_starter_monthly, parking_standard_monthly, parking_pro_monthly",
    ]:
        parts.append(bullet(item))

    parts.append(paragraph("2. Play Console에서 먼저 확인할 항목", "Heading1"))
    parts.append(table([
        ["구분", "입력 또는 확인값", "상태"],
        ["앱 만들기", "앱 이름: 아파트 주차단속 시스템 / 기본 언어: 한국어 / 앱 또는 게임: 앱", "콘솔에서 확인 필요"],
        ["패키지명", "com.parkingmanagement.app", "AAB와 일치"],
        ["스토어 등록정보", "간단한 설명, 전체 설명, 앱 아이콘 512x512, 스크린샷", "콘솔 입력 필요"],
        ["개인정보 처리방침 URL", "https://parking-man.onrender.com/privacy", "준비 완료"],
        ["앱 액세스", "로그인이 필요한 앱: 예. 테스트 계정 제공 필요", "콘솔 입력 필요"],
        ["데이터 보안", "계정, 차량, 사진, 위치/업무 기록 처리 사실 기재", "콘솔 입력 필요"],
        ["타겟층/콘텐츠 등급", "업무용 관리 앱 기준으로 설문 작성", "콘솔 입력 필요"],
        ["가격 및 배포 국가", "한국 우선 권장", "콘솔 선택 필요"],
    ], [1900, 5300, 2160]))

    parts.append(paragraph("3. 출시 트랙 권장 순서", "Heading1"))
    parts.append(paragraph("처음 공개 전에는 내부 테스트 → 비공개 테스트 → 프로덕션 순서를 권장합니다. 업무용 앱이므로 실제 관리자와 현장 담당자 2~5명으로 먼저 점검하는 것이 안전합니다."))
    parts.append(table([
        ["순서", "트랙", "목적", "판정 기준"],
        ["1", "Internal testing", "설치, 로그인, 촬영, 직접조회, 저장, 구독 버튼 동작 확인", "치명 오류 없음"],
        ["2", "Closed testing", "실제 현장 단말에서 속도와 화면 폭 확인", "주요 단말 2종 이상 통과"],
        ["3", "Production", "운영 배포", "관리자 승인 후 진행"],
    ], [900, 1900, 4300, 2260]))

    parts.append(paragraph("4. AAB 업로드 절차", "Heading1"))
    for item in [
        "Play Console > 앱 선택 > 테스트 또는 프로덕션 트랙 > 새 버전 만들기",
        "app-release.aab 업로드",
        "출시명: 1.0.0 또는 1.0.0-internal",
        "출시 노트 입력: 초기 출시. 번호판 촬영, 등록차량 조회, 단속 기록 저장, CCTV 검색요청, 관리자 차량DB 관리 기능을 제공합니다.",
        "오류 요약이 있으면 모든 Error를 해결한 뒤 저장 또는 검토 요청",
        "내부 테스트는 테스터 이메일을 추가하고 테스트 링크를 배포",
    ]:
        parts.append(bullet(item))

    parts.append(paragraph("5. 데이터 보안 섹션 입력 가이드", "Heading1"))
    parts.append(table([
        ["데이터 유형", "수집 여부", "목적", "공유 여부"],
        ["개인 정보/계정", "예", "로그인, 권한 관리, 업무 이력", "아니오"],
        ["사진/이미지", "예", "번호판 촬영 및 단속 증빙", "아니오"],
        ["위치/장소 정보", "예", "단속 위치 기록", "아니오"],
        ["차량 정보", "예", "등록차량 조회와 단속 판단", "아니오"],
        ["결제 정보", "Google Play 처리", "구독 상태 확인", "Google Play 결제 시스템 사용"],
    ], [2100, 1500, 3900, 1860]))
    parts.append(paragraph("데이터 삭제 안내는 /privacy 페이지에 공개되어 있으며, 관리자가 사용자 관리 화면에서 계정을 삭제할 수 있습니다. 차량 및 단속 기록은 관리 주체의 운영 기준과 법적 보관 필요성에 따라 처리합니다."))

    parts.append(paragraph("6. 출시 전 최종 점검 명령", "Heading1"))
    for item in [
        "python -m unittest discover -s backend/tests -p \"test_*.py\" -v",
        "node --check backend/app/static/app.js",
        "gradle.bat bundleRelease (작업 위치: android)",
        "powershell -ExecutionPolicy Bypass -File .\\tools\\check_render_parking.ps1 -Deploy",
    ]:
        parts.append(bullet(item))

    parts.append(paragraph("7. 출시 후 확인", "Heading1"))
    for item in [
        "Play Console에서 검토 상태가 In review, Ready to publish, Published 중 어디인지 확인",
        "테스터 또는 실제 설치 단말에서 앱 실행 후 로그인 확인",
        "번호판 촬영 권한 요청이 정상 표시되는지 확인",
        "운영 서버 /health 및 /privacy 접근 확인",
        "구독 상품을 사용하는 경우 Play Console 상품 상태와 서버 Billing 화면의 상품 ID가 일치하는지 확인",
    ]:
        parts.append(bullet(item))

    parts.append(paragraph("8. 현재 직접 제출이 멈춘 지점", "Heading1"))
    parts.append(paragraph("이 환경에는 Play Console 브라우저 로그인 세션이나 Google Play Android Publisher 업로드 권한 JSON이 연결되어 있지 않습니다. 따라서 AAB 파일 생성과 운영 서버 검증까지는 완료했지만, Play Console의 최종 업로드/검토 요청 버튼은 콘솔 접근 권한이 있는 브라우저에서 수행해야 합니다. 서비스 계정 JSON을 로컬에 제공하면 Android Publisher API를 이용한 트랙 업로드 자동화도 별도로 구성할 수 있습니다."))

    parts.append(paragraph("9. 공식 참고 링크", "Heading1"))
    for item in [
        "Prepare and roll out a release: https://support.google.com/googleplay/android-developer/answer/9859348",
        "Data safety form: https://support.google.com/googleplay/android-developer/answer/10787469",
        "Target API requirements: https://support.google.com/googleplay/android-developer/answer/11926878",
        "User data policy: https://support.google.com/googleplay/android-developer/answer/10144311",
        "Account deletion requirements: https://support.google.com/googleplay/android-developer/answer/13327111",
    ]:
        parts.append(bullet(item))

    body = "".join(parts)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {body}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types_xml())
        docx.writestr("_rels/.rels", rels_xml())
        docx.writestr("word/_rels/document.xml.rels", document_rels_xml())
        docx.writestr("word/styles.xml", styles_xml())
        docx.writestr("word/numbering.xml", numbering_xml())
        docx.writestr("word/document.xml", doc_xml())
    print(OUT)


if __name__ == "__main__":
    main()
