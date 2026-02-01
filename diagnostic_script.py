# diagnostic_script.py

"""
سكريبت تشخيصي شامل لفحص دقة الحسابات
يقارن النتائج ويكشف المشاكل المحتملة
"""

from django.db.models import Sum
from decimal import Decimal
from datetime import date
from rent.models import Contract
from rent.services.contract_financial_service import ContractFinancialService


def diagnose_contract(contract):
    """
    تشخيص شامل لعقد واحد
    """
    print("\n" + "=" * 100)
    print(f"📋 تشخيص العقد: {contract.contract_number}")
    print(f"   المستأجر: {contract.tenant.name if contract.tenant else 'N/A'}")
    print(f"   من: {contract.start_date} إلى: {contract.end_date}")
    print("=" * 100)
    
    # ✅ 1. معلومات العقد الأساسية
    print("\n📊 1. معلومات العقد الأساسية:")
    print(f"   • الإيجار السنوي (من الـ Model): {contract.annual_rent:,.2f}")
    print(f"   • دورية الدفع: {contract.get_payment_frequency_display()}")
    print(f"   • الحالة: {contract.get_status_display()}")
    
    # ✅ 2. التعديلات
    modifications = contract.modifications.filter(is_applied=True).order_by('effective_date')
    print(f"\n📝 2. التعديلات المطبقة: {modifications.count()}")
    
    if modifications.exists():
        for i, mod in enumerate(modifications, 1):
            print(f"   {i}. [{mod.get_modification_type_display()}] في {mod.effective_date}")
            if mod.modification_type in ['rent_increase', 'rent_decrease']:
                print(f"      من: {mod.old_rent_amount:,.2f} → إلى: {mod.new_rent_amount:,.2f}")
            elif mod.modification_type == 'discount':
                print(f"      مبلغ الخصم: {mod.discount_amount:,.2f}")
            elif mod.modification_type == 'vat':
                print(f"      ضريبة: {mod.vat_amount:,.2f}")
    
    # ✅ 3. حساب الفترات من الخدمة
    service = ContractFinancialService(contract)
    
    print("\n🔢 3. حساب الفترات (من ContractFinancialService):")
    periods = service.calculate_periods_with_modifications()
    
    total_from_periods = Decimal('0')
    print(f"   عدد الفترات: {len(periods)}")
    print("\n   تفاصيل الفترات:")
    print(f"   {'#':<5} {'من':<12} {'إلى':<12} {'المبلغ':>15} {'الإيجار السنوي':>18} {'المصدر':<15}")
    print("   " + "-" * 90)
    
    for p in periods:
        total_from_periods += p['due_amount']
        print(f"   {p['period_number']:<5} "
              f"{str(p['start_date']):<12} "
              f"{str(p.get('end_date', 'N/A')):<12} "
              f"{p['due_amount']:>15,.2f} "
              f"{p['annual_rent']:>18,.2f} "
              f"{p['source']:<15}")
    
    print("   " + "-" * 90)
    print(f"   {'الإجمالي:':<30} {total_from_periods:>15,.2f}")
    
    # ✅ 4. المدفوعات
    print("\n💰 4. المدفوعات:")
    receipts = contract.receipts.filter(
        status='posted',
        is_deleted=False
    ).order_by('receipt_date')
    
    total_paid = Decimal('0')
    print(f"   عدد السندات: {receipts.count()}")
    
    if receipts.exists():
        print("\n   تفاصيل السندات:")
        print(f"   {'رقم السند':<20} {'التاريخ':<12} {'المبلغ':>15}")
        print("   " + "-" * 50)
        
        for r in receipts:
            total_paid += r.amount
            print(f"   {r.receipt_number:<20} {str(r.receipt_date):<12} {r.amount:>15,.2f}")
        
        print("   " + "-" * 50)
        print(f"   {'الإجمالي:':<33} {total_paid:>15,.2f}")
    
    # ✅ 5. الحسابات من الخدمة
    print("\n🧮 5. الحسابات من ContractFinancialService:")
    
    data = service.calculate_periods_with_payments()
    totals = data['totals']
    
    print(f"   • إجمالي المستحق:     {totals['total_due']:>15,.2f}")
    print(f"   • إجمالي المدفوع:      {totals['total_paid']:>15,.2f}")
    print(f"   • إجمالي المتبقي:      {totals['total_remaining']:>15,.2f}")
    
    outstanding = service.get_outstanding_amount()
    print(f"   • المستحق (متأخر+حالي): {outstanding:>15,.2f}")
    
    # ✅ 6. كشف الحساب
    print("\n📄 6. كشف الحساب:")
    statement = service.generate_statement()
    
    if statement['success']:
        summary = statement['summary']
        print(f"   • إجمالي المدين:       {summary['total_debit']:>15,.2f}")
        print(f"   • إجمالي الدائن:       {summary['total_credit']:>15,.2f}")
        print(f"   • الرصيد النهائي:      {summary['final_balance']:>15,.2f}")
    else:
        print(f"   ❌ خطأ: {statement['error']}")
    
    # ✅ 7. التحقق من التطابق
    print("\n✅ 7. التحقق من التطابق:")
    
    # مقارنة 1: الفترات vs كشف الحساب
    if statement['success']:
        diff_periods_statement = total_from_periods - Decimal(str(summary['total_debit']))
        
        if diff_periods_statement == 0:
            print(f"   ✅ الفترات = كشف الحساب (المدين): {total_from_periods:,.2f}")
        else:
            print(f"   ❌ فرق بين الفترات وكشف الحساب: {diff_periods_statement:,.2f}")
            print(f"      • من الفترات: {total_from_periods:,.2f}")
            print(f"      • من كشف الحساب: {summary['total_debit']:,.2f}")
    
    # مقارنة 2: المدفوع المباشر vs الخدمة
    diff_paid = total_paid - totals['total_paid']
    
    if diff_paid == 0:
        print(f"   ✅ المدفوع (مباشر) = المدفوع (خدمة): {total_paid:,.2f}")
    else:
        print(f"   ❌ فرق في المدفوع: {diff_paid:,.2f}")
        print(f"      • من السندات مباشرة: {total_paid:,.2f}")
        print(f"      • من الخدمة: {totals['total_paid']:,.2f}")
    
    # مقارنة 3: الرصيد النهائي
    manual_balance = total_from_periods - total_paid
    service_balance = totals['total_remaining']
    
    if statement['success']:
        statement_balance = Decimal(str(summary['final_balance']))
        
        print(f"\n   📊 الرصيد النهائي (3 طرق):")
        print(f"      • يدوي (فترات - مدفوع):     {manual_balance:>15,.2f}")
        print(f"      • من الخدمة (total_remaining): {service_balance:>15,.2f}")
        print(f"      • من كشف الحساب (final_balance): {statement_balance:>15,.2f}")
        
        if manual_balance == service_balance == statement_balance:
            print(f"      ✅ جميع الطرق متطابقة!")
        else:
            print(f"      ❌ توجد اختلافات:")
            if manual_balance != service_balance:
                print(f"         • فرق (يدوي - خدمة): {manual_balance - service_balance:,.2f}")
            if manual_balance != statement_balance:
                print(f"         • فرق (يدوي - كشف): {manual_balance - statement_balance:,.2f}")
            if service_balance != statement_balance:
                print(f"         • فرق (خدمة - كشف): {service_balance - statement_balance:,.2f}")
    
    # ✅ 8. الفترات مع الدفعات (تفصيلي)
    print("\n📋 8. تفاصيل توزيع الدفعات على الفترات:")
    print(f"   {'#':<5} {'من':<12} {'المستحق':>12} {'المدفوع':>12} {'المتبقي':>12} {'الحالة':<10}")
    print("   " + "-" * 70)
    
    for p in data['periods']:
        print(f"   {p['period_number']:<5} "
              f"{str(p['start_date']):<12} "
              f"{p['due_amount']:>12,.2f} "
              f"{p['paid_amount']:>12,.2f} "
              f"{p['remaining_amount']:>12,.2f} "
              f"{p['status']:<10}")
    
    # ✅ 9. تحليل المشاكل المحتملة
    print("\n🔍 9. تحليل المشاكل المحتملة:")
    
    issues = []
    
    # مشكلة 1: الإيجار الأساسي
    if modifications.filter(modification_type__in=['rent_increase', 'rent_decrease']).exists():
        first_mod = modifications.filter(
            modification_type__in=['rent_increase', 'rent_decrease']
        ).first()
        
        if first_mod.old_rent_amount != contract.annual_rent:
            issues.append({
                'type': 'warning',
                'message': f'الإيجار في الـ Model ({contract.annual_rent:,.2f}) '
                          f'≠ الإيجار القديم في أول تعديل ({first_mod.old_rent_amount:,.2f})'
            })
    
    # مشكلة 2: تعديلات متكررة في نفس التاريخ
    dates = [m.effective_date for m in modifications]
    duplicates = [d for d in dates if dates.count(d) > 1]
    if duplicates:
        issues.append({
            'type': 'error',
            'message': f'تعديلات متكررة في نفس التاريخ: {set(duplicates)}'
        })
    
    # مشكلة 3: سندات بعد انتهاء العقد
    if contract.status == 'terminated' and contract.actual_end_date:
        late_receipts = receipts.filter(receipt_date__gt=contract.actual_end_date)
        if late_receipts.exists():
            issues.append({
                'type': 'warning',
                'message': f'{late_receipts.count()} سند بعد تاريخ إنهاء العقد'
            })
    
    # مشكلة 4: فترات بمبالغ صفرية
    zero_periods = [p for p in periods if p['due_amount'] == 0]
    if zero_periods:
        issues.append({
            'type': 'warning',
            'message': f'{len(zero_periods)} فترة بمبلغ صفري'
        })
    
    if issues:
        for issue in issues:
            icon = "⚠️" if issue['type'] == 'warning' else "❌"
            print(f"   {icon} {issue['message']}")
    else:
        print("   ✅ لم يتم اكتشاف مشاكل واضحة")
    
    print("\n" + "=" * 100)
    
    return {
        'contract': contract,
        'total_from_periods': total_from_periods,
        'total_paid': total_paid,
        'manual_balance': manual_balance,
        'service_balance': service_balance,
        'statement_balance': statement_balance if statement['success'] else None,
        'issues': issues
    }


def diagnose_all_contracts(limit=None):
    """
    تشخيص جميع العقود النشطة
    """
    contracts = Contract.objects.filter(status='active')
    
    if limit:
        contracts = contracts[:limit]
    
    print("\n" + "=" * 100)
    print(f"🔍 تشخيص {contracts.count()} عقد نشط")
    print("=" * 100)
    
    all_results = []
    
    for contract in contracts:
        result = diagnose_contract(contract)
        all_results.append(result)
    
    # ملخص عام
    print("\n" + "=" * 100)
    print("📊 الملخص العام:")
    print("=" * 100)
    
    total_issues = sum(len(r['issues']) for r in all_results)
    contracts_with_issues = sum(1 for r in all_results if r['issues'])
    
    print(f"\n   • إجمالي العقود: {len(all_results)}")
    print(f"   • عقود بها مشاكل: {contracts_with_issues}")
    print(f"   • إجمالي المشاكل: {total_issues}")
    
    # العقود مع اختلافات في الرصيد
    mismatched = []
    
    for r in all_results:
        if r['statement_balance'] is not None:
            if (r['manual_balance'] != r['service_balance'] or 
                r['manual_balance'] != r['statement_balance']):
                mismatched.append(r)
    
    if mismatched:
        print(f"\n   ⚠️  {len(mismatched)} عقد مع اختلاف في الأرصدة:")
        print(f"\n   {'رقم العقد':<20} {'يدوي':>15} {'خدمة':>15} {'كشف':>15}")
        print("   " + "-" * 70)
        
        for r in mismatched:
            print(f"   {r['contract'].contract_number:<20} "
                  f"{r['manual_balance']:>15,.2f} "
                  f"{r['service_balance']:>15,.2f} "
                  f"{r['statement_balance']:>15,.2f}")
    else:
        print("\n   ✅ جميع الأرصدة متطابقة!")
    
    print("\n" + "=" * 100)


# ========================================
# الاستخدام
# ========================================

if __name__ == '__main__':
    import django
    import os
    
    # تهيئة Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental.settings')
    django.setup()
    
    print("\n🔍 سكريبت التشخيص الشامل للحسابات")
    print("=" * 100)
    
    # خيارات:
    
    # 1. تشخيص عقد واحد
    # contract = Contract.objects.get(id=8)  # ← ضع ID العقد
    # diagnose_contract(contract)
    
    # 2. تشخيص أول 5 عقود
    # diagnose_all_contracts(limit=5)
    
    # 3. تشخيص جميع العقود
    diagnose_all_contracts()