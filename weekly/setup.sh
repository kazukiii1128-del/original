#!/bin/bash
# Kazuki Weekly Report — 초기 설정 스크립트
# 새 컴퓨터에서 한 번만 실행하면 됩니다.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.wongi.kazuki-weekly"
PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME.plist"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

echo "=== Kazuki Weekly Report 설정 ==="
echo "폴더: $SCRIPT_DIR"

# 1. Python3 확인
PYTHON=$(which python3)
if [ -z "$PYTHON" ]; then
  echo "[ERROR] python3를 찾을 수 없습니다. Python 3.9 이상을 설치하세요."
  exit 1
fi
echo "Python: $PYTHON ($($PYTHON --version))"

# 2. venv 생성
if [ ! -d "$SCRIPT_DIR/venv" ]; then
  echo "가상환경 생성 중..."
  $PYTHON -m venv "$SCRIPT_DIR/venv"
fi

# 3. 패키지 설치
echo "패키지 설치 중..."
"$SCRIPT_DIR/venv/bin/pip" install -q --upgrade pip
"$SCRIPT_DIR/venv/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
echo "설치 완료: $("$SCRIPT_DIR/venv/bin/pip" list | grep -E 'anthropic|requests')"

# 4. plist 경로 업데이트 및 설치
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"

sed \
  -e "s|__PYTHON__|$VENV_PYTHON|g" \
  -e "s|__SCRIPT_DIR__|$SCRIPT_DIR|g" \
  -e "s|__HOME__|$HOME|g" \
  "$PLIST_SRC.template" > "$PLIST_DST"

echo "plist 설치: $PLIST_DST"

# 5. launchd 등록
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
echo "launchd 등록 완료"

echo ""
echo "=== 설정 완료 ==="
echo "매주 월요일 09:00에 자동 실행됩니다."
echo "수동 실행: $VENV_PYTHON $SCRIPT_DIR/generate_weekly.py"
