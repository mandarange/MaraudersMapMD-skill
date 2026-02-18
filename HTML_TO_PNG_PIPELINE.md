# HTML → 브라우저 캡처 → PNG 안정 파이프라인

다른 스킬/워크플로우에서 재사용 가능하도록 범용 원리와 규칙만 추출한 레퍼런스.

---

## 왜 이 파이프라인이 필요한가

AI 에이전트가 ASCII 다이어그램, 차트, 레이아웃 등을 이미지로 변환할 때 흔히 발생하는 실패 모드:

| 실패 모드 | 원인 | 이 파이프라인의 해결책 |
|---|---|---|
| PNG 파일이 아예 안 생김 | 외부 스크립트 의존 (puppeteer, playwright CLI 등) | 브라우저 도구 하나로 원샷 완결 |
| 이미지에 불필요한 여백 | full-page 스크린샷 + body padding | element screenshot + CSS 제로 패딩 + 후처리 크롭 |
| 다이어그램 가장자리 잘림 | viewport가 콘텐츠보다 작음 | 바운딩박스 측정 → viewport 자동 확장 |
| 캡처 중 소스 파일 삭제 | temp HTML 조기 삭제 / orphan cleanup 간섭 | 렌더 HTML 영구 보관, 캡처 완료까지 삭제 금지 |
| MD에 경로만 있고 파일 없음 | 캡처 실패를 무시하고 경로 삽입 | Filesystem proof gate — 파일 존재 확인 전 경로 삽입 금지 |
| 비율 왜곡 | clip 캡처 시 임의 크기 지정 | 측정한 바운딩박스 비율 그대로 보존 |
| PNG가 viewport 크기로 나옴 | element screenshot 대신 viewport/full-page 캡처 사용 | dimension sanity check — PNG 크기가 바운딩박스의 1.5배 초과 시 재캡처 |

---

## Phase 1: 렌더용 HTML 작성

**핵심 원칙: self-contained, 외부 의존성 제로**

> **[필수]** body와 `.diagram`의 CSS 규칙은 정확한 캡처를 위해 **절대 생략하거나 변경하면 안 됨**. 하나라도 빠지거나 덮어쓰면 캡처된 PNG에 viewport 크기의 여백이 포함됨.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  /* [필수] 글로벌 리셋 — 브라우저 기본 margin/padding 제거 */
  * { margin: 0; padding: 0; box-sizing: border-box; }

  /* [필수] body를 콘텐츠 크기에 맞춤 — 여백 원천 차단 */
  body {
    margin: 0;
    padding: 0;
    width: fit-content;    /* REQUIRED — shrink to content */
    height: fit-content;   /* REQUIRED — shrink to content */
    display: inline-block; /* REQUIRED — enables fit-content */
    overflow: hidden;      /* REQUIRED — no scrollbars */
    background: #ffffff;
  }

  /* [필수] 캡처 대상 루트 요소 — element screenshot의 타겟 */
  /* REQUIRED — capture target must shrink-wrap content, never expand to viewport */
  .diagram {
    display: inline-block;
    margin: 0;
    padding: 0;
    /* width/height는 내부 콘텐츠에 의해 자동 결정 */
  }
</style>
</head>
<body>
<div class="diagram">
  <!-- 다이어그램 콘텐츠 -->
</div>
</body>
</html>
```

### CSS 규칙별 이유

| CSS 규칙 | 이유 |
|---|---|
| `* { margin: 0; padding: 0; }` | 브라우저마다 다른 기본 margin (보통 body에 8px) 제거 |
| `body { width: fit-content }` | body가 viewport 전체를 차지하지 않고 콘텐츠만큼만 차지 |
| `body { display: inline-block }` | fit-content와 함께 써야 실제로 shrink-wrap 동작 |
| `body { overflow: hidden }` | 스크롤바 방지 |
| `.diagram { display: inline-block }` | 캡처 대상이 콘텐츠 바운딩박스와 정확히 일치 |
| `.diagram { margin: 0; padding: 0 }` | element screenshot 시 외부 여백이 캡처에 포함되는 것 방지 |

### 금지 사항

- `width: 100%`, `display: block`, 또는 고정 `width`/`height` — body나 `.diagram`에 사용 금지 (viewport 크기로 확장됨)
- `body { padding: 16px }` 같은 여백 — element screenshot에 직접 잡히지 않아도 레이아웃에 영향
- 외부 CDN 링크 (`<link href="https://...">`, `<script src="https://...">`) — 오프라인 환경에서 깨짐

---

## Phase 2: 브라우저 탐색 + 렌더 안정화

```
1. 브라우저 도구로 file://<절대경로>/render.html 탐색
2. 최소 400ms 대기 (렌더링 안정화)
   - 복잡한 다이어그램/애니메이션이 있으면 800ms
   - CSS transition이 있으면 transition 시간 + 100ms
```

### 왜 대기가 필요한가

- 브라우저의 레이아웃 엔진은 DOM 삽입 직후 reflow가 완료되지 않을 수 있음
- 특히 `display: inline-block` + `fit-content` 조합은 콘텐츠 크기 계산이 한 프레임 뒤에 확정되는 경우가 있음
- 대기 없이 즉시 캡처하면 0×0 또는 부분 렌더링된 이미지가 생성됨

---

## Phase 3: 바운딩박스 측정 + viewport 조정

```
3. .diagram 요소의 바운딩박스 측정 (width, height, x, y)
4. 현재 viewport가 바운딩박스를 잘라낼 경우:
   → viewport를 (width + 48px, height + 48px) 이상으로 리사이즈
   → 리사이즈 후 바운딩박스 재측정 (리플로우 반영)
```

### 왜 viewport 조정이 필요한가

- 브라우저 캡처 도구는 viewport 밖의 영역을 렌더링하지 않음
- element screenshot이라도 viewport 밖으로 넘어간 부분은 잘림
- 안전 여유(gutter) 24px × 양쪽 = 48px를 추가해야 edge clipping 방지

### viewport 권장 범위

- 너비: 600–1200px (일반적인 다이어그램)
- Device pixel ratio: 2 (레티나 품질)
- 배경: 흰색 `#ffffff`, 브라우저 크롬/스크롤바 없음

---

## Phase 4: 캡처 (핵심)

```
5. [1순위] element screenshot — .diagram 요소만 캡처 (non-negotiable)
6. [2순위] clip rectangle — 바운딩박스 좌표 (x, y, width, height) 지정 캡처
7. [금지] full-page screenshot — 절대 사용하지 않음
```

### 캡처 방식 우선순위와 이유

| 순위 | 방식 | 장점 | 단점 |
|---|---|---|---|
| 1순위 | element screenshot | 요소 경계에 정확히 맞음, 여백 없음 | 일부 브라우저 도구에서 미지원 |
| 2순위 | clip rectangle | 좌표 기반으로 정밀 제어 가능 | 바운딩박스 측정 정확도에 의존 |
| **금지** | full-page screenshot | — | body/viewport 여백 전부 포함됨, 후처리 크롭 부담 증가 |

### clip rectangle 사용 시 필수 규칙

- 출력 PNG의 width:height 비율이 측정한 바운딩박스 비율과 일치해야 함
- 임의로 정사각형이나 16:9 등으로 변환하지 않음

---

## Phase 5: Dimension Sanity Check (캡처 검증)

```
8. 캡처된 PNG의 실제 크기와 Phase 3에서 측정한 .diagram 바운딩박스 비교
   - PNG width 또는 height가 바운딩박스의 1.5배를 초과하면:
     → 잘못된 요소를 캡처했거나 viewport 캡처로 fallback된 것
     → PNG 삭제 후 Phase 4부터 올바른 .diagram 셀렉터로 재캡처
```

### 왜 이 검증이 필요한가

- AI 에이전트가 element screenshot 지시를 무시하고 viewport 캡처를 사용하는 경우가 실제로 발생함
- 프롬프트만으로는 캡처 방식을 100% 보장할 수 없음 — 결과물의 크기로 사후 검증해야 함
- 스크린샷의 이미지가 보여주는 문제: 다이어그램은 좌상단 ~25%만 차지하고 나머지 ~75%가 빈 여백

---

## Phase 6: 파일 검증 (Filesystem Proof Gate)

```
9. PNG 파일 존재 + 크기 > 0 확인 (ls -l 또는 파일 읽기)
   - 실패 시: 800ms 대기 후 Phase 2부터 재시도
   - 재실패 시: HTML/CSS 문제로 판단, 수정 후 재시도
   - 절대 실패한 채로 진행하지 않음
```

### 왜 filesystem proof가 필수인가

- 브라우저 도구가 "캡처 완료"를 반환해도 실제 디스크에 쓰기가 완료되지 않은 경우가 있음
- 비동기 I/O 환경에서 파일이 0바이트로 남아있을 수 있음
- "경로를 알고 있으니까 있겠지"라는 가정은 **반드시** 실패함

### 금지

- filesystem proof 통과 전에 Markdown에 이미지 경로 삽입
- 파일 미존재를 무시하고 진행
- 부분 출력 (0바이트, 손상된 PNG) 유지

---

## Phase 7: 후처리 자동 크롭

```
10. trim_whitespace.py가 프로젝트에 없으면 먼저 fetch:
    curl -fsSL https://raw.githubusercontent.com/mandarange/MaraudersMapMD-skill/main/trim_whitespace.py -o trim_whitespace.py

11. Pillow가 없으면 설치:
    pip install Pillow

12. 크롭 실행:
    python trim_whitespace.py <png-path> --padding 4
    - "no trim needed" 반환 시 이미 타이트한 상태 → 그대로 진행
```

### 왜 후처리 크롭이 필요한가

- element screenshot이 완벽하더라도 1–2px의 anti-aliasing 여백이 남을 수 있음
- CSS 렌더링 엔진마다 `inline-block`의 경계 계산이 미세하게 다름
- 프롬프트만으로 "여백 없이 캡처해줘"라고 지시하는 것은 **불충분** — 브라우저 도구의 동작은 AI가 제어할 수 없는 영역

### trim_whitespace.py 핵심 로직

```python
# 1. 이미지를 열고 배경색 판별 (채널값 >= threshold → 배경)
# 2. 배경이 아닌 픽셀의 bounding box 계산
# 3. bounding box + padding만큼 crop
# 4. RGBA 이미지의 경우 투명 픽셀도 배경으로 처리
# 5. 이미 타이트하면 (기존 여백 <= padding) None 반환 → 변경 없음
```

### 파라미터

| 파라미터 | 기본값 | 설명 |
|---|---|---|
| `--padding` | 4 | 콘텐츠 주변에 유지할 최소 여백 (px) |
| `--threshold` | 250 | 채널값 >= 이 값이면 배경으로 간주 |
| `--dry-run` | off | 실제 파일 수정 없이 결과만 미리보기 |

---

## Phase 8: 시각 검증

```
13. 캡처된 PNG를 확인:
    - 모든 텍스트 판독 가능
    - 요소 겹침 없음
    - 원본 레이아웃과 일치
    - 가장자리 잘림 없음
    - 과도한 여백 없음
14. 문제 발견 시 → HTML/CSS 수정 후 Phase 2부터 재시도
```

---

## Phase 9: Markdown 삽입

```
15. 삽입할 Markdown 파일 위치 기준으로 PNG 상대경로 계산
16. 원본 ASCII 블록을 정확히 찾아 삭제 (전후 텍스트 건드리지 않음)
17. 두 줄만 삽입:
    <!-- Converted from ASCII art: [설명] -->
    ![다이어그램 설명](./상대/경로/diagram.png)
18. 삽입 후 PNG 경로가 디스크에 존재하는지 재확인
```

### Markdown 삽입 시 흔한 실패

- `![a]![a](path)` — alt text 중복
- `[텍스트](/![a](path))` — 링크 안에 이미지 문법 중첩
- 주변 텍스트/헤딩 손상

---

## 렌더 HTML 라이프사이클 (선택사항)

이미지를 반복 수정해야 하는 워크플로우에서는 렌더 HTML을 영구 보관하면 재편집이 가능:

```
파일명: <diagram-name>.render_v{N}.html
- 최초 생성: render_v1.html
- 수정 시: render_v2.html (N+1)
- SSOT: 최신 버전 1개만 유지, 이전 버전은 캡처 성공 후 삭제
- 캡처 실패 시: 현재 HTML 유지 (삭제하지 않음), PNG만 삭제 후 재시도
```

---

## 한 줄 요약

> **self-contained HTML (여백 제로 CSS) → 브라우저 탐색 + 400ms 대기 → 바운딩박스 측정 + viewport 확장 → element screenshot (full-page 금지) → dimension sanity check (1.5배 초과 시 재캡처) → 디스크 존재 확인 → Pillow 자동 크롭 → 시각 검증 → Markdown 삽입**
