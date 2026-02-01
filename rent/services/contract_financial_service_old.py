"""
خدمة موحدة للحسابات المالية للعقود - نسخة محسّنة ومضغوطة
"""

from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Tuple, Optional
import logging
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def handle_errors(default_return=None, log_message="Error"):
    """Decorator للمعالجة الموحدة للأخطاء"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                contract_id = getattr(getattr(args[0], 'contract', None), 'id', 'unknown')
                logger.error(f'{log_message} for contract {contract_id}: {e}', exc_info=True)
                return default_return
        return wrapper
    return decorator


class ContractStatementLine:
    """سطر في كشف الحساب"""
    __slots__ = ('date', 'type', 'description', 'debit', 'credit', 'balance', 'reference', 'period_number')
    
    def __init__(self, line_date, line_type, description, debit=0, credit=0, balance=0, reference=None, period_number=None):
        self.date = line_date
        self.type = line_type
        self.description = description
        self.debit = Decimal(str(debit))
        self.credit = Decimal(str(credit))
        self.balance = Decimal(str(balance))
        self.reference = reference
        self.period_number = period_number
    
    def __repr__(self):
        return f"<StatementLine {self.date} - {self.type}: D={self.debit}, C={self.credit}, B={self.balance}>"
    
    def to_dict(self):
        return {
            'date': self.date.isoformat() if self.date else None,
            'type': self.type,
            'description': self.description,
            'debit': float(self.debit),
            'credit': float(self.credit),
            'balance': float(self.balance),
            'reference': self.reference,
            'period_number': self.period_number,
        }


class PropertyContextManager:
    """إدارة معلومات العقار والمستأجر"""
    
    def __init__(self, contract):
        self.contract = contract
        self.unit = None
        self.unit_number = 'غير محدد'
        self.building = None
        self.building_name = 'غير محدد'
        self.location = 'غير محدد'
        self._initialize()
    
    def _initialize(self):
        if hasattr(self.contract, 'unit') and self.contract.unit:
            self.unit = self.contract.unit
            self.unit_number = (getattr(self.unit, 'unit_number', None) or 
                              getattr(self.unit, 'number', None) or 
                              getattr(self.unit, 'name', None) or 'غير محدد')
            if hasattr(self.unit, 'building') and self.unit.building:
                self.building = self.unit.building
        
        if not self.building and hasattr(self.contract, 'building') and self.contract.building:
            self.building = self.contract.building
        
        if self.building:
            self.building_name = (getattr(self.building, 'name', None) or 
                                getattr(self.building, 'building_name', None) or 
                                f'مبنى رقم {getattr(self.building, "id", "غير محدد")}')
            self.location = getattr(self.building, 'location', self.location)
        
        if self.location == 'غير محدد' and hasattr(self.contract, 'property') and self.contract.property:
            self.location = (getattr(self.contract.property, 'location', None) or 
                           getattr(self.contract.property, 'address', None) or 'غير محدد')
    
    @property
    def tenant(self):
        return getattr(self.contract, 'tenant', None)
    
    @property
    def tenant_name(self):
        return getattr(self.tenant, 'name', 'غير محدد') if self.tenant else 'غير محدد'
    
    @property
    def tenant_id(self):
        return getattr(self.tenant, 'id', None) if self.tenant else None
    
    @property
    def contract_number(self):
        return getattr(self.contract, 'contract_number', 'غير محدد')


class PeriodCalculator:
    """حساب فترات العقد مع التعديلات"""
    
    FREQUENCY_MAP = {
        'monthly': Decimal('1'), 'quarterly': Decimal('3'),
        'semi_annual': Decimal('6'), 'annual': Decimal('12'),
    }
    
    def __init__(self, contract, as_of_date=None):
        self.contract = contract
        self.as_of_date = as_of_date or date.today()
    
    @handle_errors(default_return=[], log_message="Error calculating periods")
    def calculate_periods_with_modifications(self, end_date=None, include_future=False):
        from rent.utils.contract_utils import calculate_contract_due_dates
        
        end_date = self._get_effective_end_date(end_date)
        due_dates = calculate_contract_due_dates(self.contract)
        if not due_dates:
            logger.warning(f'No due dates for contract {self.contract.id}')
            return []
        
        period_months = self.FREQUENCY_MAP.get(self.contract.payment_frequency, Decimal('6'))
        rent_timeline = self._build_rent_timeline(period_months)
        return self._create_periods(due_dates, end_date, include_future, period_months, rent_timeline)
    
    def _get_effective_end_date(self, end_date):
        if not end_date:
            end_date = self.as_of_date
        if (self.contract.status == 'terminated' and self.contract.actual_end_date and 
            end_date > self.contract.actual_end_date):
            return self.contract.actual_end_date
        return end_date
    
    def _build_rent_timeline(self, period_months):
        rent_mods = list(self.contract.modifications.filter(
            modification_type__in=['rent_increase', 'rent_decrease'], is_applied=True
        ).order_by('effective_date').values('id', 'effective_date', 'old_rent_amount', 'new_rent_amount'))
        
        base_annual_rent = rent_mods[0]['old_rent_amount'] if rent_mods else self.contract.annual_rent
        base_period_rent = base_annual_rent * period_months / Decimal('12')
        
        timeline = [{
            'from_date': self.contract.start_date,
            'to_date': rent_mods[0]['effective_date'] if rent_mods else None,
            'annual_rent': base_annual_rent,
            'period_rent': base_period_rent,
            'source': 'base'
        }]
        
        for i, mod in enumerate(rent_mods):
            timeline.append({
                'from_date': mod['effective_date'],
                'to_date': rent_mods[i + 1]['effective_date'] if i + 1 < len(rent_mods) else None,
                'annual_rent': mod['new_rent_amount'],
                'period_rent': mod['new_rent_amount'] * period_months / Decimal('12'),
                'source': f"mod_{mod['id']}"
            })
        
        return timeline
    
    def _create_periods(self, due_dates, end_date, include_future, period_months, rent_timeline):
        periods = []
        for period_number, due_date in enumerate(due_dates, start=1):
            if not include_future and due_date > end_date:
                continue
            
            applicable = rent_timeline[0]
            for segment in rent_timeline:
                if segment['from_date'] <= due_date:
                    if segment['to_date'] is None or segment['to_date'] > due_date:
                        applicable = segment
            
            periods.append({
                'period_number': period_number,
                'start_date': due_date,
                'end_date': self._calc_period_end(due_date, period_months),
                'due_amount': applicable['period_rent'],
                'annual_rent': applicable['annual_rent'],
                'source': applicable['source'],
                'description': f'قسط رقم {period_number} - {self.contract.get_payment_frequency_display()}',
                'is_future': due_date > end_date
            })
        
        logger.info(f'Generated {len(periods)} periods for contract {self.contract.id}')
        return periods
    
    def _calc_period_end(self, start_date, period_months):
        end_date = start_date + relativedelta(months=int(period_months)) - timedelta(days=1)
        return min(end_date, self.contract.end_date)


class ModificationManager:
    """إدارة تعديلات VAT والخصم"""
    
    def __init__(self, contract):
        self.contract = contract
        self._cache = None
    
    def get_modifications_map(self):
        if self._cache is not None:
            return self._cache
        self._cache = self._build_map()
        return self._cache
    
    def _build_map(self):
        from rent.utils.contract_utils import calculate_contract_due_dates
        
        due_dates = calculate_contract_due_dates(self.contract)
        if not due_dates:
            return {}
        
        modifications_map = {}
        
        for vat in self.contract.modifications.filter(modification_type='vat', is_applied=True).order_by('effective_date'):
            for due_date in due_dates:
                if due_date >= vat.effective_date:
                    if due_date not in modifications_map:
                        modifications_map[due_date] = {'vat_amount': Decimal('0'), 'discount_amount': Decimal('0')}
                    modifications_map[due_date]['vat_amount'] = vat.vat_amount
                    break
        
        for discount in self.contract.modifications.filter(modification_type='discount', is_applied=True).order_by('effective_date'):
            for due_date in due_dates:
                if due_date >= discount.effective_date:
                    if due_date not in modifications_map:
                        modifications_map[due_date] = {'vat_amount': Decimal('0'), 'discount_amount': Decimal('0')}
                    modifications_map[due_date]['discount_amount'] = discount.discount_amount
                    break
        
        for mods in modifications_map.values():
            mods['total'] = mods['vat_amount'] - mods['discount_amount']
            mods['has_modifications'] = (mods['vat_amount'] > 0 or mods['discount_amount'] > 0)
        
        return modifications_map
    
    def get_total_modifications_for_period(self, period_start_date):
        mods_map = self.get_modifications_map()
        return mods_map.get(period_start_date, {
            'total': Decimal('0'), 'vat_amount': Decimal('0'),
            'discount_amount': Decimal('0'), 'has_modifications': False
        })
    
    def invalidate_cache(self):
        self._cache = None


class PaymentDistributor:
    """توزيع المدفوعات على الفترات"""
    
    def __init__(self, contract, period_calculator, modification_manager, as_of_date=None):
        self.contract = contract
        self.period_calculator = period_calculator
        self.modification_manager = modification_manager
        self.as_of_date = as_of_date or date.today()
    
    @handle_errors(default_return={'periods': [], 'totals': {}}, log_message="Error distributing payments")
    def calculate_periods_with_payments(self):
        periods = self.period_calculator.calculate_periods_with_modifications()
        total_paid = self._get_total_paid()
        
        remaining_paid = total_paid
        total_due = Decimal('0')
        total_remaining = Decimal('0')
        
        for period in periods:
            base_due = period['due_amount']
            mods = self.modification_manager.get_total_modifications_for_period(period['start_date'])
            
            period['base_rent'] = base_due
            period['modifications'] = mods
            period['due_amount'] = base_due + mods['total']
            total_due += period['due_amount']
            
            if remaining_paid >= period['due_amount']:
                period['paid_amount'] = period['due_amount']
                period['remaining_amount'] = Decimal('0')
                period['status'] = 'paid'
                remaining_paid -= period['due_amount']
            elif remaining_paid > 0:
                period['paid_amount'] = remaining_paid
                period['remaining_amount'] = period['due_amount'] - remaining_paid
                period['status'] = 'partial'
                total_remaining += period['remaining_amount']
                remaining_paid = Decimal('0')
            else:
                period['paid_amount'] = Decimal('0')
                period['remaining_amount'] = period['due_amount']
                total_remaining += period['due_amount']
                
                if period['end_date'] < self.as_of_date:
                    period['status'] = 'overdue'
                elif period['start_date'] <= self.as_of_date <= period['end_date']:
                    period['status'] = 'current'
                else:
                    period['status'] = 'future'
        
        return {
            'periods': periods,
            'totals': {
                'total_due': total_due,
                'total_paid': total_paid,
                'total_remaining': total_remaining
            }
        }
    
    @handle_errors(default_return=Decimal('0'), log_message="Error getting total paid")
    def _get_total_paid(self):
        receipt_filter = {'status': 'posted'}
        if hasattr(self.contract.receipts.model, 'is_deleted'):
            receipt_filter['is_deleted'] = False
        
        return self.contract.receipts.filter(**receipt_filter).aggregate(
            total=Sum('amount'))['total'] or Decimal('0')


class StatementGenerator:
    """إنشاء كشف حساب شامل"""
    
    def __init__(self, contract, period_calculator, as_of_date=None):
        self.contract = contract
        self.period_calculator = period_calculator
        self.as_of_date = as_of_date or date.today()
    
    @handle_errors(default_return={'success': False, 'error': 'Unknown error'}, log_message="Error generating statement")
    def generate_statement(self, end_date=None, include_future=False):
        if not end_date:
            end_date = self.as_of_date
        
        periods = self.period_calculator.calculate_periods_with_modifications(end_date, include_future)
        modifications = self._get_applied_modifications(end_date)
        receipts = self._get_contract_receipts(end_date)
        
        timeline = self._build_timeline(periods, modifications, receipts)
        lines = self._create_statement_lines(timeline)
        summary = self._create_summary(lines, periods, end_date)
        
        return {'success': True, 'lines': lines, 'summary': summary, 'periods': periods}
    
    def _get_applied_modifications(self, end_date):
        return [{'date': m.effective_date, 'modification': m, 'description': m.get_summary()}
                for m in self.contract.modifications.filter(is_applied=True, effective_date__lte=end_date).order_by('effective_date')]
    
    def _get_contract_receipts(self, end_date):
        from rent.models.receipt_models import Receipt
        return [{'date': r.receipt_date, 'amount': r.amount, 
                'description': f'دفعة - {r.get_payment_method_display()}', 'reference': r.receipt_number}
                for r in Receipt.objects.filter(contract=self.contract, status__in=['posted', 'cleared'],
                                               receipt_date__lte=end_date, is_deleted=False).order_by('receipt_date')]
    
    def _build_timeline(self, periods, modifications, receipts):
        timeline = []
        timeline.extend([{'date': p['start_date'], 'type': 'period', 'amount': p['due_amount'],
                         'description': p['description'], 'period_number': p['period_number'], 'sort_priority': 1}
                        for p in periods])
        timeline.extend([{'date': m['date'], 'type': 'modification', 'modification': m['modification'],
                         'description': m['description'], 'sort_priority': 2} for m in modifications])
        timeline.extend([{'date': r['date'], 'type': 'receipt', 'amount': r['amount'],
                         'description': r['description'], 'reference': r.get('reference'), 'sort_priority': 3}
                        for r in receipts])
        timeline.sort(key=lambda x: (x['date'], x['sort_priority']))
        return timeline
    
    def _create_statement_lines(self, timeline):
        lines = []
        balance = Decimal('0.00')
        processed_mods = set()
        
        for item in timeline:
            line, balance = self._process_timeline_item(item, balance, processed_mods)
            if line:
                lines.append(line)
        
        return lines
    
    def _process_timeline_item(self, item, balance, processed_mods):
        if item['type'] == 'period':
            debit = item['amount']
            balance += debit
            return ContractStatementLine(item['date'], 'period', item['description'],
                                        debit, Decimal('0.00'), balance, period_number=item.get('period_number')), balance
        
        elif item['type'] == 'modification':
            mod = item['modification']
            mod_key = f"MOD-{mod.id}"
            if mod_key in processed_mods:
                return None, balance
            
            line = None
            if mod.modification_type in ['rent_increase', 'rent_decrease']:
                icon = '📈' if mod.modification_type == 'rent_increase' else '📉'
                line = ContractStatementLine(item['date'], 'modification', f"{icon} {item['description']}",
                                            Decimal('0.00'), Decimal('0.00'), balance, mod_key)
            elif mod.modification_type == 'discount':
                credit = mod.discount_amount
                balance -= credit
                line = ContractStatementLine(item['date'], 'modification', f"💰 {item['description']}",
                                            Decimal('0.00'), credit, balance, mod_key)
            elif mod.modification_type == 'vat':
                debit = mod.vat_amount
                balance += debit
                line = ContractStatementLine(item['date'], 'modification', f"📊 {item['description']}",
                                            debit, Decimal('0.00'), balance, mod_key)
            elif mod.modification_type in ['extension', 'termination']:
                icon = '📅' if mod.modification_type == 'extension' else '🔴'
                line = ContractStatementLine(item['date'], 'modification', f"{icon} {item['description']}",
                                            Decimal('0.00'), Decimal('0.00'), balance, mod_key)
            
            if line:
                processed_mods.add(mod_key)
            return line, balance
        
        elif item['type'] == 'receipt':
            credit = item['amount']
            balance -= credit
            return ContractStatementLine(item['date'], 'payment', item['description'],
                                        Decimal('0.00'), credit, balance, item.get('reference')), balance
        
        return None, balance
    
    def _create_summary(self, lines, periods, end_date):
        total_debit = sum(l.debit for l in lines)
        total_credit = sum(l.credit for l in lines)
        final_balance = total_debit - total_credit
        
        return {
            'contract_number': getattr(self.contract, 'contract_number', 'غير محدد'),
            'tenant_name': getattr(getattr(self.contract, 'tenant', None), 'name', 'غير محدد'),
            'start_date': self.contract.start_date.isoformat(),
            'end_date': self.contract.end_date.isoformat(),
            'actual_end_date': self.contract.actual_end_date.isoformat() if self.contract.actual_end_date else None,
            'statement_end_date': end_date.isoformat(),
            'total_debit': float(total_debit),
            'total_credit': float(total_credit),
            'final_balance': float(final_balance),
            'is_overdue': final_balance > 0,
            'is_overpaid': final_balance < 0,
            'is_settled': final_balance == 0,
            'total_periods': len([l for l in lines if l.type == 'period']),
            'total_payments': len([l for l in lines if l.type == 'payment']),
            'total_modifications': len([l for l in lines if l.type == 'modification']),
        }


class ModificationValidator:
    """التحقق من صحة التعديلات"""
    
    def __init__(self, contract, period_calculator):
        self.contract = contract
        self.period_calculator = period_calculator
    
    def validate_modification(self, modification_type: str, effective_date: date, **kwargs) -> Tuple[bool, str]:
        validators = [
            self._validate_date_within_contract,
            self._validate_due_date_for_rent_changes,
            self._validate_no_overlap_for_rent_changes,
            self._validate_period_number,
        ]
        
        for validator in validators:
            is_valid, error = validator(modification_type, effective_date, **kwargs)
            if not is_valid:
                return False, error
        
        return True, ''
    
    def _validate_date_within_contract(self, modification_type, effective_date, **kwargs):
        if not (self.contract.start_date <= effective_date <= self.contract.end_date):
            return False, _('تاريخ السريان يجب أن يكون ضمن مدة العقد')
        return True, ''
    
    def _validate_due_date_for_rent_changes(self, modification_type, effective_date, **kwargs):
        if modification_type not in ['rent_increase', 'rent_decrease']:
            return True, ''
        
        from rent.utils.contract_utils import calculate_contract_due_dates
        due_dates = calculate_contract_due_dates(self.contract)
        if effective_date not in due_dates:
            dates_str = ', '.join([d.strftime('%Y-%m-%d') for d in due_dates[:5]])
            return False, _(f'تاريخ السريان يجب أن يكون أحد تواريخ الاستحقاق: {dates_str}')
        return True, ''
    
    def _validate_no_overlap_for_rent_changes(self, modification_type, effective_date, **kwargs):
        if modification_type not in ['rent_increase', 'rent_decrease']:
            return True, ''
        
        overlap = self.contract.modifications.filter(
            modification_type__in=['rent_increase', 'rent_decrease'],
            is_applied=True, effective_date=effective_date
        ).first()
        
        if overlap:
            return False, _(f'يوجد تعديل آخر ({overlap.get_modification_type_display()}) '
                          f'في تاريخ {overlap.effective_date}. لا يمكن وجود أكثر من تعديل إيجار في نفس التاريخ.')
        return True, ''
    
    def _validate_period_number(self, modification_type, effective_date, **kwargs):
        if modification_type not in ['discount', 'vat']:
            return True, ''
        
        period_number = kwargs.get('period_number')
        if not period_number:
            return True, ''
        
        periods = self.period_calculator.calculate_periods_with_modifications()
        if not (1 <= period_number <= len(periods)):
            return False, _(f'رقم الفترة غير صحيح. العقد يحتوي على {len(periods)} فترة فقط.')
        return True, ''


class ContractFinancialService:
    """الخدمة الموحدة للحسابات المالية"""
    
    def __init__(self, contract, as_of_date=None):
        self.contract = contract
        self.as_of_date = as_of_date or date.today()
        
        self._property_context = PropertyContextManager(contract)
        self._period_calculator = PeriodCalculator(contract, as_of_date)
        self._modification_manager = ModificationManager(contract)
        self._payment_distributor = None
        self._statement_generator = None
        self._validator = None
        self._cached_periods_with_payments = None
    
    @property
    def unit(self):
        return self._property_context.unit
    
    @property
    def unit_number(self):
        return self._property_context.unit_number
    
    @property
    def building(self):
        return self._property_context.building
    
    @property
    def building_name(self):
        return self._property_context.building_name
    
    @property
    def location(self):
        return self._property_context.location
    
    @property
    def tenant(self):
        return self._property_context.tenant
    
    @property
    def tenant_name(self):
        return self._property_context.tenant_name
    
    @property
    def tenant_id(self):
        return self._property_context.tenant_id
    
    @property
    def contract_number(self):
        return self._property_context.contract_number
    
    def calculate_periods_with_modifications(self, end_date=None, include_future=False):
        return self._period_calculator.calculate_periods_with_modifications(end_date, include_future)
    
    def get_total_modifications_for_period(self, period_start_date):
        return self._modification_manager.get_total_modifications_for_period(period_start_date)
    
    def calculate_periods_with_payments(self, force_refresh=True):
        if force_refresh or self._cached_periods_with_payments is None:
            distributor = self._get_payment_distributor()
            self._cached_periods_with_payments = distributor.calculate_periods_with_payments()
        return self._cached_periods_with_payments
    
    def generate_statement(self, end_date=None, include_future=False):
        generator = self._get_statement_generator()
        return generator.generate_statement(end_date, include_future)
    
    def validate_modification(self, modification_type: str, effective_date: date, **kwargs) -> Tuple[bool, str]:
        validator = self._get_validator()
        return validator.validate_modification(modification_type, effective_date, **kwargs)
    
    def get_unpaid_periods(self):
        data = self.calculate_periods_with_payments()
        return [p for p in data['periods'] if p.get('remaining_amount', 0) > 0]
    
    def get_due_periods(self):
        data = self.calculate_periods_with_payments()
        return [p for p in data['periods'] if p.get('status') in ['overdue', 'current', 'partial']]
    
    def get_outstanding_amount(self, include_future=False):
        data = self.calculate_periods_with_payments()
        total = Decimal('0')
        for period in data['periods']:
            if period['status'] in ['overdue', 'current', 'partial']:
                total += period['remaining_amount']
            elif include_future and period['status'] == 'future':
                total += period['remaining_amount']
        return total
    
    def get_unpaid_periods_range(self):
        unpaid_periods = self.get_unpaid_periods()
        if not unpaid_periods:
            return None
        
        first = unpaid_periods[0]
        last = unpaid_periods[-1]
        return {
            'start_date': first['start_date'],
            'end_date': last['end_date'],
            'unpaid_periods': unpaid_periods,
            'unpaid_periods_count': len(unpaid_periods),
            'total_unpaid_amount': sum(p['remaining_amount'] for p in unpaid_periods),
            'first_period_number': first['period_number'],
            'last_period_number': last['period_number'],
        }
    
    def get_unpaid_periods_date_range_text(self, date_format='%d/%m/%Y'):
        range_data = self.get_unpaid_periods_range()
        if not range_data:
            return "لا توجد فترات غير مسددة"
        return f"من {range_data['start_date'].strftime(date_format)} إلى {range_data['end_date'].strftime(date_format)}"
    
    def get_tenant_report_data(self):
        data = self.calculate_periods_with_payments()
        summary = self.get_contract_summary()
        due_periods = self.get_due_periods()
        
        due_period_info = ""
        if due_periods:
            first_due = due_periods[0]
            due_period_info = f"من {first_due['start_date']} إلى {first_due['end_date']}"
        
        unpaid_range = self.get_unpaid_periods_range()
        
        report_data = {
            'tenant_id': self.tenant_id,
            'tenant_name': self.tenant_name,
            'location': self.location,
            'unit_number': self.unit_number,
            'building_name': self.building_name,
            'annual_rent': self.contract.annual_rent,
            'outstanding_amount': self.get_outstanding_amount(),
            'due_period': due_period_info,
            'contract_number': self.contract_number,
            'total_overdue': sum(p['remaining_amount'] for p in summary['overdue_periods']),
            'overdue_periods_count': len(summary['overdue_periods']),
        }
        
        if unpaid_range:
            report_data.update({
                'unpaid_range_start': unpaid_range['start_date'],
                'unpaid_range_end': unpaid_range['end_date'],
                'unpaid_range_text': self.get_unpaid_periods_date_range_text(),
                'unpaid_periods_count': unpaid_range['unpaid_periods_count'],
                'total_unpaid_amount': unpaid_range['total_unpaid_amount'],
            })
        else:
            report_data.update({
                'unpaid_range_start': None,
                'unpaid_range_end': None,
                'unpaid_range_text': 'لا توجد فترات غير مسددة',
                'unpaid_periods_count': 0,
                'total_unpaid_amount': Decimal('0'),
            })
        
        return report_data
    
    def get_contract_summary(self):
        data = self.calculate_periods_with_payments()
        periods = data.get('periods', [])
        totals = data.get('totals', {})
        
        summary = {
            'total_periods': len(periods),
            'paid_periods': [],
            'partial_periods': [],
            'overdue_periods': [],
            'current_period': None,
            'future_periods': [],
            'total_contract_value': sum(p['due_amount'] for p in periods),
            'total_paid': totals.get('total_paid', Decimal('0')),
            'total_remaining': totals.get('total_remaining', Decimal('0')),
            'outstanding': self.get_outstanding_amount(),
        }
        
        for period in periods:
            status = period['status']
            if status == 'paid':
                summary['paid_periods'].append(period)
            elif status == 'partial':
                summary['partial_periods'].append(period)
            elif status == 'overdue':
                summary['overdue_periods'].append(period)
            elif status == 'current':
                summary['current_period'] = period
            elif status == 'future':
                summary['future_periods'].append(period)
        
        return summary
    
    def calculate_payment_distribution(self, payment_amount):
        unpaid_periods = self.get_unpaid_periods()
        distribution = []
        remaining_amount = payment_amount
        
        for period in unpaid_periods:
            if remaining_amount <= 0:
                break
            
            allocated = min(remaining_amount, period['remaining_amount'])
            distribution.append({
                'period_number': period['period_number'],
                'start_date': period['start_date'],
                'end_date': period['end_date'],
                'due_amount': period['due_amount'],
                'paid_amount': period['paid_amount'],
                'remaining_before': period['remaining_amount'],
                'allocated_amount': allocated,
                'remaining_after': period['remaining_amount'] - allocated,
                'status': period['status']
            })
            remaining_amount -= allocated
        
        return distribution
    
    def calculate_vat(self, base_amount: Decimal, vat_percentage: Decimal) -> Decimal:
        return (base_amount * vat_percentage) / Decimal('100')
    
    def calculate_extension(self, extension_months: int) -> date:
        return self.contract.end_date + relativedelta(months=extension_months)
    
    def invalidate_cache(self):
        self._cached_periods_with_payments = None
        self._modification_manager.invalidate_cache()
    
    def refresh_data(self):
        self.invalidate_cache()
        self._period_calculator = PeriodCalculator(self.contract, self.as_of_date)
        self._modification_manager = ModificationManager(self.contract)
        self._payment_distributor = None
        self._statement_generator = None
        self._validator = None
    
    def _get_payment_distributor(self):
        if self._payment_distributor is None:
            self._payment_distributor = PaymentDistributor(
                self.contract, self._period_calculator, self._modification_manager, self.as_of_date)
        return self._payment_distributor
    
    def _get_statement_generator(self):
        if self._statement_generator is None:
            self._statement_generator = StatementGenerator(
                self.contract, self._period_calculator, self.as_of_date)
        return self._statement_generator
    
    def _get_validator(self):
        if self._validator is None:
            self._validator = ModificationValidator(self.contract, self._period_calculator)
        return self._validator
    
    def _build_modifications_map(self):
        return self._modification_manager.get_modifications_map()
    
    def _get_total_paid(self):
        distributor = self._get_payment_distributor()
        return distributor._get_total_paid()
    
    def _initialize_property_context(self):
        pass


def generate_contract_statement(contract, end_date=None, include_future=False):
    service = ContractFinancialService(contract)
    return service.generate_statement(end_date, include_future)


def calculate_periods_with_payments(contract, as_of_date=None):
    service = ContractFinancialService(contract, as_of_date)
    return service.calculate_periods_with_payments()


def validate_contract_modification(contract, modification_type: str, effective_date: date, **kwargs):
    service = ContractFinancialService(contract)
    return service.validate_modification(modification_type, effective_date, **kwargs)


def get_contract_periods_with_modifications(contract):
    service = ContractFinancialService(contract)
    return service.calculate_periods_with_modifications()


def generate_tenants_report(contracts):
    return [ContractFinancialService(c).get_tenant_report_data() for c in contracts]


def format_statement_report(statement):
    if not statement.get('success'):
        return f"❌ خطأ: {statement.get('error', 'خطأ غير معروف')}"
    
    summary = statement['summary']
    lines = statement['lines']
    
    report = f"""
╔═══════════════════════════════════════════════════════════════╗
║                    كشف حساب العقد                            ║
╚═══════════════════════════════════════════════════════════════╝

📋 معلومات العقد:
  • رقم العقد: {summary['contract_number']}
  • المستأجر: {summary['tenant_name']}
  • من: {summary['start_date']} إلى: {summary['end_date']}
  • كشف الحساب حتى: {summary['statement_end_date']}

═══════════════════════════════════════════════════════════════

التاريخ          |  البيان                    |    مدين    |   دائن    |   الرصيد
═══════════════════════════════════════════════════════════════
"""
    
    for line in lines:
        date_str = line.date.strftime('%Y-%m-%d') if line.date else '-'
        desc = line.description[:25].ljust(25)
        debit = f"{line.debit:>10,.2f}" if line.debit > 0 else " " * 10
        credit = f"{line.credit:>10,.2f}" if line.credit > 0 else " " * 10
        balance = f"{line.balance:>12,.2f}"
        report += f"{date_str} | {desc} | {debit} | {credit} | {balance}\n"
    
    report += f"""
═══════════════════════════════════════════════════════════════

💰 الملخص المالي:
  • إجمالي المستحق (مدين):  {summary['total_debit']:>12,.2f} ريال
  • إجمالي المدفوع (دائن):   {summary['total_credit']:>12,.2f} ريال
  ────────────────────────────────────────────────────────────
  • الرصيد النهائي:           {summary['final_balance']:>12,.2f} ريال
"""
    
    if summary['is_overdue']:
        report += "\n  ⚠️  مديونية متبقية يجب تحصيلها"
    elif summary['is_overpaid']:
        report += "\n  ℹ️  رصيد زائد للمستأجر"
    else:
        report += "\n  ✅ الحساب متوازن"
    
    report += f"""

📊 الإحصائيات:
  • عدد الفترات: {summary['total_periods']}
  • عدد الدفعات: {summary['total_payments']}
  • عدد التعديلات: {summary['total_modifications']}
"""
    
    return report