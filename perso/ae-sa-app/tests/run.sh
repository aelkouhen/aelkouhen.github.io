#!/bin/bash
# Runs the two headless suites against ../index.html. Requires Google Chrome.
set -e
cd "$(dirname "$0")"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
[ -x "$CHROME" ] || { echo "Chrome not found. Set CHROME=/path/to/chrome"; exit 1; }
APP=../index.html
TMP=$(mktemp -d)
fail=0
for suite in render clicks; do
  python3 - "$APP" "$suite.js" "$TMP/$suite.html" <<'PY'
import sys
app, js, out = sys.argv[1], sys.argv[2], sys.argv[3]
html = open(app).read()
open(out, 'w').write(html.replace("</body>", "<script>\n" + open(js).read() + "\n</script></body>"))
PY
  echo "=== $suite ==="
  out=$("$CHROME" --headless --disable-gpu --no-sandbox --dump-dom --virtual-time-budget=4000 "$TMP/$suite.html" 2>/dev/null \
    | python3 -c "
import sys,re
ms=re.findall(r'<pre id=\"RESULT\">(.*?)</pre>', sys.stdin.read(), re.S)
print(ms[-1] if ms else 'NO RESULT BLOCK')")
  echo "$out"
  echo "$out" | grep -q FAIL && fail=1
done
rm -rf "$TMP"
[ $fail -eq 0 ] && echo && echo "all green" || { echo; echo "FAILURES"; exit 1; }
