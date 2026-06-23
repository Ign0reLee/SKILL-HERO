#!/usr/bin/env python3
# Skill Hero — Claude Code 연동 훅.
# Claude Code 가 보내는 hook 이벤트(stdin JSON)를 받아 skill-hero-state.json 을 갱신한다.
# 비주얼라이저(skill-hero.html)가 이 파일을 1초마다 폴링해 실시간 반영한다.
import sys, json, os

# 상태 파일은 플러그인 설치 위치와 무관하게 공용 경로 사용(훅·오버레이가 공유).
# 환경변수 SKILL_HERO_STATE 로 덮어쓸 수 있음.
STATE = os.environ.get("SKILL_HERO_STATE") or os.path.join(os.path.expanduser("~"), ".claude", "skill-hero-state.json")
DEFAULT = {"phase": "idle", "label": "대기 중...", "agents": [{"name": "main"}], "skills": [], "hp": 100}

def load():
    try:
        with open(STATE, encoding="utf-8") as f:
            s = json.load(f)
        for k, v in DEFAULT.items():
            s.setdefault(k, v)
        return s
    except Exception:
        return dict(DEFAULT)

def save(s):
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False)
    except Exception:
        pass

def main():
    try:
        ev = json.load(sys.stdin)
    except Exception:
        ev = {}
    name = ev.get("hook_event_name", "")
    tool = ev.get("tool_name", "")
    s = load()

    if name == "UserPromptSubmit":
        s.update(phase="thinking", label="요청 분석 중 (Thinking)", hp=100, agents=[{"name": "main"}])
    elif name == "PreToolUse":
        if tool == "Task":  # 서브에이전트 소환 = 용사 추가
            sub = (ev.get("tool_input") or {}).get("subagent_type") or "agent"
            if len(s["agents"]) < 4:
                s["agents"].append({"name": str(sub)[:6]})
        s.update(phase="tool", label="도구 실행: " + (tool or "tool"))
    elif name == "PostToolUse":
        s["hp"] = max(5, int(s.get("hp", 100)) - 8)  # 진행될수록 적 HP 감소
        s.update(phase="baking", label="작업 적용 중 (Baking)")
    elif name == "Stop":
        s.update(phase="done", label="결함 처치 완료!", hp=0, agents=[{"name": "main"}])

    save(s)

if __name__ == "__main__":
    main()
