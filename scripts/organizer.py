#!/usr/bin/env python3
"""
File Organizer Engine
Usage: python organizer.py <target_directory> <plan_json_path>
"""
import sys
import os
import shutil
import json
import datetime
from pathlib import Path

# 扩展名到基础分类的映射字典
EXTENSION_MAP = {
    # 图片
    '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images', '.gif': 'Images', 
    '.svg': 'Images', '.webp': 'Images', '.heic': 'Images',
    # 文档
    '.pdf': 'Documents', '.doc': 'Documents', '.docx': 'Documents', 
    '.txt': 'Documents', '.md': 'Documents', '.rtf': 'Documents',
    # 表格/演示
    '.xls': 'Documents', '.xlsx': 'Documents', '.csv': 'Documents',
    '.ppt': 'Documents', '.pptx': 'Documents',
    # 媒体
    '.mp4': 'Media', '.mov': 'Media', '.mp3': 'Media', '.wav': 'Media',
    # 安装包/压缩包
    '.zip': 'Archives', '.rar': 'Archives', '.7z': 'Archives', '.tar': 'Archives', '.gz': 'Archives',
    '.dmg': 'Apps', '.pkg': 'Apps', '.exe': 'Apps', '.apk': 'Apps'
}

def get_fallback_category(file_path):
    ext = file_path.suffix.lower()
    return EXTENSION_MAP.get(ext, 'Others')

def ensure_month_subfolder(target_category_dir, file_path):
    """
    检查目标分类文件夹下是否超过 50 个文件。
    如果超过，根据被移动文件的修改时间返回一个月份子文件夹路径 (如 '2026-04')。
    如果不超过，直接返回目标分类文件夹路径。
    注意：只计算顶层文件数，不包括已有的子目录。
    """
    if not target_category_dir.exists():
        target_category_dir.mkdir(parents=True, exist_ok=True)
        return target_category_dir
        
    file_count = sum(1 for item in target_category_dir.iterdir() if item.is_file())
    
    if file_count >= 50:
        mtime = file_path.stat().st_mtime
        dt = datetime.datetime.fromtimestamp(mtime)
        month_folder_name = dt.strftime("%Y-%m")
        month_dir = target_category_dir / month_folder_name
        month_dir.mkdir(parents=True, exist_ok=True)
        return month_dir
    return target_category_dir

def handle_duplicate_name(dest_path):
    """如果目标文件已存在，则自动添加时间戳后缀"""
    if not dest_path.exists():
        return dest_path
    
    stem = dest_path.stem
    ext = dest_path.suffix
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = f"{stem}_{timestamp}{ext}"
    return dest_path.parent / new_name

def execute_plan(target_dir, plan_data):
    base_dir = Path(target_dir).resolve()
    success_count = 0
    errors = []
    
    # plan_data 结构示例：
    # {
    #   "projects": {
    #       "Project_A": ["file1.pdf", "file2.jpg"],
    #       "Design_B": ["logo.png"]
    #   },
    #   "fallback": ["report.docx", "installer.dmg", "unknown_file"]
    # }
    
    # 1. 处理归属项目的文件
    projects = plan_data.get('projects', {})
    for project_name, file_names in projects.items():
        project_dir = base_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        for fname in file_names:
            src = base_dir / fname
            if not src.exists() or not src.is_file():
                errors.append(f"Not found or not a file: {fname}")
                continue
            
            dest = handle_duplicate_name(project_dir / fname)
            try:
                shutil.move(str(src), str(dest))
                success_count += 1
            except Exception as e:
                errors.append(f"Failed to move {fname}: {e}")
                
    # 2. 处理需要兜底分类的文件
    fallback_files = plan_data.get('fallback', [])
    for fname in fallback_files:
        src = base_dir / fname
        if not src.exists() or not src.is_file():
            errors.append(f"Not found or not a file: {fname}")
            continue
            
        category = get_fallback_category(src)
        category_dir = base_dir / category
        
        # 检查是否需要触发超 50 个文件的按月分子文件夹机制
        final_dest_dir = ensure_month_subfolder(category_dir, src)
        dest = handle_duplicate_name(final_dest_dir / fname)
        
        try:
            shutil.move(str(src), str(dest))
            success_count += 1
        except Exception as e:
            errors.append(f"Failed to move {fname} to fallback: {e}")
            
    return success_count, errors

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python organizer.py <target_directory> <plan_json_path>")
        sys.exit(1)
        
    target_dir = sys.argv[1]
    plan_path = sys.argv[2]
    
    try:
        with open(plan_path, 'r', encoding='utf-8') as f:
            plan = json.load(f)
    except Exception as e:
        print(f"Error reading plan JSON: {e}")
        sys.exit(1)
        
    print(f"Starting organization in {target_dir}...")
    success, errs = execute_plan(target_dir, plan)
    
    print(f"\nOrganization Complete: {success} files moved successfully.")
    if errs:
        print("\nErrors encountered:")
        for err in errs:
            print(f"- {err}")
