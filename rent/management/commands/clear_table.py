from django.core.management.base import BaseCommand, CommandError
from django.apps import apps


class Command(BaseCommand):
    help = 'حذف جميع السجلات من جدول معين - Delete all records from a specified model'

    def add_arguments(self, parser):
        parser.add_argument('model_name', type=str, help='اسم الموديل مثل: Contract, Tenant, Receipt')
        parser.add_argument('--force', action='store_true', help='حذف بدون تأكيد')

    def handle(self, *args, **options):
        model_name = options['model_name']
        force = options['force']

        # البحث عن الموديل في كل التطبيقات
        model = None
        for app_config in apps.get_app_configs():
            try:
                model = apps.get_model(app_config.label, model_name)
                break
            except LookupError:
                continue

        if model is None:
            available = []
            for app_config in apps.get_app_configs():
                for m in app_config.get_models():
                    available.append(m.__name__)
            self.stderr.write(self.style.ERROR(f'الموديل "{model_name}" غير موجود.'))
            self.stderr.write(self.style.WARNING(f'الموديلات المتاحة: {", ".join(sorted(available))}'))
            raise CommandError(f'Model "{model_name}" not found.')

        count = model.objects.count()

        if count == 0:
            self.stdout.write(self.style.WARNING(f'الجدول "{model_name}" فارغ بالفعل.'))
            return

        if not force:
            self.stdout.write(self.style.WARNING(
                f'سيتم حذف {count} سجل من "{model_name}". هل أنت متأكد؟ (yes/no): '
            ))
            confirm = input()
            if confirm.lower() not in ('yes', 'y'):
                self.stdout.write(self.style.NOTICE('تم الإلغاء.'))
                return

        deleted, details = model.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'تم حذف {deleted} سجل من "{model_name}" بنجاح.'))
        if details:
            for key, val in details.items():
                if val > 0:
                    self.stdout.write(f'  - {key}: {val}')
