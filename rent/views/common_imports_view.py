# rent/common_imports_view.py

from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from decimal import Decimal
import json

# استيراد النماذج
from rent.models import (
    UserProfile, Land, Building, Unit, Tenant, TenantDocument,
    Contract, ContractModification, Receipt, Notification,
    ReportTemplate
)

# استيراد النماذج (Forms)
from rent.forms import (
    UserProfileForm, LandForm, BuildingForm, UnitForm, TenantForm,
    ContractForm, ContractModificationForm, ReceiptForm, ReportFilterForm
)

# ✅ استيراد الـ Mixins من mixins.py
from rent.mixins import PermissionCheckMixin, AuditLogMixin