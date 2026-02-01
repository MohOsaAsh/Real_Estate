# simple_auto_fix.py

"""
سكريبت التحديث التلقائي - نسخة مبسطة وآمنة
يحدّث 4 ملفات فقط بطريقة آمنة
"""

import os
import shutil

def backup_and_fix():
    """التحديث الآمن مع نسخ احتياطية"""
    
    print("\n" + "=" * 80)
    print("🔧 سكريبت التحديث التلقائي")
    print("=" * 80 + "\n")
    
    # التحقق من المجلد
    if not os.path.exists('rent'):
        print("❌ خطأ: تأكد أنك في مجلد المشروع (حيث manage.py)")
        return
    
    files_to_update = [
        'rent/forms/ReceiptForm.py',
        'rent/models/report_models.py',
        'rent/models/tenant_models.py',
    ]
    
    print("📋 الملفات المراد تحديثها:\n")
    for i, f in enumerate(files_to_update, 1):
        exists = "✅" if os.path.exists(f) else "❌"
        print(f"   {i}. {exists} {f}")
    
    print("\n" + "=" * 80)
    confirm = input("\n❓ المتابعة؟ (y/n): ").lower()
    
    if confirm != 'y':
        print("❌ تم الإلغاء")
        return
    
    print("\n🔄 جارٍ التحديث...\n")
    
    # ═══════════════════════════════════════════════════════════
    # 1. ReceiptForm.py
    # ═══════════════════════════════════════════════════════════
    
    file1 = 'rent/forms/ReceiptForm.py'
    if os.path.exists(file1):
        print(f"📄 {file1}")
        
        # نسخة احتياطية
        shutil.copy(file1, file1 + '.backup')
        print("   💾 نسخة احتياطية: ✅")
        
        with open(file1, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # التعديلات
        if 'contract.calculator.calculate_periods_with_payments()' in content:
            content = content.replace(
                'contract.calculator.calculate_periods_with_payments()',
                'service.calculate_periods_with_payments()'
            )
            
            # إضافة الاستيراد إذا لم يكن موجوداً
            if 'ContractFinancialService' not in content:
                lines = content.split('\n')
                # البحث عن آخر سطر استيراد
                last_import = 0
                for i, line in enumerate(lines):
                    if line.startswith('from ') or line.startswith('import '):
                        last_import = i
                
                lines.insert(last_import + 1, 'from rent.services.contract_financial_service import ContractFinancialService')
                content = '\n'.join(lines)
            
            # إضافة إنشاء service
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'service.calculate_periods_with_payments()' in line and i > 0:
                    # التحقق إذا service موجود قبلها
                    prev_lines = '\n'.join(lines[max(0, i-5):i])
                    if 'service = ContractFinancialService' not in prev_lines:
                        indent = len(line) - len(line.lstrip())
                        lines.insert(i, ' ' * indent + 'service = ContractFinancialService(contract)')
                        break
            content = '\n'.join(lines)
            
            # حفظ
            with open(file1, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("   ✅ تم التحديث")
        else:
            print("   ℹ️  لا يحتاج تحديث")
    
    # ═══════════════════════════════════════════════════════════
    # 2. report_models.py
    # ═══════════════════════════════════════════════════════════
    
    file2 = 'rent/models/report_models.py'
    if os.path.exists(file2):
        print(f"\n📄 {file2}")
        
        # نسخة احتياطية
        shutil.copy(file2, file2 + '.backup')
        print("   💾 نسخة احتياطية: ✅")
        
        with open(file2, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # التعديلات
        changed = False
        
        if 'ContractCalculator(contract, end_date)' in content:
            content = content.replace(
                'ContractCalculator(contract, end_date)',
                'ContractFinancialService(contract, as_of_date=end_date)'
            )
            changed = True
        
        if 'calculator = ' in content:
            content = content.replace('calculator = ', 'service = ')
            content = content.replace('calculator.', 'service.')
            changed = True
        
        # حذف استيراد قديم
        if 'from rent.services.recp import' in content:
            content = content.replace(
                'from rent.services.recp import ContractCalculator\n',
                ''
            )
            content = content.replace(
                'from rent.services.recp import ContractCalculator',
                ''
            )
        
        # إضافة استيراد جديد
        if 'ContractFinancialService' not in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from django') or line.startswith('from rent'):
                    lines.insert(i, 'from rent.services.contract_financial_service import ContractFinancialService')
                    break
            content = '\n'.join(lines)
            changed = True
        
        if changed:
            with open(file2, 'w', encoding='utf-8') as f:
                f.write(content)
            print("   ✅ تم التحديث")
        else:
            print("   ℹ️  لا يحتاج تحديث")
    
    # ═══════════════════════════════════════════════════════════
    # 3. tenant_models.py
    # ═══════════════════════════════════════════════════════════
    
    file3 = 'rent/models/tenant_models.py'
    if os.path.exists(file3):
        print(f"\n📄 {file3}")
        
        # نسخة احتياطية
        shutil.copy(file3, file3 + '.backup')
        print("   💾 نسخة احتياطية: ✅")
        
        with open(file3, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # التعديلات
        changed = False
        
        if 'ContractCalculator(contract)' in content:
            content = content.replace(
                'ContractCalculator(contract)',
                'ContractFinancialService(contract)'
            )
            changed = True
        
        if 'calculator = ' in content:
            content = content.replace('calculator = ', 'service = ')
            content = content.replace('calculator.', 'service.')
            changed = True
        
        # حذف استيراد قديم
        if 'from rent.services.recp import' in content:
            content = content.replace(
                'from rent.services.recp import ContractCalculator\n',
                ''
            )
            content = content.replace(
                'from rent.services.recp import ContractCalculator',
                ''
            )
        
        # إضافة استيراد جديد
        if 'ContractFinancialService' not in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from django') or line.startswith('from rent'):
                    lines.insert(i, 'from rent.services.contract_financial_service import ContractFinancialService')
                    break
            content = '\n'.join(lines)
            changed = True
        
        if changed:
            with open(file3, 'w', encoding='utf-8') as f:
                f.write(content)
            print("   ✅ تم التحديث")
        else:
            print("   ℹ️  لا يحتاج تحديث")
    
    # ═══════════════════════════════════════════════════════════
    # النتيجة النهائية
    # ═══════════════════════════════════════════════════════════
    
    print("\n" + "=" * 80)
    print("✅ تم الانتهاء!")
    print("=" * 80 + "\n")
    
    print("💡 الخطوات التالية:\n")
    print("   1. اختبر التطبيق:")
    print("      python manage.py runserver\n")
    print("   2. إذا حدث خطأ، استعد النسخ الاحتياطية:")
    print("      - rent/forms/ReceiptForm.py.backup")
    print("      - rent/models/report_models.py.backup")
    print("      - rent/models/tenant_models.py.backup\n")
    print("   3. بعد التأكد من عمل كل شيء:")
    print("      - احذف النسخ الاحتياطية (.backup)")
    print("      - احذف مجلد 'rent/services/old file'\n")

if __name__ == '__main__':
    backup_and_fix()