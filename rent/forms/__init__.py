"""
Forms Package
حزمة النماذج - تصدير جميع النماذج
"""

# استيراد من الملفات الفرعية
from .user_forms import (
    UserProfileForm,
)

from .property_forms import (
    LandForm,
    BuildingForm,
    UnitForm,
)

from .tenant_forms import (
    TenantForm,
    TenantDocumentForm,
)

from .contract_forms import (
    ContractForm,
)

# استيراد نماذج تعديلات العقود (إذا كان الملف موجود)
try:
    from .contract_modification_forms import (
        BaseContractModificationForm,
        ExtensionForm,
        RentIncreaseForm,
        RentDecreaseForm,
        DiscountForm,
        VATForm,
        TerminationForm,
        ContractModificationAdminForm,
    )
    HAS_CONTRACT_MODIFICATION_FORMS = True
except ImportError:
    HAS_CONTRACT_MODIFICATION_FORMS = False

from .payment_forms import (
    ReceiptForm,
)

from .search_forms import (
    TenantSearchForm,
    ContractSearchForm,
    UnitSearchForm,
)

from .report_forms import (
    ReportFilterForm,
   
)


# تصدير جميع النماذج
__all__ = [
    # User Forms
    'UserProfileForm',
    
    # Property Forms
    'LandForm',
    'BuildingForm',
    'UnitForm',
    
    # Tenant Forms
    'TenantForm',
    'TenantDocumentForm',
    
    # Contract Forms
    'ContractForm',
    
    # Payment Forms
    'ReceiptForm',
    
    # Search Forms
    'TenantSearchForm',
    'ContractSearchForm',
    'UnitSearchForm',
    
    # Report & System Forms
    'ReportFilterForm',
   
]

# إضافة نماذج تعديلات العقود إذا كانت متاحة
if HAS_CONTRACT_MODIFICATION_FORMS:
    __all__.extend([
        'BaseContractModificationForm',
        'ExtensionForm',
        'RentIncreaseForm',
        'RentDecreaseForm',
        'DiscountForm',
        'VATForm',
        'TerminationForm',
        'ContractModificationAdminForm',
    ])
    
    # ========================================
    # Backward Compatibility Alias
    # للتوافق مع الكود القديم
    # ========================================
    ContractModificationForm = ContractModificationAdminForm
    __all__.append('ContractModificationForm')