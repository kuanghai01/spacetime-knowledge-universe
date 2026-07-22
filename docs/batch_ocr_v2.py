#!/usr/bin/env python3
"""Batch OCR with incremental saves - process 20 pages at a time."""
from rapidocr_onnxruntime import RapidOCR
from pathlib import Path

pages_dir = Path("/Users/haikuang/.qclaw/workspace/spacetime-knowledge-universe/docs/pages_small")
output_file = Path("/Users/haikuang/.qclaw/workspace/spacetime-knowledge-universe/docs/textbook_raw_ocr.txt")

# Determine starting point from existing output
start_page = 1
if output_file.exists():
    content = output_file.read_text(encoding='utf-8')
    # Find last successfully processed page
    for line in content.split('\n'):
        if line.startswith('=== 第') and '页 ===' in line and 'OCR失败' not in line:
            try:
                num = int(line.replace('=== 第', '').replace('页 ===', ''))
                start_page = num + 1
            except:
                pass

print(f"Starting from page {start_page}")
ocr = RapidOCR()

page_files = sorted(pages_dir.glob("page_*.png"))
remaining = [f for f in page_files if int(f.stem.split('_')[1]) >= start_page]
print(f"{len(remaining)} pages remaining")

batch_size = 20
for batch_idx in range(0, len(remaining), batch_size):
    batch = remaining[batch_idx:batch_idx + batch_size]
    all_text = []
    
    for page_file in batch:
        page_num = int(page_file.stem.split('_')[1])
        print(f"  Page {page_num}...", end=' ', flush=True)
        try:
            result, elapse = ocr(str(page_file))
            page_lines = []
            if result:
                for item in result:
                    page_lines.append(item[1])
            all_text.append(f"=== 第{page_num}页 ===\n")
            all_text.append("\n".join(page_lines))
            all_text.append("\n")
            print(f"OK ({len(page_lines)} lines)")
        except Exception as e:
            all_text.append(f"=== 第{page_num}页 [OCR失败: {e}] ===\n\n")
            print(f"FAIL: {e}")
    
    # Append batch to file
    mode = 'a' if output_file.exists() and start_page > 1 else 'w'
    with open(output_file, mode, encoding='utf-8') as f:
        f.write("\n".join(all_text))
    
    last_page = int(batch[-1].stem.split('_')[1])
    print(f"Batch saved: pages {int(batch[0].stem.split('_')[1])}-{last_page}")

print(f"\nAll done! Output: {output_file}")
