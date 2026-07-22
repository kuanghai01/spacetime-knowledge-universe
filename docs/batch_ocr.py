#!/usr/bin/env python3
"""Batch OCR small pages using RapidOCR."""
from rapidocr_onnxruntime import RapidOCR
from pathlib import Path

pages_dir = Path("/Users/haikuang/.qclaw/workspace/spacetime-knowledge-universe/docs/pages_small")
output_file = Path("/Users/haikuang/.qclaw/workspace/spacetime-knowledge-universe/docs/textbook_raw_ocr.txt")

print("Initializing RapidOCR...")
ocr = RapidOCR()

page_files = sorted(pages_dir.glob("page_*.png"))
print(f"Found {len(page_files)} pages to process")

all_text = []
for i, page_file in enumerate(page_files, 1):
    page_num = int(page_file.stem.split('_')[1])
    print(f"Page {page_num} ({i}/{len(page_files)})...")
    
    try:
        result, elapse = ocr(str(page_file))
        page_lines = []
        if result:
            for item in result:
                page_lines.append(item[1])
        
        all_text.append(f"=== 第{page_num}页 ===\n")
        all_text.append("\n".join(page_lines))
        all_text.append("\n")
    except Exception as e:
        all_text.append(f"=== 第{page_num}页 [OCR失败: {e}] ===\n\n")

output_file.write_text("\n".join(all_text), encoding='utf-8')
print(f"\nDone! Output written to {output_file}")
print(f"Total pages: {len(page_files)}")
