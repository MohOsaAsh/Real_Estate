# models/__init__.py

"""
نظام إدارة العقارات - نماذج البيانات
Real Estate Management System - Data Models

هذا الملف يقوم بتجميع كل النماذج وجعلها متاحة للاستيراد من مجلد models
This file aggregates all models and makes them available for import from models package

الاستخدام / Usage:
    from models import Contract, Tenant, Building
    from models import PropertyStatus, generate_contract_number
"""

# ========================================
# 1. استيراد المكونات المشتركة
#    Import Shared Components
# ========================================
from .common_imports_models import (
    # Django Core
    models,
    User,
    timezone,
    ValidationError,
    PermissionDenied,
    
    # Validators
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
    
    # Python Types
    Decimal,
    date,
    datetime,
    timedelta,
    
    # Choices/Enums
    PropertyStatus,
    ContractStatus,
    PaymentStatus,
    NotificationType,
    UserRole,
    RentType,
    PaymentMethod,
    UnitType,
    
    
    # Utility Functions - Generators
    generate_contract_number,
    generate_receipt_number,
    generate_tenant_code,
    generate_unit_code,
    
    # Utility Functions - Calculations
    calculate_contract_end_date,
    calculate_payment_due_date,
    calculate_days_between,
    is_overdue,
    format_currency,
    
    # Custom Validators
    validate_phone_number,
    validate_national_id,
    validate_positive_decimal,
    validate_percentage,
    validate_future_date,
    validate_past_date,
    
    # Abstract Models
    TimeStampedModel,
    UserTrackingModel,
    SoftDeleteModel,
)

# ========================================
# 2. استيراد النماذج بالترتيب الصحيح
#    Import Models in Correct Order
# ========================================

# ----------------------------------------
# User Models (لا تعتمد على نماذج أخرى)
# No dependencies on other models
# ----------------------------------------
from .user_models import UserProfile

# ----------------------------------------
# Property Models (ترتيب هرمي)
# Hierarchical order: Land → Building → Unit
# ----------------------------------------
from .land_models import Land
from .building_models import Building
from .unit_models import Unit

# ----------------------------------------
# Tenant Models (لا تعتمد على نماذج أخرى)
# No dependencies on other models
# ----------------------------------------
from .tenant_models import (
    Tenant,
    TenantDocument
)

# ----------------------------------------
# Contract Models (تعتمد على Unit و Tenant)
# Depend on Unit and Tenant
# ----------------------------------------
from .contract_models import Contract
from .contractmodify_models import ContractModification


# ----------------------------------------
# Financial Models (تعتمد على Contract)
# Depend on Contract
# ----------------------------------------
from .receipt_models import Receipt

# ----------------------------------------
# System Models
# ----------------------------------------
from .notification_models import Notification
from .report_models import ReportTemplate


# ----------------------------------------
# Scheduled Task Models
# ----------------------------------------
from .scheduledtask_models import (
    ScheduledTask,
    TaskLog,
    TaskExecution
)

# ----------------------------------------
# Backup Models
# ----------------------------------------
from .backup_models import (
    Backup,
    BackupSchedule,
   # BackupLog
)

# ========================================
# 3. تحديد ما يتم تصديره بشكل صريح
#    Explicit exports via __all__
# ========================================
__all__ = [
    # ============================================
    # User Models
    # ============================================
    'UserProfile',
    
    # ============================================
    # Property Models
    # ============================================
    'Land',
    'Building',
    'Unit',
    
    # ============================================
    # Tenant Models
    # ============================================
    'Tenant',
    'TenantDocument',
    
    # ============================================
    # Contract Models
    # ============================================
    'Contract',
    'ContractModification',
    'ContractCalculator',
    
    # ============================================
    # Financial Models
    # ============================================
    'Receipt',
    
    # ============================================
    # System Models
    # ============================================
    'Notification',
    'ReportTemplate',
    #'SystemSetting',
    
    # ============================================
    # Scheduled Task Models
    # ============================================
    'ScheduledTask',
    'TaskLog',
    'TaskExecution',
    
    # ============================================
    # Backup Models
    # ============================================
    'Backup',
    'BackupSchedule',
    #'BackupLog',
    
    # ============================================
    # Enums/Choices (للاستخدام في النماذج والعروض)
    # For use in forms and views
    # ============================================
    'PropertyStatus',
    'ContractStatus',
    'PaymentStatus',
    'NotificationType',
    'UserRole',
    'RentType',
    'PaymentMethod',
    
    # ============================================
    # Utility Functions (اختياري للتصدير)
    # Optional utility exports
    # ============================================
    'generate_contract_number',
    'generate_receipt_number',
    'generate_tenant_code',
    'generate_unit_code',
    'calculate_contract_end_date',
    'calculate_payment_due_date',
    'calculate_days_between',
    'is_overdue',
    'format_currency',
    
    # ============================================
    # Validators (للاستخدام في النماذج)
    # For use in forms
    # ============================================
    'validate_phone_number',
    'validate_national_id',
    'validate_positive_decimal',
    'validate_percentage',
    'validate_future_date',
    'validate_past_date',
    
    # ============================================
    # Abstract Models (للوراثة)
    # For inheritance
    # ============================================
    'TimeStampedModel',
    'UserTrackingModel',
    'SoftDeleteModel',
    
    # ============================================
    # Django Core (للاستخدام الخارجي)
    # For external use
    # ============================================
    'models',
    'User',
    'timezone',
    'ValidationError',
]


# ========================================
# 4. معلومات إضافية عن الحزمة
#    Package Metadata
# ========================================
__version__ = '1.0.0'
__author__ = 'Real Estate Management Team'
__description__ = 'نماذج نظام إدارة العقارات - Real Estate Management Models'


# ========================================
# 5. ملاحظات مهمة للمطورين
#    Important Notes for Developers
# ========================================
"""
ترتيب الاستيراد مهم جداً:
Import order is critical:

1. المكونات المشتركة (common_imports_models)
2. UserProfile (مستقل)
3. Land (مستقل)
4. Building (يعتمد على Land)
5. Unit (يعتمد على Building)
6. Tenant (مستقل)
7. Contract (يعتمد على Unit و Tenant)
8. باقي النماذج التي تعتمد على Contract

عند إضافة نموذج جديد:
When adding new model:
- تأكد من استيراده في المكان الصحيح حسب اعتمادياته
- أضفه إلى __all__
- حدّث هذا التعليق إذا لزم الأمر

تجنب:
Avoid:
- استيراد * من أي ملف (استخدم استيراد صريح)
- الاستيرادات الدائرية
- تغيير ترتيب الاستيراد دون فهم الاعتماديات
"""