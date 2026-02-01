"""
Contract Utilities
دوال مساعدة للعقود
"""
from dateutil.relativedelta import relativedelta
from typing import List, Tuple, Optional
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum, Q
import logging

logger = logging.getLogger(__name__)


def calculate_contract_due_dates(contract) -> List[date]:
    """
    حساب تواريخ الاستحقاق للعقد
    
    Args:
        contract: Contract object
    
    Returns:
        List of due dates
    
    Example:
        >>> due_dates = calculate_contract_due_dates(contract)
        >>> print(due_dates)
        [datetime.date(2024, 1, 1), datetime.date(2024, 7, 1), ...]
    """
    if not contract or not contract.start_date or not contract.end_date:
        return []
    
    frequency_map = {
        'monthly': 1,
        'quarterly': 3,
        'semi_annual': 6,
        'annual': 12,
    }
    
    period_months = frequency_map.get(contract.payment_frequency, 6)
    due_dates = []
    current_date = contract.start_date
    
    # حماية من infinite loop
    MAX_PERIODS = 1000
    count = 0
    
    while current_date <= contract.end_date and count < MAX_PERIODS:
        due_dates.append(current_date)
        next_date = current_date + relativedelta(months=period_months)
        
        # التوقف إذا تجاوز التاريخ التالي نهاية العقد
        if next_date > contract.end_date:
            break
            
        current_date = next_date
        count += 1
    
    return due_dates


def format_due_dates_error_message(due_dates: List[date], max_display: int = 5) -> str:
    """
    تنسيق رسالة خطأ تواريخ الاستحقاق
    
    Args:
        due_dates: قائمة التواريخ
        max_display: عدد التواريخ المعروضة
    
    Returns:
        رسالة الخطأ منسقة
    
    Example:
        >>> msg = format_due_dates_error_message(due_dates, 3)
        >>> print(msg)
        تاريخ السريان يجب أن يكون أحد تواريخ الاستحقاق:
        2024-01-01, 2024-07-01, 2025-01-01
        ... و 7 تاريخ آخر
    """
    if not due_dates:
        return 'لا توجد تواريخ استحقاق متاحة'
    
    dates_str = ', '.join([d.strftime('%Y-%m-%d') for d in due_dates[:max_display]])
    remaining = len(due_dates) - max_display
    
    msg = f'تاريخ السريان يجب أن يكون أحد تواريخ الاستحقاق:\n{dates_str}'
    if remaining > 0:
        msg += f'\n... و {remaining} تاريخ آخر'
    
    return msg


def validate_modification_date(modification_date: date, contract) -> Tuple[bool, Optional[str]]:
    """
    التحقق من صحة تاريخ التعديل
    
    Args:
        modification_date: تاريخ التعديل المطلوب
        contract: Contract object
    
    Returns:
        Tuple: (is_valid: bool, error_message: str or None)
    
    Example:
        >>> is_valid, error = validate_modification_date(date(2024, 6, 1), contract)
        >>> if not is_valid:
        >>>     print(error)
    """
    if not modification_date or not contract:
        return False, 'يجب تحديد تاريخ التعديل والعقد'
    
    due_dates = calculate_contract_due_dates(contract)
    
    if not due_dates:
        return False, 'لا يمكن حساب تواريخ الاستحقاق للعقد'
    
    if modification_date not in due_dates:
        return False, format_due_dates_error_message(due_dates)
    
    return True, None


def calculate_rent_change(old_rent: Decimal, new_rent: Decimal) -> Tuple[Decimal, Decimal]:
    """
    حساب مبلغ ونسبة التغيير في الإيجار
    
    Args:
        old_rent: الإيجار القديم
        new_rent: الإيجار الجديد
    
    Returns:
        Tuple: (change_amount, change_percentage)
    
    Example:
        >>> change, percentage = calculate_rent_change(Decimal('10000'), Decimal('11000'))
        >>> print(f"التغيير: {change}, النسبة: {percentage}%")
        التغيير: 1000, النسبة: 10.00%
    """
    if not old_rent or not new_rent:
        return Decimal('0'), Decimal('0')
    
    change_amount = new_rent - old_rent
    
    if old_rent > 0:
        change_percentage = (change_amount / old_rent) * 100
    else:
        change_percentage = Decimal('0')
    
    return change_amount, change_percentage


def calculate_vat_amount(base_amount: Decimal, vat_percentage: Decimal = Decimal('15.00')) -> Decimal:
    """
    حساب مبلغ القيمة المضافة
    
    Args:
        base_amount: المبلغ الأساسي
        vat_percentage: نسبة القيمة المضافة (افتراضي: 15%)
    
    Returns:
        مبلغ القيمة المضافة
    
    Example:
        >>> vat = calculate_vat_amount(Decimal('10000'), Decimal('15'))
        >>> print(vat)
        1500.00
    """
    if not base_amount or base_amount <= 0:
        return Decimal('0')
    
    if not vat_percentage or vat_percentage < 0:
        vat_percentage = Decimal('15.00')
    
    vat_amount = (base_amount * vat_percentage) / 100
    return vat_amount.quantize(Decimal('0.01'))


def get_period_months_from_frequency(frequency: str) -> int:
    """
    الحصول على عدد الأشهر حسب تكرار الدفع
    
    Args:
        frequency: تكرار الدفع ('monthly', 'quarterly', 'semi_annual', 'annual')
    
    Returns:
        عدد الأشهر
    
    Example:
        >>> months = get_period_months_from_frequency('quarterly')
        >>> print(months)
        3
    """
    frequency_map = {
        'monthly': 1,
        'quarterly': 3,
        'semi_annual': 6,
        'annual': 12,
    }
    
    return frequency_map.get(frequency, 6)  # افتراضي: نصف سنوي




def calculate_termination_settlement(contract, termination_date):
    """
    حساب التسوية المالية عند إنهاء العقد - ديناميكياً
    
    Args:
        contract: العقد
        termination_date: تاريخ الإنهاء
    
    Returns:
        dict: تفاصيل التسوية
    """
    if not contract or not termination_date:
        return {
            'success': False,
            'error': 'بيانات غير صحيحة',
            'outstanding_balance': Decimal('0.00'),
            'prorated_rent': Decimal('0.00'),
            'total_amount_due': Decimal('0.00'),
        }
    
    try:
        # 1. حساب تواريخ الاستحقاق
        due_dates = calculate_contract_due_dates(contract)
        
        if not due_dates:
            return {
                'success': False,
                'error': 'لا يمكن حساب تواريخ الاستحقاق',
                'outstanding_balance': Decimal('0.00'),
                'prorated_rent': Decimal('0.00'),
                'total_amount_due': Decimal('0.00'),
            }
        
        # 2. الحصول على المدفوعات الفعلية
        from rent.models.receipt_models import Receipt
        
        total_paid = Receipt.objects.filter(
            contract=contract,
            status__in=['posted', 'cleared'],
            is_deleted=False
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # 3. حساب معلومات الفترات
        frequency_map = {
            'monthly': 1,
            'quarterly': 3,
            'semi_annual': 6,
            'annual': 12,
        }
        
        period_months = frequency_map.get(contract.payment_frequency, 6)
        period_rent = contract.annual_rent / (12 / period_months)
        
        # 4. حساب عدد الفترات الكاملة والجزئية
        full_periods = 0
        last_due_date = None
        
        for due_date in due_dates:
            if due_date <= termination_date:
                full_periods += 1
                last_due_date = due_date
            else:
                break
        
        # الإيجار عن الفترات الكاملة
        full_periods_rent = period_rent * full_periods
        
        # 5. حساب الإيجار الجزئي
        prorated_rent = Decimal('0.00')
        days_in_partial_period = 0
        next_due_date = None
        
        if last_due_date and last_due_date < termination_date:
            # التاريخ التالي
            next_due_date = last_due_date + relativedelta(months=period_months)
            
            # التأكد من عدم تجاوز نهاية العقد
            if next_due_date > contract.end_date:
                next_due_date = contract.end_date
            
            # حساب الأيام
            total_days_in_period = (next_due_date - last_due_date).days
            days_used = (termination_date - last_due_date).days
            days_in_partial_period = days_used
            
            # حساب الإيجار بالنسبة
            if total_days_in_period > 0:
                daily_rate = period_rent / Decimal(str(total_days_in_period))
                prorated_rent = daily_rate * Decimal(str(days_used))
                prorated_rent = prorated_rent.quantize(
                    Decimal('0.01'),
                    rounding=ROUND_HALF_UP
                )
        
        # 6. حساب المديونية
        total_rent_due = full_periods_rent + prorated_rent
        outstanding_balance = total_rent_due - total_paid
        outstanding_balance = outstanding_balance.quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        
        # 7. تحضير التفاصيل
        settlement_details = {
            'contract_id': contract.id,
            'contract_number': contract.contract_number,
            'tenant_name': contract.tenant.name if contract.tenant else 'N/A',
            
            # التواريخ
            'contract_start_date': contract.start_date.isoformat(),
            'contract_end_date': contract.end_date.isoformat(),
            'termination_date': termination_date.isoformat(),
            'last_due_date': last_due_date.isoformat() if last_due_date else None,
            'next_due_date': next_due_date.isoformat() if next_due_date else None,
            
            # المبالغ
            'annual_rent': float(contract.annual_rent),
            'payment_frequency': contract.payment_frequency,
            'period_months': period_months,
            'period_rent': float(period_rent),
            
            # الفترات
            'full_periods_count': full_periods,
            'full_periods_rent': float(full_periods_rent),
            'days_in_partial_period': days_in_partial_period,
            'prorated_rent': float(prorated_rent),
            
            # المالية
            'total_rent_due': float(total_rent_due),
            'total_paid': float(total_paid),
            'outstanding_balance': float(outstanding_balance),
            
            # معلومات إضافية
            'calculation_date': date.today().isoformat(),
            'is_overpaid': outstanding_balance < 0,
            'is_settled': outstanding_balance == 0,
            'has_outstanding': outstanding_balance > 0,
        }
        
        logger.info(
            f'Settlement calculated for contract {contract.id}: '
            f'Due={total_rent_due}, Paid={total_paid}, '
            f'Outstanding={outstanding_balance}'
        )
        
        return {
            'success': True,
            'outstanding_balance': outstanding_balance,
            'prorated_rent': prorated_rent,
            'total_amount_due': outstanding_balance,
            'total_rent_due': total_rent_due,
            'total_paid': total_paid,
            'settlement_details': settlement_details,
        }
    
    except Exception as e:
        logger.error(
            f'Error calculating settlement for contract {contract.id}: {str(e)}',
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e),
            'outstanding_balance': Decimal('0.00'),
            'prorated_rent': Decimal('0.00'),
            'total_amount_due': Decimal('0.00'),
        }


def get_contract_settlement_summary(contract):
    """
    الحصول على ملخص التسوية لعقد معين
    (يمكن استخدامها في أي مكان للحصول على حالة المديونية)
    
    Args:
        contract: العقد
    
    Returns:
        dict: ملخص التسوية
    """
    from rent.models.receipt_models import Receipt
    
    # إجمالي المستحق (من الفواتير أو حساب يدوي)
    total_due = Decimal('0.00')
    
    # يمكن حساب المستحق بناءً على تواريخ الاستحقاق حتى اليوم
    due_dates = calculate_contract_due_dates(contract)
    today = date.today()
    
    frequency_map = {
        'monthly': 1,
        'quarterly': 3,
        'semi_annual': 6,
        'annual': 12,
    }
    
    period_months = frequency_map.get(contract.payment_frequency, 6)
    period_rent = contract.annual_rent / (12 / period_months)
    
    for due_date in due_dates:
        if due_date <= today:
            total_due += period_rent
        else:
            break
    
    # إجمالي المدفوع
    total_paid = Receipt.objects.filter(
        contract=contract,
        status__in=['posted', 'cleared'],
        is_deleted=False
    ).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    # المديونية
    balance = total_due - total_paid
    
    return {
        'contract': contract,
        'total_due': total_due,
        'total_paid': total_paid,
        'outstanding_balance': balance,
        'is_settled': balance == 0,
        'has_outstanding': balance > 0,
        'is_overpaid': balance < 0,
        'as_of_date': today,
    }


def format_settlement_report(settlement):
    """
    تنسيق تقرير التسوية للعرض
    """
    if not settlement or not settlement.get('success'):
        return '❌ خطأ في حساب التسوية'
    
    details = settlement.get('settlement_details', {})
    
    report = f"""
╔════════════════════════════════════════════════════════════╗
║              تقرير تسوية إنهاء العقد                      ║
╚════════════════════════════════════════════════════════════╝

📋 معلومات العقد:
  • رقم العقد: {details.get('contract_number')}
  • المستأجر: {details.get('tenant_name')}
  • تاريخ البداية: {details.get('contract_start_date')}
  • تاريخ النهاية الأصلي: {details.get('contract_end_date')}
  • تاريخ الإنهاء الفعلي: {details.get('termination_date')}
  • الإيجار السنوي: {details.get('annual_rent'):,.2f} ريال

📊 حسابات الفترات:
  • تكرار الدفع: {details.get('payment_frequency')}
  • إيجار الفترة الواحدة: {details.get('period_rent'):,.2f} ريال
  • عدد الفترات الكاملة: {details.get('full_periods_count')}
  • إيجار الفترات الكاملة: {details.get('full_periods_rent'):,.2f} ريال

📅 الفترة الجزئية:
  • من: {details.get('last_due_date')}
  • إلى: {details.get('termination_date')}
  • عدد الأيام: {details.get('days_in_partial_period')} يوم
  • إيجار الفترة الجزئية: {details.get('prorated_rent'):,.2f} ريال

💰 التسوية المالية:
  • إجمالي الإيجار المستحق: {details.get('total_rent_due'):,.2f} ريال
  • إجمالي المدفوع: {details.get('total_paid'):,.2f} ريال
  • ═══════════════════════════════════════════════════
  • المديونية المتبقية: {details.get('outstanding_balance'):,.2f} ريال
  
📅 تاريخ الحساب: {details.get('calculation_date')}
"""
    
    # إضافة التنبيه حسب الحالة
    balance = details.get('outstanding_balance', 0)
    
    if balance > 0:
        report += f"\n⚠️  تنبيه: يوجد مديونية يجب تحصيلها!"
    elif balance < 0:
        report += f"\nℹ️  ملاحظة: يوجد رصيد زائد يجب إعادته للمستأجر."
    else:
        report += f"\n✅ الحساب متوازن - لا توجد مديونية."
    
    return report




def calculate_rent_change(old_rent, new_rent):
    """
    حساب مبلغ ونسبة التغيير في الإيجار مع تقريب ذكي
    """
    if not old_rent or not new_rent:
        return Decimal('0.00'), Decimal('0.00')
    
    # تحويل إلى Decimal
    if not isinstance(old_rent, Decimal):
        old_rent = Decimal(str(old_rent))
    if not isinstance(new_rent, Decimal):
        new_rent = Decimal(str(new_rent))
    
    # حساب مبلغ التغيير
    change_amount = new_rent - old_rent
    change_amount = change_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # حساب النسبة
    if old_rent > 0:
        change_percentage = (change_amount / old_rent) * 100
        # التقريب إلى 4 أرقام بعد الفاصلة
        change_percentage = change_percentage.quantize(
            Decimal('0.0001'),
            rounding=ROUND_HALF_UP
        )
    else:
        change_percentage = Decimal('0.0000')
    
    return change_amount, change_percentage