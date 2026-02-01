#!/usr/bin/env python
# find_all_old_usage.py

"""
سكريبت للبحث عن جميع الاستخدامات القديمة في المشروع
"""

import os
import re

# الأنماط المراد البحث عنها
PATTERNS = [
    # استيرادات قديمة
    (r'from rent\.services\.recp import', 'استيراد من recp.py'),
    (r'from rent\.utils\.contract_statement import', 'استيراد من contract_statement.py'),
    (r'from services\.contract_modification_service import', 'استيراد من contract_modification_service.py'),
    
    # استخدام الكلاسات القديمة
    (r'ContractCalculator\(', 'استخدام ContractCalculator'),
    (r'ContractModificationService\(', 'استخدام ContractModificationService'),
    
    # استخدام الدوال القديمة (المستقلة)
    (r'generate_contract_statement\(', 'استدعاء generate_contract_statement'),
    (r'calculate_periods_with_payments\(', 'استدعاء calculate_periods_with_payments'),
    (r'generate_tenants_report\(', 'استدعاء generate_tenants_report'),
]

def search_in_file(filepath, patterns):
    """البحث عن الأنماط في ملف واحد"""
    matches = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for pattern, description in patterns:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1].strip()
                    
                    matches.append({
                        'line': line_num,
                        'content': line_content,
                        'description': description,
                        'pattern': pattern
                    })
    
    except Exception as e:
        print(f"⚠️  خطأ في قراءة {filepath}: {e}")
    
    return matches

def scan_directory(directory='rent', extensions=['.py']):
    """مسح المجلد بالكامل"""
    results = {}
    
    for root, dirs, files in os.walk(directory):
        # تخطي المجلدات غير المهمة
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
            'venv', 'env', '__pycache__', 'migrations', 'static', 'media'
        ]]
        
        for file in files:
            if not any(file.endswith(ext) for ext in extensions):
                continue
            
            filepath = os.path.join(root, file)
            matches = search_in_file(filepath, PATTERNS)
            
            if matches:
                results[filepath] = matches
    
    return results

def print_results(results):
    """طباعة النتائج بشكل منسق"""
    
    if not results:
        print("\n✅ ممتاز! لم يتم العثور على أي استخدامات قديمة.\n")
        return
    
    print("\n" + "=" * 100)
    print("🔍 الملفات التي تحتاج للتحديث:")
    print("=" * 100 + "\n")
    
    # تجميع حسب نوع المشكلة
    by_type = {}
    
    for filepath, matches in results.items():
        for match in matches:
            desc = match['description']
            if desc not in by_type:
                by_type[desc] = []
            by_type[desc].append((filepath, match))
    
    # طباعة حسب النوع
    for desc, items in sorted(by_type.items()):
        print(f"\n📌 {desc}: {len(items)} موضع")
        print("-" * 100)
        
        for filepath, match in items:
            print(f"   📄 {filepath}:{match['line']}")
            print(f"      {match['content'][:90]}")
        
        print()
    
    # ملخص إجمالي
    total_files = len(results)
    total_matches = sum(len(matches) for matches in results.values())
    
    print("=" * 100)
    print(f"📊 الملخص:")
    print(f"   • عدد الملفات: {total_files}")
    print(f"   • عدد المواضع: {total_matches}")
    print("=" * 100 + "\n")
    
    # قائمة الملفات للتحديث
    print("📋 قائمة الملفات التي تحتاج للتحديث:\n")
    for i, filepath in enumerate(sorted(results.keys()), 1):
        print(f"   {i}. {filepath}")
    print()

def generate_checklist(results):
    """إنشاء checklist للتحديث"""
    
    if not results:
        return
    
    print("\n✅ Checklist التحديث:\n")
    
    for i, (filepath, matches) in enumerate(sorted(results.items()), 1):
        print(f"- [ ] {filepath}")
        print(f"      • {len(matches)} موضع يحتاج تحديث")
        
        # عرض أنواع التحديثات المطلوبة
        types = set(m['description'] for m in matches)
        for t in types:
            print(f"        - {t}")
        print()

if __name__ == '__main__':
    print("\n🔍 البحث عن الاستخدامات القديمة...\n")
    
    # البحث في مجلد rent
    results = scan_directory('rent')
    
    # طباعة النتائج
    print_results(results)
    
    # إنشاء checklist
    generate_checklist(results)
    
    print("\n💡 الخطوات التالية:")
    print("   1. راجع الملفات أعلاه")
    print("   2. حدّث كل ملف ليستخدم ContractFinancialService")
    print("   3. اختبر بعد كل تحديث")
    print("   4. بعد التأكد، احذف الملفات القديمة:")
    print("      - rent/services/recp.py")
    print("      - rent/utils/contract_statement.py")
    print("      - services/contract_modification_service.py")
    print()