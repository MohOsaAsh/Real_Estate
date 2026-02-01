# services/unit_availability_service.py

from django.db.models import Q, Exists, OuterRef
from typing import List, Dict, Optional


class UnitAvailabilityService:
    """
    خدمة لتحديث حالة الوحدات بناءً على العقود الساريه
    يدعم علاقة ManyToMany بين العقود والوحدات
    """
    
    def __init__(
        self,
        contract_model,
        unit_model,
        active_status_value: str,
        available_status_value: str,
        rented_status_value: str
    ):
        """
        Parameters:
        -----------
        contract_model : Model
            نموذج العقود (Contract)
        unit_model : Model
            نموذج الوحدات (Unit)
        active_status_value : str
            القيمة التي تعني أن العقد ساري (مثل: 'ACTIVE')
        available_status_value : str
            القيمة التي تعني أن الوحدة متاحة (مثل: 'AVAILABLE')
        rented_status_value : str
            القيمة التي تعني أن الوحدة مؤجرة (مثل: 'RENTED')
        """
        self.contract_model = contract_model
        self.unit_model = unit_model
        self.active_status_value = active_status_value
        self.available_status_value = available_status_value
        self.rented_status_value = rented_status_value
    
    def update_all_units_availability(self) -> Dict[str, int]:
        """
        تحديث حالة جميع الوحدات بناءً على العقود الساريه
        
        Returns:
        --------
        dict: إحصائيات العملية
        """
        # الحصول على الوحدات التي لها عقود ساريه
        active_contracts = self.contract_model.objects.filter(
            status=self.active_status_value
        ).prefetch_related('units')
        
        # جمع IDs الوحدات من جميع العقود الساريه
        units_with_active_contracts = set()
        for contract in active_contracts:
            units_with_active_contracts.update(
                contract.units.values_list('id', flat=True)
            )
        
        # تحديث الوحدات إلى حالة "مؤجرة" (لها عقود ساريه)
        rented_count = self.unit_model.objects.filter(
            id__in=units_with_active_contracts
        ).update(status=self.rented_status_value)
        
        # تحديث الوحدات إلى حالة "متاحة" (ليس لها عقود ساريه)
        available_count = self.unit_model.objects.exclude(
            id__in=units_with_active_contracts
        ).update(status=self.available_status_value)
        
        return {
            'rented_units': rented_count,
            'available_units': available_count,
            'total_processed': rented_count + available_count,
            'units_with_active_contracts': len(units_with_active_contracts)
        }
    
    def update_units_by_contract(self, contract_id: int) -> Dict[str, any]:
        """
        تحديث حالة الوحدات المرتبطة بعقد معين
        
        Parameters:
        -----------
        contract_id : int
            معرف العقد
            
        Returns:
        --------
        dict: معلومات العملية
        """
        try:
            contract = self.contract_model.objects.get(id=contract_id)
        except self.contract_model.DoesNotExist:
            return {
                'success': False,
                'message': 'العقد غير موجود',
                'updated_units': 0
            }
        
        units = contract.units.all()
        
        # تحديد الحالة الجديدة بناءً على حالة العقد
        new_status = (
            self.rented_status_value 
            if contract.status == self.active_status_value 
            else self.available_status_value
        )
        
        # تحديث الوحدات
        updated_count = units.update(status=new_status)
        
        return {
            'success': True,
            'contract_status': contract.status,
            'new_units_status': new_status,
            'updated_units': updated_count,
            'unit_ids': list(units.values_list('id', flat=True))
        }
    
    def update_specific_unit(self, unit_id: int) -> Dict[str, any]:
        """
        تحديث حالة وحدة معينة بناءً على عقودها
        
        Parameters:
        -----------
        unit_id : int
            معرف الوحدة
            
        Returns:
        --------
        dict: معلومات الوحدة بعد التحديث
        """
        try:
            unit = self.unit_model.objects.get(id=unit_id)
        except self.unit_model.DoesNotExist:
            return {
                'success': False,
                'message': 'الوحدة غير موجودة'
            }
        
        # التحقق من وجود عقود ساريه للوحدة
        has_active_contract = self.contract_model.objects.filter(
            units=unit,
            status=self.active_status_value
        ).exists()
        
        # تحديد الحالة الجديدة
        new_status = (
            self.rented_status_value 
            if has_active_contract 
            else self.available_status_value
        )
        
        # تحديث الوحدة
        unit.status = new_status
        unit.save(update_fields=['status'])
        
        return {
            'success': True,
            'unit_id': unit.id,
            'old_status': unit.status,
            'new_status': new_status,
            'has_active_contract': has_active_contract
        }
    
    def get_units_statistics(self) -> Dict[str, any]:
        """
        الحصول على إحصائيات الوحدات
        
        Returns:
        --------
        dict: إحصائيات مفصلة
        """
        total_units = self.unit_model.objects.count()
        available_units = self.unit_model.objects.filter(
            status=self.available_status_value
        ).count()
        rented_units = self.unit_model.objects.filter(
            status=self.rented_status_value
        ).count()
        
        active_contracts_count = self.contract_model.objects.filter(
            status=self.active_status_value
        ).count()
        
        return {
            'total_units': total_units,
            'available_units': available_units,
            'rented_units': rented_units,
            'other_status_units': total_units - available_units - rented_units,
            'active_contracts': active_contracts_count
        }
    
    def get_available_units(self):
        """الحصول على جميع الوحدات المتاحة"""
        return self.unit_model.objects.filter(
            status=self.available_status_value
        )
    
    def get_rented_units(self):
        """الحصول على جميع الوحدات المؤجرة"""
        return self.unit_model.objects.filter(
            status=self.rented_status_value
        )
    
    def get_units_with_active_contracts(self):
        """الحصول على الوحدات التي لها عقود ساريه"""
        return self.unit_model.objects.filter(
            contracts__status=self.active_status_value
        ).distinct()