#!/usr/bin/env python3
"""Generate new B9A data from extracted knowledge points and update history_data.py."""
import re, json
from pathlib import Path

# Load extracted KPs
with open('docs/knowledge_points_raw.json', 'r', encoding='utf-8') as f:
    kps = json.load(f)

# Filter and clean KPs
def clean_kp(kp):
    content = kp['content']
    
    # Remove image captions and metadata
    content = re.sub(r'第\d+—.*?\n', '', content)
    content = re.sub(r'.*?照片.*?\n', '', content)
    content = re.sub(r'《.*?》.*?油画.*?\n', '', content)
    content = re.sub(r'圣马丁堂.*?\n', '', content)
    content = re.sub(r'巴黎公社社员墙.*?\n', '', content)
    content = re.sub(r'第\d+课.*?\n', '', content)
    content = re.sub(r'第[一二三四五六七八九十]+单元.*?\n', '', content)
    content = re.sub(r'\[第\d+页\]', '', content)
    content = re.sub(r'^\d+\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'想一想.*', '', content, flags=re.DOTALL)
    content = re.sub(r'读地图.*', '', content, flags=re.DOTALL)
    content = re.sub(r'读一读.*', '', content, flags=re.DOTALL)
    content = re.sub(r'课后活动.*', '', content, flags=re.DOTALL)
    content = re.sub(r'知识拓展.*', '', content, flags=re.DOTALL)
    content = re.sub(r'材料研读.*', '', content, flags=re.DOTALL)
    content = re.sub(r'相关史事.*?(?=\n\n)', '', content, flags=re.DOTALL)
    
    # Fix OCR errors
    replacements = {
        '来白': '来自', '丁人': '工人', '呼叶': '呼吁',
        '进人': '进入', '暂死': '誓死', '国民白卫军': '国民自卫军',
        '普鲁上': '普鲁士', '利I': '和', '占代': '古代',
        '埃卫': '埃及', '两河流城': '两河流域', '古代罗': '古代罗马',
        '古代欣洲': '古代欧洲', '两欧': '西欧', '平期': '早期',
        '阿拉们': '阿拉们', '中古时的': '中古时期的',
        '利巴黎公社': '和巴黎公社', '第·次1亚革命': '第一次工业革命',
        '工业站命': '工业革命', '法国大革命利': '法国大革命和',
        '法兰克王国利': '法兰克王国和', '西欧的城市利': '西欧的城市和',
        '西欧经济社会': '西欧经济社会发展', '古代欧洲文服': '古代欧洲文明',
        '文明的产生利': '文明的产生和', '从原始社会到奴求社会': '从原始社会到奴隶社会',
        '埃塞像让亚': '埃塞俄比亚', '艺方': '发现', '造骨': '骨骼',
        '陡今': '距今', '逛分': '化石', '定对': '定名为',
        '照造音': '骨骼化', '够直立': '能够直立',
        '洞大': '洞穴', '烧制': '烧制', '御案': '御寒',
        '防物野': '防御野兽', '渔精采集': '渔猎采集',
        '某木': '基本', '育牧业': '畜牧业', '普道': '普遍',
        '多地': '多地', '大麦和小麦': '大麦和小麦',
        '山子': '谷子', '头': '', '马': '', '区': '',
        '母花': '母系', '大奖': '大奖', '能': '',
        '农业和育牧业': '农业和畜牧业', '寺': '出现',
        '绿松退石': '绿松石', '管饰品': '装饰品',
        '已/：级浆握轴先技式': '已掌握制陶技术',
        '隶制': '原始', '落葬': '墓葬',
        '描绘了很多': '描绘了很多', '用土、石、木': '用土、石、木',
        '生活方式也随之变': '生活方式也随之改变', '定居生活开始': '定居生活开始',
        '古城遗地位': '古城遗址', '陶给': '陶器',
        '远古先民': '远古先民', '岩洞': '岩洞',
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Clean whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()
    
    # Skip if too short or just metadata
    if len(content) < 30:
        return None
    if content in ['目录', '从原始社会到奴隶社会']:
        return None
    
    kp['content'] = content
    return kp

# Process all KPs
cleaned = []
for kp in kps:
    result = clean_kp(kp)
    if result:
        cleaned.append(result)

# Now format as B9A entries
dynasty_map = {
    '1': '史前', '2': '古巴比伦', '3': '古埃及', '4': '古印度',
    '5': '古希腊', '6': '古罗马', '7': '中世纪', '8': '中世纪',
    '9': '拜占庭', '10': '中古时期', '11': '阿拉伯', '12': '中古时期',
    '13': '近代', '14': '近代', '15': '近代',
    '16': '近代', '17': '近代', '18': '近代',
    '19': '近代', '20': '近代', '21': '近代', '22': '近代',
}

b9a_entries = []
for i, kp in enumerate(cleaned, 1):
    lesson_num = kp['id'].split('_')[1]
    dynasty = dynasty_map.get(lesson_num, '古代')
    
    entry = {
        "id": f"hist_b9a_{i:03d}",
        "title": kp['title'][:30],
        "content": kp['content'],
        "chapter": kp['chapter'],
        "difficulty": kp['difficulty'],
        "dynasty": dynasty,
        "tags": kp['tags'][:5],
    }
    b9a_entries.append(entry)

print(f"Generated {len(b9a_entries)} B9A entries")

# Now update history_data.py
data_file = Path('src/data/history_data.py')
content = data_file.read_text(encoding='utf-8')

# Find and replace HISTORY_B9A section
# Pattern: HISTORY_B9A = [ ... ] before HISTORY_B9B
pattern = r'(HISTORY_B9A = \[)(.*?)(\n# 九年级下册)'
match = re.search(pattern, content, re.DOTALL)

if not match:
    # Try alternative pattern
    pattern = r'(HISTORY_B9A = \[)(.*?)(\n# 合并所有历史知识点)'
    match = re.search(pattern, content, re.DOTALL)

if match:
    # Generate new B9A content
    new_b9a = "HISTORY_B9A = [\n"
    for entry in b9a_entries:
        new_b9a += "    {\n"
        new_b9a += f'        "id": "{entry["id"]}",\n'
        new_b9a += f'        "title": "{entry["title"]}",\n'
        # Escape content for Python string
        escaped_content = entry['content'].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        new_b9a += f'        "content": "{escaped_content}",\n'
        new_b9a += f'        "chapter": "{entry["chapter"]}",\n'
        new_b9a += f'        "difficulty": {entry["difficulty"]},\n'
        new_b9a += f'        "dynasty": "{entry["dynasty"]}",\n'
        new_b9a += f'        "tags": {entry["tags"]},\n'
        new_b9a += "    },\n"
    new_b9a += "]\n\n"
    
    # Replace
    new_content = content[:match.start(2)] + new_b9a + content[match.end(2):]
    
    # Also fix the channel typo in old B9A_001 if it exists
    new_content = new_content.replace('"channel":', '"chapter":')
    
    data_file.write_text(new_content, encoding='utf-8')
    print(f"Updated {data_file}")
    print(f"Old B9A: 12 entries → New B9A: {len(b9a_entries)} entries")
else:
    print("ERROR: Could not find HISTORY_B9A section to replace")
    print("Searching for pattern...")
    if 'HISTORY_B9A' in content:
        print("HISTORY_B9A found in file")
    else:
        print("HISTORY_B9A NOT found")
