"""
Management command to setup default permission groups
أمر إعداد مجموعات الصلاحيات الافتراضية
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'إعداد مجموعات الصلاحيات الافتراضية'

    # تعريف المجموعات وصلاحياتها
    GROUPS = {
        'مدير النظام': {
            'description': 'جميع الصلاحيات',
            'permissions': '__all__',
        },
        'محاسب': {
            'description': 'سندات القبض + عرض العقود + التقارير',
            'permissions': [
                # سندات القبض - كاملة
                'rent.view_receipt',
                'rent.add_receipt',
                'rent.change_receipt',
                'rent.delete_receipt',
                'rent.post_receipt',
                'rent.cancel_receipt',
                'rent.print_receipt',
                'rent.export_receipt_pdf',
                # العقود - عرض فقط
                'rent.view_contract',
                'rent.view_contract_statement',
                # المستأجرين - عرض فقط
                'rent.view_tenant',
                # التقارير - كاملة
                'rent.view_reporttemplate',
                'rent.view_reports',
                'rent.export_reports',
            ],
        },
        'مدير إيجار': {
            'description': 'العقود + المستأجرين + عرض العقارات والسندات',
            'permissions': [
                # العقود - كاملة
                'rent.view_contract',
                'rent.add_contract',
                'rent.change_contract',
                'rent.delete_contract',
                'rent.activate_contract',
                'rent.terminate_contract',
                'rent.view_contract_statement',
                # تعديلات العقود - كاملة
                'rent.view_contractmodification',
                'rent.add_contractmodification',
                'rent.change_contractmodification',
                'rent.delete_contractmodification',
                'rent.apply_contractmodification',
                # المستأجرين - كاملة
                'rent.view_tenant',
                'rent.add_tenant',
                'rent.change_tenant',
                'rent.delete_tenant',
                'rent.view_tenantdocument',
                'rent.add_tenantdocument',
                'rent.change_tenantdocument',
                'rent.delete_tenantdocument',
                # العقارات - عرض فقط
                'rent.view_land',
                'rent.view_building',
                'rent.view_unit',
                # سندات القبض - عرض فقط
                'rent.view_receipt',
                # التقارير - عرض فقط
                'rent.view_reporttemplate',
                'rent.view_reports',
            ],
        },
        'موظف استقبال': {
            'description': 'إضافة سندات + عرض العقود والمستأجرين',
            'permissions': [
                # سندات القبض - إضافة وعرض وطباعة
                'rent.view_receipt',
                'rent.add_receipt',
                'rent.print_receipt',
                # العقود - عرض فقط
                'rent.view_contract',
                'rent.view_contract_statement',
                # المستأجرين - عرض فقط
                'rent.view_tenant',
            ],
        },
        'مشاهد فقط': {
            'description': 'عرض فقط لجميع البيانات',
            'permissions': [
                'rent.view_receipt',
                'rent.view_contract',
                'rent.view_contract_statement',
                'rent.view_contractmodification',
                'rent.view_tenant',
                'rent.view_tenantdocument',
                'rent.view_land',
                'rent.view_building',
                'rent.view_unit',
                'rent.view_reporttemplate',
                'rent.view_reports',
            ],
        },
    }

    def handle(self, *args, **options):
        self.stdout.write('\n=== Setup Permission Groups ===\n')

        rent_permissions = Permission.objects.filter(
            content_type__app_label='rent'
        )

        for group_name, config in self.GROUPS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'\n  Group: {group_name} ({status})')

            if config['permissions'] == '__all__':
                group.permissions.set(rent_permissions)
                self.stdout.write(f'  Permissions: ALL rent permissions ({rent_permissions.count()})')
            else:
                perms_to_add = []
                for perm_str in config['permissions']:
                    app_label, codename = perm_str.split('.')
                    try:
                        perm = Permission.objects.get(
                            content_type__app_label=app_label,
                            codename=codename,
                        )
                        perms_to_add.append(perm)
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'  WARNING: Permission {perm_str} not found')
                        )

                group.permissions.set(perms_to_add)
                self.stdout.write(f'  Permissions: {len(perms_to_add)} assigned')

        self.stdout.write(self.style.SUCCESS('\n=== Setup Complete ===\n'))

        self.stdout.write('\nAvailable rent permissions:')
        for perm in rent_permissions.order_by('content_type__model', 'codename'):
            self.stdout.write(f'  - rent.{perm.codename}')
