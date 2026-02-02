# models/common_imports_models.py
"""
ملف الاستيرادات والمكونات المشتركة لنظام إدارة العقارات
Shared imports and components for Real Estate Management System
"""

# ========================================
# Django Core Imports
# ========================================
from django.db import models
from django.db.models import Q, Sum, Count, Avg ,Max
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import (
    MinValueValidator, 
    MaxValueValidator,
    RegexValidator,
    FileExtensionValidator
)
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver



def generate_contract_number() -> int:
    from rent.models import Contract  # import داخلي لتجنب circular import
    last_number = Contract.objects.aggregate(
        max_num=Max('contract_number')
    )['max_num']
    return (last_number or 0) + 1


# ========================================
# Python Standard Library
# ========================================
import uuid
import re
import json
import hashlib
from decimal import Decimal
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from functools import lru_cache
from typing import Optional, Union

# ========================================
# Enums and Choices
# ========================================

class PropertyStatus(models.TextChoices):
    """
    Property status choices
    حالات العقارات
    """
    AVAILABLE = 'available', _('متاح')
    RENTED = 'rented', _('مؤجر')
    MAINTENANCE = 'maintenance', _('قيد الصيانة')
    RESERVED = 'reserved', _('محجوز')

class UnitType(models.TextChoices):
    """
     انواع  الوحدات
    """
    SHOWROOM = 'showroom', _('معرض')
    WORKSHOP = 'workshop', _('ورشه')
    OFIEC = 'ofiec', _('مكتب')
    STATION = 'station', _('محطة محروقات')
    ATM = 'atm', _(' صراف الي سيار')
    HALL = 'hall', _('صاله ')



class ContractStatus(models.TextChoices):
    """
    Contract status choices
    حالات العقود
    """
    DRAFT = 'draft', _('مسودة')
    ACTIVE = 'active', _('نشط')
    EXPIRED = 'expired', _('منتهي')
    TERMINATED = 'terminated', _('ملغي')
    RENEWED = 'renewed', _('مجدد')


class PaymentStatus(models.TextChoices):
    """
    Payment status choices
    حالات الدفع
    """
    PENDING = 'pending', _('معلق')
    PAID = 'paid', _('مدفوع')
    PARTIAL = 'partial', _('دفع جزئي')
    OVERDUE = 'overdue', _('متأخر')
    CANCELLED = 'cancelled', _('ملغي')


class NotificationType(models.TextChoices):
    """
    Notification type choices
    أنواع الإشعارات
    """
    CONTRACT_EXPIRY = 'contract_expiry', _('انتهاء عقد')
    PAYMENT_DUE = 'payment_due', _('موعد دفع')
    PAYMENT_OVERDUE = 'payment_overdue', _('تأخر دفع')
    MAINTENANCE = 'maintenance', _('صيانة')
    GENERAL = 'general', _('عام')


class UserRole(models.TextChoices):
    """
    User role choices
    أدوار المستخدمين
    """
    ADMIN = 'admin', _('مدير')
    MANAGER = 'manager', _('مدير عقارات')
    ACCOUNTANT = 'accountant', _('محاسب')
    VIEWER = 'viewer', _('مشاهد')


class RentType(models.TextChoices):
    """
    Rent type/period choices
    أنواع الإيجار
    """
    MONTHLY = 'monthly', _('شهري')
    QUARTERLY = 'quarterly', _('ربع سنوي')
    SEMI_ANNUAL = 'semi_annual', _('نصف سنوي')
    ANNUAL = 'annual', _('سنوي')


class PaymentMethod(models.TextChoices):
    """
    Payment method choices
    طرق الدفع
    """
    CASH = 'cash', _('نقدي')
    BANK_TRANSFER = 'bank_transfer', _('تحويل بنكي')
    CHECK = 'check', _('شيك')
    ONLINE = 'online', _('دفع إلكتروني')


# ========================================
# Utility Functions - Number Generators
# ========================================

def generate_contract_number() -> int:
    from rent.models.contract_models import Contract
    last = Contract.objects.aggregate(max_num=Max('contract_number'))['max_num']
    return (last or 0) + 1


def generate_receipt_number() -> int:
    from rent.models.receipt_models import Receipt
    last = Receipt.objects.aggregate(max_num=Max('receipt_number'))['max_num']
    return (last or 0) + 1


def generate_tenant_code() -> str:
    
    unique_id = uuid.uuid4().hex[:8].upper()
    return f"TEN-{unique_id}"


def generate_unit_code(building_code: Optional[str] = None) -> str:
    
    if building_code:
        unique_id = uuid.uuid4().hex[:4].upper()
        return f"{building_code}-U{unique_id}"
    return f"UNIT-{uuid.uuid4().hex[:6].upper()}"


# ========================================
# Utility Functions - Date Calculations
# ========================================

def calculate_contract_end_date(
    start_date: Union[date, datetime],
    rent_type: str,
    duration_months: Optional[int] = None
) -> date:
    """
    Calculate contract end date based on rent type
    حساب تاريخ نهاية العقد بناءً على نوع الإيجار
    
    Args:
        start_date: Contract start date
        rent_type: Type of rent (monthly, quarterly, etc.)
        duration_months: Custom duration in months (overrides rent_type)
        
    Returns:
        date: Contract end date
        
    Example:
        >>> from datetime import date
        >>> calculate_contract_end_date(date(2024, 1, 1), RentType.ANNUAL)
        datetime.date(2025, 1, 1)
    """
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    
    if duration_months:
        return start_date + relativedelta(months=duration_months)
    
    duration_map = {
        RentType.MONTHLY: 1,
        RentType.QUARTERLY: 3,
        RentType.SEMI_ANNUAL: 6,
        RentType.ANNUAL: 12,
    }
    months = duration_map.get(rent_type, 12)
    return start_date + relativedelta(months=months)


def calculate_payment_due_date(
    start_date: Union[date, datetime],
    payment_day: Optional[int] = None
) -> date:
    """
    Calculate next payment due date
    حساب موعد الدفع التالي
    
    Args:
        start_date: Starting date
        payment_day: Day of month for payment (1-28)
        
    Returns:
        date: Next payment due date
        
    Example:
        >>> from datetime import date
        >>> calculate_payment_due_date(date(2024, 1, 15), payment_day=5)
        datetime.date(2024, 2, 5)
    """
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    
    if payment_day:
        next_month = start_date + relativedelta(months=1)
        # Ensure payment_day is valid (1-28 to avoid month-end issues)
        safe_day = min(payment_day, 28)
        return next_month.replace(day=safe_day)
    
    return start_date + relativedelta(months=1)


def calculate_days_between(
    start_date: Union[date, datetime],
    end_date: Union[date, datetime]
) -> int:
    """
    Calculate number of days between two dates
    حساب عدد الأيام بين تاريخين
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        int: Number of days
        
    Example:
        >>> from datetime import date
        >>> calculate_days_between(date(2024, 1, 1), date(2024, 1, 10))
        9
    """
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    return (end_date - start_date).days


def is_overdue(
    due_date: Union[date, datetime],
    grace_days: int = 0
) -> bool:
    """
    Check if payment is overdue
    التحقق من تأخر الدفع
    
    Args:
        due_date: Payment due date
        grace_days: Grace period in days
        
    Returns:
        bool: True if overdue
        
    Example:
        >>> from datetime import date
        >>> is_overdue(date(2024, 1, 1), grace_days=3)
        True  # if today > 2024-01-04
    """
    if isinstance(due_date, datetime):
        due_date = due_date.date()
    grace_date = due_date + timedelta(days=grace_days)
    return timezone.now().date() > grace_date


# ========================================
# Utility Functions - Formatting
# ========================================

def format_currency(amount: Union[Decimal, float, int]) -> str:
    """
    Format amount as currency (Saudi Riyal)
    تنسيق المبلغ كعملة سعودية
    
    Args:
        amount: Amount to format
        
    Returns:
        str: Formatted currency string
        
    Example:
        >>> format_currency(1234.56)
        '1,234.56 ريال'
    """
    return f"{float(amount):,.2f} ريال"


# ========================================
# Validators
# ========================================

def validate_phone_number(value: str) -> None:
    """
    Validate Saudi phone number
    التحقق من صحة رقم الهاتف السعودي
    
    Args:
        value: Phone number to validate
        
    Raises:
        ValidationError: If phone number is invalid
        
    Valid formats:
        - 0512345678 (10 digits starting with 05)
        - 05 1234 5678 (with spaces)
        - 05-1234-5678 (with dashes)
    """
    # إزالة المسافات والرموز
    clean_value = re.sub(r'[\s\-\+\(\)]', '', str(value))
    
    # يجب أن يبدأ بـ 05 ويكون 10 أرقام بالضبط
    pattern = r'^05\d{8}$'
    if not re.match(pattern, clean_value):
        raise ValidationError(
            _('رقم الهاتف يجب أن يبدأ بـ 05 ويتكون من 10 أرقام (مثال: 0512345678)')
        )


def validate_national_id(value: str) -> None:
    """
    Validate Saudi National ID / Iqama number
    التحقق من صحة رقم الهوية الوطنية / الإقامة
    
    Args:
        value: National ID to validate
        
    Raises:
        ValidationError: If ID is invalid
        
    Rules:
        - Must be exactly 10 digits
        - National ID starts with 1
        - Iqama starts with 2
    """
    clean_value = str(value).strip()
    
    if not clean_value.isdigit() or len(clean_value) != 10:
        raise ValidationError(
            _('رقم الهوية/الإقامة يجب أن يتكون من 10 أرقام بالضبط')
        )
    
    # التحقق من أن الرقم يبدأ بـ 1 أو 2
    if not clean_value.startswith(('1', '2','7')):
        raise ValidationError(
            _('رقم الهوية يجب أن يبدأ بـ 1 (سعودي) أو 2 (مقيم)')
        )


def validate_positive_decimal(value: Union[Decimal, float, int]) -> None:
    """
    Validate that value is positive
    التحقق من أن القيمة موجبة
    
    Args:
        value: Value to validate
        
    Raises:
        ValidationError: If value is negative
    """
    if Decimal(str(value)) < 0:
        raise ValidationError(_('القيمة يجب أن تكون موجبة (أكبر من أو تساوي صفر)'))


def validate_percentage(value: Union[Decimal, float, int]) -> None:
    """
    Validate percentage value (0-100)
    التحقق من أن القيمة نسبة صحيحة
    
    Args:
        value: Percentage value to validate
        
    Raises:
        ValidationError: If value is not between 0 and 100
    """
    decimal_value = Decimal(str(value))
    if not (0 <= decimal_value <= 100):
        raise ValidationError(_('النسبة يجب أن تكون بين 0 و 100'))


def validate_future_date(value: Union[date, datetime]) -> None:
    """
    Validate that date is in the future
    التحقق من أن التاريخ في المستقبل
    
    Args:
        value: Date to validate
        
    Raises:
        ValidationError: If date is in the past
    """
    if isinstance(value, datetime):
        value = value.date()
    
    if value < timezone.now().date():
        raise ValidationError(_('التاريخ يجب أن يكون في المستقبل'))


def validate_past_date(value: Union[date, datetime]) -> None:
    """
    Validate that date is in the past
    التحقق من أن التاريخ في الماضي
    
    Args:
        value: Date to validate
        
    Raises:
        ValidationError: If date is in the future
    """
    if isinstance(value, datetime):
        value = value.date()
    
    if value > timezone.now().date():
        raise ValidationError(_('التاريخ يجب أن يكون في الماضي أو اليوم'))


# ========================================
# Base Abstract Models
# ========================================

class TimeStampedModel(models.Model):
    """
    Abstract model with creation and modification timestamps
    نموذج أساسي يحتوي على تواريخ الإنشاء والتعديل
    
    Fields:
        created_at: Auto-set on creation
        updated_at: Auto-updated on save
    """
    created_at = models.DateTimeField(
        _('تاريخ الإنشاء'),
        auto_now_add=True,
        help_text=_('تاريخ إنشاء السجل تلقائياً')
    )
    updated_at = models.DateTimeField(
        _('تاريخ التعديل'),
        auto_now=True,
        help_text=_('تاريخ آخر تعديل تلقائياً')
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class UserTrackingModel(models.Model):
    """
    Abstract model that tracks creating and updating users
    نموذج أساسي يتتبع المستخدم المنشئ والمعدل
    
    Fields:
        created_by: User who created the record
        updated_by: User who last updated the record
    """
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name=_('أنشئ بواسطة'),
        help_text=_('المستخدم الذي أنشأ السجل')
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name=_('عُدل بواسطة'),
        help_text=_('المستخدم الذي عدّل السجل آخر مرة')
    )
    
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract model for soft deletion
    نموذج أساسي للحذف الناعم
    
    Instead of deleting records, marks them as deleted
    بدلاً من حذف السجلات، يتم وضع علامة عليها كمحذوفة
    
    Fields:
        is_deleted: Deletion flag
        deleted_at: Deletion timestamp
        deleted_by: User who deleted the record
    """
    is_deleted = models.BooleanField(
        _('محذوف'),
        default=False,
        db_index=True,
        help_text=_('هل السجل محذوف (حذف ناعم)')
    )
    deleted_at = models.DateTimeField(
        _('تاريخ الحذف'),
        null=True,
        blank=True,
        help_text=_('تاريخ حذف السجل')
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted',
        verbose_name=_('حذف بواسطة'),
        help_text=_('المستخدم الذي حذف السجل')
    )
    
    class Meta:
        abstract = True
    
    def soft_delete(self, user: Optional[User] = None) -> None:
        """
        Soft delete the record
        حذف ناعم للسجل
        
        Args:
            user: User performing the deletion
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def restore(self) -> None:
        """
        Restore soft-deleted record
        استعادة السجل المحذوف
        """
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


# ========================================
# Export All
# ========================================

__all__ = [
    # Django Core
    'models',
    'User',
    '_',
    'timezone',
    'ValidationError',
    'PermissionDenied',
    
    # Validators
    'MinValueValidator',
    'MaxValueValidator',
    'RegexValidator',
    'FileExtensionValidator',
    
    # Signals
    'post_save',
    'pre_save',
    'post_delete',
    'receiver',
    
    # Python Types
    'Decimal',
    'date',
    'timedelta',
    'datetime',
    'relativedelta',
    'uuid',
    'json',
    'Optional',
    'Union',
    
    # Choices/Enums
    'PropertyStatus',
    'ContractStatus',
    'PaymentStatus',
    'NotificationType',
    'UserRole',
    'RentType',
    'PaymentMethod',
    
    # Utility Functions - Generators
    'generate_contract_number',
    'generate_receipt_number',
    'generate_tenant_code',
    'generate_unit_code',
    
    # Utility Functions - Dates
    'calculate_contract_end_date',
    'calculate_payment_due_date',
    'calculate_days_between',
    'is_overdue',
    
    # Utility Functions - Formatting
    'format_currency',
    
    # Custom Validators
    'validate_phone_number',
    'validate_national_id',
    'validate_positive_decimal',
    'validate_percentage',
    'validate_future_date',
    'validate_past_date',
    
    # Abstract Base Models
    'TimeStampedModel',
    'UserTrackingModel',
    'SoftDeleteModel',
]