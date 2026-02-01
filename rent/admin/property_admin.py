"""
Property Admin
إدارة العقارات (الأراضي، المباني، الوحدات)
"""

from .common_imports_admin import (
    admin, format_html, reverse,
    Land, Building, Unit,
    BaseModelAdmin, BaseTabularInline,
    create_model_link, format_percentage,
    SYSTEM_INFO_FIELDSET, NOTES_FIELDSET, STATUS_FIELDSET,
)


# ========================================
# Land Admin
# ========================================

class BuildingInline(BaseTabularInline):
    """Inline للمباني في صفحة الأرض"""
    model = Building
    fields = ('name', 'building_type', 'total_area', 'floors_count', 'is_active')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Land)
class LandAdmin(BaseModelAdmin):
    """إدارة الأراضي"""
    
    list_display = (
        'name', 'deed_number', 'owner_name', 'ownership_type', 
        'area', 'is_active', 'created_at'
    )
    
    list_filter = ('ownership_type', 'is_active', 'created_at')
    
    search_fields = ('name', 'deed_number', 'owner_name', 'city', 'district')
    
    readonly_fields = ('rent_end_date',)
    
    fieldsets = (
        ('معلومات الأرض', {
            'fields': (
                'name', 'deed_number', 'area', 
                'owner_name', 'ownership_type'
            )
        }),
        ('تفاصيل الإيجار', {
            'fields': (
                'rent_start_date', 'rent_duration_years', 
                'rent_end_date', 'annual_rent_amount'
            ),
            'classes': ('collapse',)
        }),
        STATUS_FIELDSET(),
        NOTES_FIELDSET,
        SYSTEM_INFO_FIELDSET,
    )
    
    inlines = [BuildingInline]


# ========================================
# Building Admin
# ========================================

class UnitInline(BaseTabularInline):
    """Inline للوحدات في صفحة المبنى"""
    model = Unit
    fields = ('unit_number', 'floor', 'area', 'rooms_count', 'status', 'is_active')
    readonly_fields = ('created_at',)


@admin.register(Building)
class BuildingAdmin(BaseModelAdmin):
    """إدارة المباني"""
    
    list_display = (
        'name', 'land', 'building_type', 'total_area', 
        'floors_count', 'occupancy_rate', 'is_active'
    )
    
    list_filter = (
        'building_type', 'is_active', 
        'has_elevator', 'has_parking', 'land'
    )
    
    search_fields = ('name', 'land__name')
    
    fieldsets = (
        ('معلومات المبنى', {
            'fields': (
                'land', 'name', 'building_type', 
                'total_area', 'floors_count', 'construction_year'
            )
        }),
        ('المرافق', {
            'fields': ('has_elevator', 'has_parking', 'parking_spaces'),
            'classes': ('collapse',)
        }),
        STATUS_FIELDSET(),
        NOTES_FIELDSET,
        SYSTEM_INFO_FIELDSET,
    )
    
    inlines = [UnitInline]
    
    def occupancy_rate(self, obj):
        """عرض نسبة الإشغال"""
        rate = obj.get_occupancy_rate()
        return format_percentage(rate)
    occupancy_rate.short_description = 'نسبة الإشغال'


# ========================================
# Unit Admin
# ========================================

@admin.register(Unit)
class UnitAdmin(BaseModelAdmin):
    """إدارة الوحدات"""
    
    list_display = (
        'unit_number', 'building', 'floor', 'area', 
        'rooms_count', 'status', 'current_contract', 'is_active'
    )
    
    list_filter = (
        'status', 'is_active', 'building', 'floor', 'rooms_count'
    )
    
    search_fields = (
        'unit_number', 'building__name', 
        'water_meter_number', 'electricity_meter_number'
    )
    
    fieldsets = (
        ('معلومات الوحدة', {
            'fields': (
                'building', 'unit_number', 'floor', 
                'area', 'rooms_count', 'bathrooms_count'
            )
        }),
        ('المرافق', {
            'fields': (
                'has_kitchen', 'has_balcony', 
                'water_meter_number', 'electricity_meter_number'
            ),
            'classes': ('collapse',)
        }),
        ('المالية', {
            'fields': ('monthly_rent', 'security_deposit'),
            'classes': ('collapse',)
        }),
        ('الحالة', {
            'fields': ('status', 'is_active', 'notes')
        }),
        SYSTEM_INFO_FIELDSET,
    )
    
    def current_contract(self, obj):
        """عرض رابط العقد الحالي"""
        contract = obj.get_current_contract()
        if contract:
            return create_model_link('contract', contract.id, contract.contract_number)
        return "-"
    current_contract.short_description = 'العقد الحالي'