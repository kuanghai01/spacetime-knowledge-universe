#!/usr/bin/env python3
"""Extract knowledge points from cleaned lesson content."""
import re, json, math
from pathlib import Path

# Load cleaned lessons
with open('docs/lessons_clean.json', 'r', encoding='utf-8') as f:
    lessons = json.load(f)

# Unit mapping
UNIT_MAP = {
    '1': ('第一单元', '文明的产生和古代亚非文明'),
    '2': ('第一单元', '文明的产生和古代亚非文明'),
    '3': ('第一单元', '文明的产生和古代亚非文明'),
    '4': ('第一单元', '文明的产生和古代亚非文明'),
    '5': ('第二单元', '古代欧洲文明'),
    '6': ('第二单元', '古代欧洲文明'),
    '7': ('第三单元', '封建时代的欧洲'),
    '8': ('第三单元', '封建时代的欧洲'),
    '9': ('第三单元', '封建时代的欧洲'),
    '10': ('第四单元', '中古时期的亚洲、非洲和美洲'),
    '11': ('第四单元', '中古时期的亚洲、非洲和美洲'),
    '12': ('第四单元', '中古时期的亚洲、非洲和美洲'),
    '13': ('第五单元', '走向近代'),
    '14': ('第五单元', '走向近代'),
    '15': ('第五单元', '走向近代'),
    '16': ('第六单元', '资本主义制度的初步确立'),
    '17': ('第六单元', '资本主义制度的初步确立'),
    '18': ('第六单元', '资本主义制度的初步确立'),
    '19': ('第七单元', '第一次工业革命和马克思主义的诞生'),
    '20': ('第七单元', '第一次工业革命和马克思主义的诞生'),
    '21': ('第七单元', '第一次工业革命和马克思主义的诞生'),
    '22': ('第七单元', '第一次工业革命和马克思主义的诞生'),
}

# Clean content: remove page markers and metadata sections
def clean_content(text):
    # Remove page markers
    text = re.sub(r'\[第\d+页\]\n?', '', text)
    # Remove lesson title
    text = re.sub(r'第\s*\d+\s*课.*?\n', '', text)
    # Remove unit title
    text = re.sub(r'第[一二三四五六七八九十]+单元.*?\n', '', text)
    # Remove metadata sections
    text = re.sub(r'课后活动.*', '', text, flags=re.DOTALL)
    text = re.sub(r'知识拓展.*', '', text, flags=re.DOTALL)
    text = re.sub(r'材料研读.*', '', text, flags=re.DOTALL)
    text = re.sub(r'相关史事.*?(?=\n\n|\n第)', '', text, flags=re.DOTALL)
    text = re.sub(r'想一想.*', '', text, flags=re.DOTALL)
    text = re.sub(r'读一读.*', '', text, flags=re.DOTALL)
    # Remove image captions
    text = re.sub(r'第\d+—.*?\n', '', text)
    text = re.sub(r'第\s*\d+.*?图.*?\n', '', text)
    text = re.sub(r'.*?照片.*?\n', '', text)
    text = re.sub(r'圣马丁堂.*?\n', '', text)
    text = re.sub(r'巴黎公社社员墙.*?\n', '', text)
    text = re.sub(r'《.*?》.*?油画.*?\n', '', text)
    # Remove standalone numbers (page numbers)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+第.*$', '', text, flags=re.MULTILINE)
    # Clean whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# Split content into paragraphs
def split_paragraphs(text):
    paragraphs = re.split(r'\n\n+', text)
    result = []
    for p in paragraphs:
        p = p.strip()
        if len(p) > 10:  # Skip very short fragments
            result.append(p)
    return result

# Extract knowledge points from a lesson
def extract_knowledge_points(lesson_num, content):
    unit_name, unit_title = UNIT_MAP.get(lesson_num, ('未知', '未知'))
    
    # Get lesson title
    title_match = re.search(r'第\s*' + lesson_num + r'\s*课\s*(.+?)(?:\n|$)', content)
    lesson_title = title_match.group(1).strip() if title_match else f"第{lesson_num}课"
    lesson_title = re.sub(r'\d+$', '', lesson_title).strip()
    
    # Clean content
    cleaned = clean_content(content)
    paragraphs = split_paragraphs(cleaned)
    
    # Group paragraphs into knowledge points
    kp_groups = []
    current_group = []
    
    for para in paragraphs:
        # Check if this paragraph starts a new topic
        if re.match(r'^[一二三四五六七八九十]+、', para) or \
           re.match(r'^\d+[、.]', para) or \
           re.match(r'^[（(]\d+[)）]', para) or \
           (len(para) < 30 and not re.search(r'[，。；]', para)):
            if current_group:
                kp_groups.append(current_group)
            current_group = [para]
        else:
            current_group.append(para)
    
    if current_group:
        kp_groups.append(current_group)
    
    # If no clear grouping, split by length
    if len(kp_groups) <= 1 and len(cleaned) > 200:
        # Split into chunks of ~150 chars
        chunks = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) > 200 and current:
                chunks.append(current)
                current = para
            else:
                current += "\n" + para if current else para
        if current:
            chunks.append(current)
        kp_groups = [[c] for c in chunks]
    
    # Create knowledge point objects
    kps = []
    for i, group in enumerate(kp_groups):
        group_text = "\n".join(group)
        
        # Generate title from first line
        first_line = group[0].split('\n')[0].strip()
        if len(first_line) > 25:
            first_line = first_line[:25] + "..."
        
        kp_id = f"B9A_{lesson_num}_{i+1:03d}"
        
        # Determine difficulty based on content length and complexity
        difficulty = 1
        if len(group_text) > 150:
            difficulty = 2
        if len(group_text) > 300:
            difficulty = 3
        
        # Generate tags
        tags = []
        if '公元前' in group_text or '公元' in group_text:
            tags.append('时间')
        if re.search(r'[\u4e00-\u9fff]{2,4}(?:王|帝|皇|汗|苏丹)', group_text):
            tags.append('人物')
        if re.search(r'战争|战役|革命|起义|征服', group_text):
            tags.append('战争')
        if re.search(r'法|律|宪|章|制度', group_text):
            tags.append('制度')
        if re.search(r'文化|艺术|建筑|文学|哲学|宗教', group_text):
            tags.append('文化')
        if re.search(r'经济|贸易|商业|工业|农业', group_text):
            tags.append('经济')
        if not tags:
            tags.append('概述')
        
        kps.append({
            'id': kp_id,
            'title': first_line,
            'content': group_text,
            'chapter': f"第{lesson_num}课 {lesson_title}",
            'unit': unit_name,
            'difficulty': difficulty,
            'tags': tags,
            'source_page': f"九年级上册第{lesson_num}课"
        })
    
    return kps

# Process all lessons
all_kps = []
for lesson_num in sorted(lessons.keys(), key=int):
    kps = extract_knowledge_points(lesson_num, lessons[lesson_num])
    all_kps.extend(kps)
    unit_name, _ = UNIT_MAP.get(lesson_num, ('未知', '未知'))
    print(f"第{lesson_num}课: {len(kps)} knowledge points")

print(f"\nTotal: {len(all_kps)} knowledge points")

# Save as JSON for review
with open('docs/knowledge_points_raw.json', 'w', encoding='utf-8') as f:
    json.dump(all_kps, f, ensure_ascii=False, indent=2)

print("Saved to docs/knowledge_points_raw.json")
