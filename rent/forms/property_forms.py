"""
Property Forms
نماذج العقارات (الأراضي، المباني، الوحدات)
"""

from .common_imports_forms import (
    forms, _, timezone,
    Land, Building, Unit,
    PropertyStatus,
    COMMON_WIDGETS, BaseModelForm
)


# ========================================
# Land Form
# ========================================

class LandForm(BaseModelForm):
    """نموذج الأرض"""
    
    class Meta:
        model = Land
        fields = [
            'name', 'deed_number', 'area',
            'owner_name', 'ownership_type',
            'rent_start_date', 'rent_duration_years', 'annual_rent_amount',
            'is_active', 'notes'
        ]
        widgets = {
            'name': COMMON_WIDGETS['text_input']('اسم الأرض'),
            'deed_number': COMMON_WIDGETS['text_input']('رقم الصك'),
            'area': COMMON_WIDGETS['number_input']('المساحة بالمتر مربع'),
            'owner_name': COMMON_WIDGETS['text_input']('اسم المالك'),
            'ownership_type': COMMON_WIDGETS['select'](),
            'rent_start_date': COMMON_WIDGETS['date_input'](),
            'rent_duration_years': COMMON_WIDGETS['number_input']('مدة الإيجار بالسنوات', step='1', min='1'),
            'annual_rent_amount': COMMON_WIDGETS['number_input']('الإيجار السنوي'),
            'is_active': COMMON_WIDGETS['checkbox'](),
            'notes': COMMON_WIDGETS['textarea'](placeholder='ملاحظات'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].required = False
        self.fields['annual_rent_amount'].required = False


# ========================================
# Building Form
# ========================================

class BuildingForm(BaseModelForm):
    """نموذج المبنى"""
    
    class Meta:
        model = Building
        fields = [
            'land', 'name', 'building_type',
            'total_area', 'floors_count', 'construction_year',
            'has_elevator', 'has_parking', 'parking_spaces',
            'is_active', 'notes'
        ]
        widgets = {
            'land': COMMON_WIDGETS['select'](),
            'name': COMMON_WIDGETS['text_input']('اسم المبنى'),
            'building_type': COMMON_WIDGETS['select'](),
            'total_area': COMMON_WIDGETS['number_input'](),
            'floors_count': COMMON_WIDGETS['number_input'](step='1', min='1'),
            'construction_year': COMMON_WIDGETS['number_input'](step='1', min='1990'),
            'has_elevator': COMMON_WIDGETS['checkbox'](),
            'has_parking': COMMON_WIDGETS['checkbox'](),
            'parking_spaces': COMMON_WIDGETS['number_input'](step='1', min='0'),
            'is_active': COMMON_WIDGETS['checkbox'](),
            'notes': COMMON_WIDGETS['textarea'](),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['construction_year'].initial = timezone.now().year
        self.fields['has_elevator'].initial = False
        self.fields['has_parking'].initial = False


# ========================================
# Unit Form
# ========================================

class UnitForm(BaseModelForm):
    """نموذج الوحدة"""
    
    class Meta:
        model = Unit
        fields = [
            'building', 'unit_type', 'unit_number', 'floor',
            'area', 'rooms_count', 'bathrooms_count',
            'has_kitchen', 'has_balcony',
            'water_meter_number', 'electricity_meter_number',
            'monthly_rent', 'security_deposit',
            'status', 'is_active', 'notes'
        ]
        widgets = {
            'building': COMMON_WIDGETS['select'](),
            'unit_number': COMMON_WIDGETS['text_input']('رقم الوحدة'),
            'unit_type': COMMON_WIDGETS['select'](),
            'floor': COMMON_WIDGETS['number_input'](step='1'),
            'area': COMMON_WIDGETS['number_input'](),
            'rooms_count': COMMON_WIDGETS['number_input'](step='1', min='0'),
            'bathrooms_count': COMMON_WIDGETS['number_input'](step='1', min='0'),
            'has_kitchen': COMMON_WIDGETS['checkbox'](),
            'has_balcony': COMMON_WIDGETS['checkbox'](),
            'water_meter_number': COMMON_WIDGETS['text_input'](),
            'electricity_meter_number': COMMON_WIDGETS['text_input'](),
            'monthly_rent': COMMON_WIDGETS['number_input'](),
            'security_deposit': COMMON_WIDGETS['number_input'](),
            'status': COMMON_WIDGETS['select'](),
            'is_active': COMMON_WIDGETS['checkbox'](),
            'notes': COMMON_WIDGETS['textarea'](),
        }