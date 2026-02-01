# rent/views/backup_views.py

"""
Backup Views
عروض النسخ الاحتياطي والاستعادة
"""

import os
import json
import hashlib
import subprocess
import shutil
from io import StringIO
from django.views import View
from django.views.generic import ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import FileResponse
from django.utils import timezone
from django.core.management import call_command
from django.conf import settings
from django.db import connection

from rent.models import Backup
from rent.models.backup_models import BackupType, BackupStatus


BACKUP_DIR = os.path.join(settings.BASE_DIR, 'backups')


def _get_db_config():
    """استخراج إعدادات قاعدة البيانات"""
    db = settings.DATABASES['default']
    return {
        'engine': db.get('ENGINE', ''),
        'name': db.get('NAME', ''),
        'user': db.get('USER', ''),
        'password': db.get('PASSWORD', ''),
        'host': db.get('HOST', 'localhost'),
        'port': db.get('PORT', '5432'),
    }


def _pg_dump_available():
    """التحقق من توفر pg_dump"""
    return shutil.which('pg_dump') is not None


class SuperuserRequiredMixin:
    """يتطلب أن يكون المستخدم superuser"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'هذه الصفحة متاحة للمشرفين فقط.')
            return redirect('rent:dashboard')
        return super().dispatch(request, *args, **kwargs)


class BackupListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    """قائمة النسخ الاحتياطية"""
    model = Backup
    template_name = 'backups/backup_list.html'
    context_object_name = 'backups'
    paginate_by = 20
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pg_dump_available'] = _pg_dump_available()
        return context


class BackupCreateView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """إنشاء نسخة احتياطية جديدة (JSON عبر dumpdata)"""

    def post(self, request):
        os.makedirs(BACKUP_DIR, exist_ok=True)

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        file_name = f'backup_{timestamp}.json'
        file_path = os.path.join(BACKUP_DIR, file_name)

        backup = Backup(
            backup_type=BackupType.FULL,
            file_name=file_name,
            file_path=file_path,
            status=BackupStatus.IN_PROGRESS,
            started_at=timezone.now(),
            created_by=request.user,
        )
        backup.save()

        try:
            output = StringIO()
            call_command(
                'dumpdata',
                '--indent', '2',
                '--exclude', 'contenttypes',
                '--exclude', 'admin.logentry',
                '--exclude', 'sessions',
                '--natural-foreign',
                '--natural-primary',
                stdout=output,
            )

            data = output.getvalue()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(data)

            file_size = os.path.getsize(file_path)
            checksum = hashlib.sha256(data.encode('utf-8')).hexdigest()

            parsed = json.loads(data)
            records_count = len(parsed)
            tables = set()
            for record in parsed:
                tables.add(record.get('model', ''))
            tables_count = len(tables)

            backup.file_size = file_size
            backup.records_count = records_count
            backup.tables_count = tables_count
            backup.included_tables = sorted(list(tables))
            backup.checksum = checksum
            backup.mark_as_completed()

            messages.success(request, f'تم إنشاء النسخة الاحتياطية JSON بنجاح ({backup.get_file_size_display()}, {records_count} سجل)')

        except Exception as e:
            backup.mark_as_failed(str(e))
            messages.error(request, f'فشل إنشاء النسخة الاحتياطية: {e}')

        return redirect('rent:backup_list')


class BackupCreateSQLView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """إنشاء نسخة احتياطية SQL عبر pg_dump (مثل SQL Server backup)"""

    def post(self, request):
        if not _pg_dump_available():
            messages.error(request, 'أداة pg_dump غير متوفرة على السيرفر.')
            return redirect('rent:backup_list')

        os.makedirs(BACKUP_DIR, exist_ok=True)

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        file_name = f'backup_{timestamp}.sql'
        file_path = os.path.join(BACKUP_DIR, file_name)

        db = _get_db_config()

        backup = Backup(
            backup_type=BackupType.FULL,
            file_name=file_name,
            file_path=file_path,
            status=BackupStatus.IN_PROGRESS,
            started_at=timezone.now(),
            created_by=request.user,
        )
        backup.save()

        try:
            env = os.environ.copy()
            if db['password']:
                env['PGPASSWORD'] = db['password']

            cmd = [
                'pg_dump',
                '--host', db['host'] or 'localhost',
                '--port', str(db['port'] or '5432'),
                '--username', db['user'],
                '--format', 'plain',
                '--no-owner',
                '--no-privileges',
                '--file', file_path,
                db['name'],
            ]

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                raise Exception(result.stderr)

            file_size = os.path.getsize(file_path)
            checksum = hashlib.sha256(
                open(file_path, 'rb').read()
            ).hexdigest()

            # حساب عدد الجداول من قاعدة البيانات
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
                tables_count = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT SUM(n_live_tup) FROM pg_stat_user_tables"
                )
                records_count = cursor.fetchone()[0] or 0

            backup.file_size = file_size
            backup.tables_count = tables_count
            backup.records_count = records_count
            backup.checksum = checksum
            backup.notes = 'نسخة SQL (pg_dump)'
            backup.mark_as_completed()

            messages.success(request, f'تم إنشاء نسخة SQL بنجاح ({backup.get_file_size_display()})')

        except Exception as e:
            backup.mark_as_failed(str(e))
            if os.path.exists(file_path):
                os.remove(file_path)
            messages.error(request, f'فشل إنشاء نسخة SQL: {e}')

        return redirect('rent:backup_list')


class BackupDownloadView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """تحميل ملف النسخة الاحتياطية"""

    def get(self, request, pk):
        try:
            backup = Backup.objects.get(pk=pk)
        except Backup.DoesNotExist:
            messages.error(request, 'النسخة الاحتياطية غير موجودة.')
            return redirect('rent:backup_list')

        if not os.path.exists(backup.file_path):
            messages.error(request, 'ملف النسخة الاحتياطية غير موجود على السيرفر.')
            return redirect('rent:backup_list')

        return FileResponse(
            open(backup.file_path, 'rb'),
            as_attachment=True,
            filename=backup.file_name,
        )


class BackupRestoreView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """استعادة البيانات من نسخة احتياطية"""

    def get(self, request):
        return render(request, 'backups/backup_restore.html')

    def post(self, request):
        backup_id = request.POST.get('backup_id')
        uploaded_file = request.FILES.get('backup_file')

        file_path = None
        temp_file = False
        is_sql = False

        if backup_id:
            try:
                backup = Backup.objects.get(pk=backup_id)
                file_path = backup.file_path
                is_sql = file_path.endswith('.sql')
            except Backup.DoesNotExist:
                messages.error(request, 'النسخة الاحتياطية غير موجودة.')
                return redirect('rent:backup_list')
        elif uploaded_file:
            if not (uploaded_file.name.endswith('.json') or uploaded_file.name.endswith('.sql')):
                messages.error(request, 'يجب أن يكون الملف بصيغة JSON أو SQL.')
                return redirect('rent:backup_restore')

            is_sql = uploaded_file.name.endswith('.sql')
            os.makedirs(BACKUP_DIR, exist_ok=True)
            ext = 'sql' if is_sql else 'json'
            file_path = os.path.join(BACKUP_DIR, f'restore_temp_{timezone.now().strftime("%Y%m%d_%H%M%S")}.{ext}')
            temp_file = True
            with open(file_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
        else:
            messages.error(request, 'يرجى اختيار نسخة أو رفع ملف.')
            return redirect('rent:backup_restore')

        if not os.path.exists(file_path):
            messages.error(request, 'ملف النسخة الاحتياطية غير موجود.')
            return redirect('rent:backup_list')

        try:
            if is_sql:
                self._restore_sql(file_path)
            else:
                call_command('loaddata', file_path, verbosity=0)
            messages.success(request, 'تم استعادة البيانات بنجاح!')
        except Exception as e:
            messages.error(request, f'فشل استعادة البيانات: {e}')
        finally:
            if temp_file and os.path.exists(file_path):
                os.remove(file_path)

        return redirect('rent:backup_list')

    def _restore_sql(self, file_path):
        """استعادة من ملف SQL عبر psql"""
        if not shutil.which('psql'):
            raise Exception('أداة psql غير متوفرة على السيرفر.')

        db = _get_db_config()
        env = os.environ.copy()
        if db['password']:
            env['PGPASSWORD'] = db['password']

        cmd = [
            'psql',
            '--host', db['host'] or 'localhost',
            '--port', str(db['port'] or '5432'),
            '--username', db['user'],
            '--dbname', db['name'],
            '--file', file_path,
        ]

        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            raise Exception(result.stderr)


class BackupDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    """حذف نسخة احتياطية"""
    model = Backup
    success_url = reverse_lazy('rent:backup_list')

    def delete(self, request, *args, **kwargs):
        backup = self.get_object()
        if backup.file_path and os.path.exists(backup.file_path):
            os.remove(backup.file_path)
        messages.success(request, 'تم حذف النسخة الاحتياطية بنجاح.')
        return super().delete(request, *args, **kwargs)
