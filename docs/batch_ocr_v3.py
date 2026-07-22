#!/usr/bin/env python3
"""Batch OCR with correct incremental saves."""
from rapidocr_onnxruntime import RapidOCR
from pathlib import Path

pages_dir = Path("/Users/haikuang/.qclaw/workspace/spacetime-knowledge-universe/docs/pages_small")
output_file = Path("/Users/haikuang/.qclaw/workspace/spacetime-knowledge-universe/docs/textbook_raw_ocr.txt")

# Determine starting point
start_page = 1
if output_file.exists():
    content = output_file.read_text(encoding='utf-8')
    for line in content.split('\n'):
        if line.startswith('=== 第') and '页 ===' in line and 'OCR失败' not in line:
            try:
                num = int(line.replace('=== 第', '').replace('页 ===', ''))
                start_page = max(start_page, num + 1)
            except:
                pass

print(f"Starting from page {start_page}")
ocr = RapidOCR()

page_files = sorted(pages_dir.glob("page_*.png"))
remaining = [f for f in page_files if int(f.stem.split('_')[1]) >= start_page]
print(f"{len(remaining)} pages remaining")

for page_file in remaining:
    page_num = int(page_file.stem.split('_')[1])
    print(f"  Page {page_num}...", end=' ', flush=True)
    try:
        result, elapse = ocr(str(page_file))
        page_lines = []
        if result:
            for item in result:
                page_lines.append(item[1])
        text = f"=== 第{page_num}页 ===\n" + "\n".join(page_lines) + "\n\n"
        print(f"OK ({len(page_lines)} lines)")
    except Exception as e:
        text = f"=== 第{page_num}页 [OCR失败: {e}] ===\n\n"
        print(f"FAIL: {e}")
    
    # Always append
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(text)

print(f"\nAll done! Output: {output_file}")
