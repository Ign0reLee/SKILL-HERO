---
description: Skill Hero 비주얼라이저를 켭니다 — 로컬 브라우저로 표시 (SSH/원격 포함 어디서나)
disable-model-invocation: true
allowed-tools: Bash(python3 *), Bash(python *), Bash(cmd *), Bash(open *), Bash(xdg-open *)
---
Skill Hero 라이브 서버를 **백그라운드**로 실행하세요 (GUI 아님 → Bash 를 `run_in_background: true` 로 사용해 즉시 반환):
`python3 "${CLAUDE_PLUGIN_ROOT}/skill-hero-serve.py"`  (`python3` 가 없으면 `python`)
서버는 `http://localhost:8777` 에서 HTML + 실시간 상태를 서빙합니다.

그다음 **환경을 판별**하세요 — 환경변수 `SSH_CONNECTION` 또는 `SSH_TTY` 가 있으면 **원격(SSH)** 입니다.

- **원격(SSH)일 때:** 브라우저를 열지 말고 아래만 안내하세요 —
  "⚔ 원격에서 Skill Hero 서버를 켰습니다(포트 8777). VS Code가 자동으로 포워딩합니다(안 되면 하단 **포트** 탭에서 8777 추가). **내 로컬 브라우저에서 http://localhost:8777 을 여세요.** Claude가 일하면 실시간 전투로 보입니다."

- **로컬일 때:** 기본 브라우저를 자동으로 여세요 —
  - Windows: `cmd /c start http://localhost:8777`
  - macOS: `open http://localhost:8777`
  - Linux: `xdg-open http://localhost:8777`
  그리고 "⚔ 브라우저에서 http://localhost:8777 을 열었습니다. 스킬을 용사에게 드래그해 장착하고, Claude가 일하면 실시간 전투로 보입니다." 라고 안내하세요.

끝에 한 줄 덧붙이세요: "투명한 '채팅 위' 데스크톱 오버레이(로컬 전용)를 원하면 **로컬 PC에서** `skill-hero-overlay.pyw` 를 직접 실행하세요."
