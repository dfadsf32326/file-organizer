import os
import sys
import json
import shutil
from datetime import datetime

CATEGORY_MAP = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.heic'],
    'Documents': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.md', '.csv', '.pages', '.numbers', '.key'],
    'Media': ['.mp4', '.mkv', '.avi', '.mov', '.mp3', '.wav', '.flac', '.aac', '.m4a'],
    'Apps': ['.dmg', '.pkg', '.app', '.exe', '.msi', '.apk'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'Others': []
}

def get_category(ext):
    ext = ext.lower()
    for cat, exts in CATEGORY_MAP.items():
        if ext in exts:
            return cat
    return 'Others'

def get_folder_file_count(folder_path):
    if not os.path.exists(folder_path):
        return 0
    return len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])

def main():
    if len(sys.argv) < 3:
        print("用法: python organizer.py <目标目录> <计划JSON文件路径>")
        sys.exit(1)

    target_dir = sys.argv[1]
    plan_path = sys.argv[2]

    if not os.path.exists(target_dir):
        print(f"错误: 目标目录 {target_dir} 不存在。")
        sys.exit(1)

    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            plan = json.load(f)
    except Exception as e:
        print(f"读取计划文件失败: {e}")
        sys.exit(1)

    project_moves = plan.get('project_moves', [])
    fallback_moves = plan.get('fallback_moves', [])

    moved_count = 0

    print("=== 开始执行整理计划 ===")

    # 1. 处理项目归类
    for item in project_moves:
        filename = item.get('file')
        project = item.get('project')
        src = os.path.join(target_dir, filename)

        if not os.path.exists(src) or not os.path.isfile(src):
            continue

        dest_dir = os.path.join(target_dir, project)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, filename)

        shutil.move(src, dest)
        print(f"移动至项目: {filename} -> {project}/")
        moved_count += 1

    # 2. 处理兜底归类
    for filename in fallback_moves:
        src = os.path.join(target_dir, filename)
        if not os.path.exists(src) or not os.path.isfile(src):
            continue

        _, ext = os.path.splitext(filename)
        category = get_category(ext)
        category_dir = os.path.join(target_dir, category)
        os.makedirs(category_dir, exist_ok=True)

        # 检查是否超过50个文件
        if get_folder_file_count(category_dir) >= 50:
            mtime = os.path.getmtime(src)
            dt = datetime.fromtimestamp(mtime)
            month_folder = dt.strftime('%Y-%m')
            dest_dir = os.path.join(category_dir, month_folder)
        else:
            dest_dir = category_dir

        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, filename)

        shutil.move(src, dest)
        rel_path = os.path.relpath(dest, target_dir)
        print(f"兜底归类: {filename} -> {rel_path}")
        moved_count += 1

    print(f"\n整理完成！成功移动 {moved_count} 个文件。")

if __name__ == '__main__':
    main()
