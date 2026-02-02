"""
Admin Package
حزمة إدارة Django - تصدير جميع الـ Admin Classes
"""

from django.contrib import admin

# استيراد وتسجيل المستخدمين
from .user_admin import register_user_admin

# استيراد العقارات
from .property_admin import (
    LandAdmin,
    BuildingAdmin,
    UnitAdmin,
)

# استيراد المستأجرين
from .tenant_admin import (
    TenantAdmin,
    TenantDocumentAdmin,
)

# استيراد العقود
from .contract_admin import (
    ContractAdmin,
    ContractModificationAdmin,
)

# استيراد المدفوعات
from .payment_admin import (
    ReceiptAdmin,
)

# استيراد الإشعارات
from .notification_admin import (
    NotificationAdmin,
)

# استيراد النظام
from .system_admin import (
    
    ReportTemplateAdmin,
    
)

# استيراد النسخ الاحتياطي
from .backup_admin import (
    BackupAdmin,
    BackupScheduleAdmin,
)

# استيراد المهام
from .task_admin import (
    ScheduledTaskAdmin,
    TaskExecutionAdmin,
    TaskLogAdmin,
)


# ========================================
# تسجيل المستخدمين
# ========================================

register_user_admin()


# ========================================
# إعدادات لوحة الإدارة
# ========================================

admin.site.site_header = "نظام إدارة الإيجارات"
admin.site.site_title = "نظام الإيجارات"
admin.site.index_title = "مرحباً بك في لوحة إدارة نظام الإيجارات"


# ========================================
# تصدير جميع الـ Admin Classes
# ========================================

__all__ = [
    # User
    'register_user_admin',
    
    # Properties
    'LandAdmin',
    'BuildingAdmin',
    'UnitAdmin',
    
    # Tenants
    'TenantAdmin',
    'TenantDocumentAdmin',
    
    # Contracts
    'ContractAdmin',
    'ContractModificationAdmin',
    
    # Payments
    'ReceiptAdmin',
    
    # Notifications
    'NotificationAdmin',
    
    # System
    
    'ReportTemplateAdmin',
   
    
    # Backup
    'BackupAdmin',
    'BackupScheduleAdmin',
    
    # Tasks
    'ScheduledTaskAdmin',
    'TaskExecutionAdmin',
    'TaskLogAdmin',
]