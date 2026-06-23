---
description: Skill Hero 도트 오버레이를 켭니다 — Claude 작업을 실시간 도트 RPG 전투로 시각화
disable-model-invocation: true
allowed-tools: Bash(pythonw *), Bash(python3 *), Bash(python *)
---
Skill Hero 데스크톱 오버레이(투명 always-on-top 창)를 **백그라운드로 실행**하세요.
GUI 프로그램이므로 절대 블로킹하면 안 됩니다 — Bash 도구를 `run_in_background: true` 로 사용해 즉시 반환하세요.

실행 대상(이미 절대경로로 치환됨):
`${CLAUDE_PLUGIN_ROOT}/skill-hero-overlay.pyw`

플랫폼별 실행:
- Windows: `pythonw "${CLAUDE_PLUGIN_ROOT}/skill-hero-overlay.pyw"`  (콘솔 창 없이)
- macOS/Linux: `python3 "${CLAUDE_PLUGIN_ROOT}/skill-hero-overlay.pyw"`

`pythonw`/`python3` 가 없으면 `python` 으로 대체하세요. 실행 후에는 아래 안내만 한 줄로 출력하세요:

"⚔ Skill Hero 오버레이를 켰습니다 — 좌상단=장비 창(스킬을 용사에게 드래그), 전장 창은 상단바로 이동. 실제 Claude 작업과 연동하려면 전장 창에서 **SPACE**(LIVE 전환), 끄려면 **ESC**."
