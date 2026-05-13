#!/usr/bin/env bash
# Сборка единого PDF из артефактов product-workflow.
#
# Использование:
#   bash build_pdf.sh <repo-root> <output-pdf>
#
# Аргументы:
#   repo-root    — корень репозитория (содержит docs/product/ и docs/plans/).
#   output-pdf   — путь до итогового PDF (например, ~/Downloads/myproduct-product-docs.pdf).
#
# Переменные окружения (опциональны):
#   DOCS_PRODUCT  — путь до docs/product/ (default: <repo-root>/docs/product).
#   DOCS_PLANS    — путь до docs/plans/   (default: <repo-root>/docs/plans).
#   PDF_TITLE     — заголовок на обложке (default: "<product> — Продуктовая документация").
#   WORK_DIR      — временная директория (default: /tmp/product-workflow-pdf).
#   CHROME_BIN    — путь до Google Chrome (default: macOS-стандартный).
#
# Зависимости:
#   - pandoc (рекомендуется) ИЛИ python3 + pip-пакет markdown
#   - Google Chrome (headless печать в PDF)

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: bash build_pdf.sh <repo-root> <output-pdf>" >&2
  exit 1
fi

REPO_ROOT="$1"
OUTPUT_PDF="$2"
DOCS_PRODUCT="${DOCS_PRODUCT:-$REPO_ROOT/docs/product}"
DOCS_PLANS="${DOCS_PLANS:-$REPO_ROOT/docs/plans}"
PDF_TITLE="${PDF_TITLE:-Продуктовая документация}"
WORK_DIR="${WORK_DIR:-/tmp/product-workflow-pdf}"

# Найти Chrome
if [[ -z "${CHROME_BIN:-}" ]]; then
  if [[ "$(uname)" == "Darwin" ]]; then
    CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  elif command -v google-chrome &>/dev/null; then
    CHROME_BIN="$(command -v google-chrome)"
  elif command -v chromium &>/dev/null; then
    CHROME_BIN="$(command -v chromium)"
  fi
fi

if [[ ! -x "$CHROME_BIN" ]]; then
  echo "ERROR: Chrome не найден. Установите Google Chrome или задайте CHROME_BIN." >&2
  exit 2
fi

# Проверить existence корня
[[ -d "$DOCS_PRODUCT" ]] || { echo "ERROR: $DOCS_PRODUCT не существует" >&2; exit 3; }

mkdir -p "$WORK_DIR"
COMBINED_MD="$WORK_DIR/combined.md"
HTML_PATH="$WORK_DIR/combined.html"

echo "[1/4] Объединение markdown в $COMBINED_MD"
{
  cat <<EOF
---
title: "$PDF_TITLE"
date: $(date +%Y-%m-%d)
lang: ru
documentclass: article
geometry: margin=1.6cm
toc: true
toc-depth: 2
numbersections: true
---

EOF

  # 1. overview
  if [[ -f "$DOCS_PRODUCT/overview.md" ]]; then
    cat "$DOCS_PRODUCT/overview.md"
    echo
    echo
  fi

  # 2. сценарии в порядке имени файла
  if [[ -d "$DOCS_PRODUCT/scenarios" ]]; then
    for f in "$DOCS_PRODUCT/scenarios"/*.md; do
      [[ -f "$f" ]] || continue
      cat "$f"
      echo
      echo
    done
  fi

  # 3. план реализации (любой *-implementation-plan.md в DOCS_PLANS)
  if [[ -d "$DOCS_PLANS" ]]; then
    for f in "$DOCS_PLANS"/*implementation-plan*.md; do
      [[ -f "$f" ]] || continue
      cat "$f"
      echo
      echo
    done

    # 4. план усиления
    for f in "$DOCS_PLANS"/*hardening-plan*.md; do
      [[ -f "$f" ]] || continue
      cat "$f"
      echo
      echo
    done
  fi
} > "$COMBINED_MD"

echo "[2/4] Markdown → HTML"
if command -v pandoc &>/dev/null; then
  # Pandoc-путь (предпочтительный — корректные таблицы, footnotes, TOC)
  CSS_FILE="$WORK_DIR/style.css"
  cat > "$CSS_FILE" <<'CSS'
@page { size: A4; margin: 18mm 14mm 18mm 14mm; }
* { box-sizing: border-box; }
html { font-size: 10.5pt; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; color: #1a1a1a; line-height: 1.5; max-width: 100%; margin: 0; padding: 0; }
header#title-block-header { text-align: center; padding: 60mm 0 30mm; page-break-after: always; }
header#title-block-header .title { font-size: 28pt; margin: 0 0 8mm; color: #0b1f3a; }
header#title-block-header .date { font-size: 11pt; color: #666; }
nav#TOC { page-break-after: always; padding: 6mm 0; }
nav#TOC h1, nav#TOC h2 { font-size: 18pt; color: #0b1f3a; border-bottom: 1px solid #ccc; padding-bottom: 4mm; }
nav#TOC ul { list-style: none; padding-left: 0; }
nav#TOC ul ul { padding-left: 6mm; font-size: 0.95em; color: #444; }
nav#TOC li { margin: 1.5mm 0; }
nav#TOC a { color: #1a4480; text-decoration: none; }
h1 { font-size: 22pt; color: #0b1f3a; border-bottom: 2px solid #0b1f3a; padding-bottom: 2mm; margin-top: 8mm; page-break-before: always; }
h1:first-of-type { page-break-before: auto; }
h2 { font-size: 15pt; color: #0b1f3a; margin-top: 6mm; padding-top: 1mm; border-bottom: 1px solid #d0d0d0; padding-bottom: 1mm; }
h3 { font-size: 12pt; color: #1a4480; margin-top: 4mm; }
h4 { font-size: 11pt; color: #1a4480; margin-top: 3mm; }
p { margin: 2.5mm 0; orphans: 3; widows: 3; }
ul, ol { margin: 2mm 0 2mm 6mm; padding-left: 2mm; }
li { margin: 1mm 0; }
strong { color: #0b1f3a; }
code { background: #f4f4f4; padding: 0.5mm 1mm; border-radius: 2px; font-family: 'SF Mono', Menlo, monospace; font-size: 0.92em; word-wrap: break-word; word-break: break-word; }
pre { background: #f6f6f6; padding: 3mm; border-radius: 3px; border: 1px solid #e0e0e0; font-size: 0.85em; overflow: auto; line-height: 1.4; page-break-inside: avoid; word-wrap: break-word; word-break: break-word; white-space: pre-wrap; }
pre code { background: transparent; padding: 0; word-break: break-all; }
a { color: #1a4480; text-decoration: none; word-break: break-word; overflow-wrap: break-word; }
table { border-collapse: collapse; margin: 3mm 0; width: 100%; font-size: 0.92em; page-break-inside: avoid; }
table th { background: #e9eef5; color: #0b1f3a; font-weight: 600; text-align: left; padding: 1.5mm 2mm; border: 1px solid #c8d2dc; }
table td { padding: 1.5mm 2mm; border: 1px solid #d8d8d8; vertical-align: top; word-wrap: break-word; word-break: break-word; }
blockquote { border-left: 3px solid #1a4480; margin: 2mm 0; padding: 1mm 4mm; color: #444; background: #f7f9fc; }
hr { border: none; border-top: 1px solid #d0d0d0; margin: 5mm 0; }
CSS
  pandoc "$COMBINED_MD" \
    -f markdown+yaml_metadata_block+pipe_tables+fenced_code_blocks \
    -t html5 \
    --standalone \
    --toc \
    --toc-depth=2 \
    --css="$CSS_FILE" \
    --embed-resources \
    -o "$HTML_PATH"
elif python3 -c "import markdown" 2>/dev/null; then
  echo "  (pandoc не найден, использую python-markdown)"
  python3 - <<PY
import markdown, pathlib
src = pathlib.Path("$COMBINED_MD").read_text(encoding="utf-8")
# strip yaml frontmatter
if src.startswith("---"):
    end = src.find("---", 3)
    if end != -1:
        src = src[end+3:].lstrip()
md = markdown.Markdown(extensions=["fenced_code","tables","toc","sane_lists","codehilite"], extension_configs={"toc":{"toc_depth":"1-2"},"codehilite":{"guess_lang":False,"noclasses":True}})
body = md.convert(src)
toc = md.toc
css = """
@page { size: A4; margin: 18mm 14mm 18mm 14mm; }
html { font-size: 10.5pt; }
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; color: #1a1a1a; line-height: 1.5; }
.cover { text-align: center; padding: 60mm 0 30mm; page-break-after: always; }
.cover h1 { font-size: 28pt; color: #0b1f3a; }
nav.toc { page-break-after: always; padding: 6mm 0; }
nav.toc h2 { font-size: 18pt; color: #0b1f3a; border-bottom: 1px solid #ccc; padding-bottom: 4mm; }
h1 { font-size: 22pt; color: #0b1f3a; border-bottom: 2px solid #0b1f3a; padding-bottom: 2mm; page-break-before: always; }
h1:first-of-type { page-break-before: auto; }
h2 { font-size: 15pt; color: #0b1f3a; border-bottom: 1px solid #d0d0d0; padding-bottom: 1mm; margin-top: 6mm; }
h3 { font-size: 12pt; color: #1a4480; }
table { border-collapse: collapse; width: 100%; font-size: 0.92em; page-break-inside: avoid; margin: 3mm 0; }
table th { background: #e9eef5; padding: 1.5mm 2mm; border: 1px solid #c8d2dc; }
table td { padding: 1.5mm 2mm; border: 1px solid #d8d8d8; vertical-align: top; }
code { background: #f4f4f4; padding: 0.5mm 1mm; border-radius: 2px; }
pre { background: #f6f6f6; padding: 3mm; border-radius: 3px; border: 1px solid #e0e0e0; font-size: 0.85em; overflow: auto; white-space: pre-wrap; word-break: break-word; }
a { color: #1a4480; text-decoration: none; word-break: break-word; }
"""
out = f"<!doctype html><html lang='ru'><head><meta charset='utf-8'><title>$PDF_TITLE</title><style>{css}</style></head><body><section class='cover'><h1>$PDF_TITLE</h1></section><nav class='toc'><h2>Содержание</h2>{toc}</nav>{body}</body></html>"
pathlib.Path("$HTML_PATH").write_text(out, encoding="utf-8")
print("HTML built")
PY
else
  echo "ERROR: ни pandoc, ни python-markdown не установлены." >&2
  echo "  Установка pandoc:    brew install pandoc" >&2
  echo "  Установка markdown:  pip3 install --user --break-system-packages markdown" >&2
  exit 4
fi

echo "[3/4] HTML → PDF (Chrome headless)"
"$CHROME_BIN" --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$OUTPUT_PDF" --print-to-pdf-no-header \
  "file://$HTML_PATH" 2>&1 | tail -2

echo "[4/4] Готово"
ls -la "$OUTPUT_PDF"

# Открыть в просмотрщике (macOS)
if [[ "$(uname)" == "Darwin" ]]; then
  open "$OUTPUT_PDF" 2>/dev/null || true
fi
