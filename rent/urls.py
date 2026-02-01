# urls.py - نظام إدارة العقود والإيجارات
from django.urls import path, include
from . import views
from rent.views.report_t_views import (
    tenants_report_view,
    detailed_tenants_report,
    export_tenants_report_excel,
    export_tenants_report_pdf,
)
from rent.views.contract_modification_views import (
    ModificationListView,
    ModificationDetailView,
    ExtensionCreateView,
    RentIncreaseCreateView,
    RentDecreaseCreateView,
    DiscountCreateView,
    VATCreateView,
    TerminationCreateView,
    ModificationUpdateView,
    ModificationDeleteView,
    ContractModificationsView,
    ApplyModificationView,
   
)
from rent.views.contract_statement_views import (
    ContractStatementView,
    ContractStatementPrintView,
    ContractStatementAPIView
)
from rent.views.backup_views import (
    BackupListView,
    BackupCreateView,
    BackupCreateSQLView,
    BackupDownloadView,
    BackupRestoreView,
    BackupDeleteView,
)

app_name = 'rent'

urlpatterns = [
    # ========================================
    # الصفحة الرئيسية والداشبورد
    # ========================================
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # ========================================
    # إدارة الأراضي
    # ========================================
    path('lands/', views.LandListView.as_view(), name='land_list'),
    path('lands/create/', views.LandCreateView.as_view(), name='land_create'),
    path('lands/<int:pk>/', views.LandDetailView.as_view(), name='land_detail'),
    path('lands/<int:pk>/update/', views.LandUpdateView.as_view(), name='land_update'),
    path('lands/<int:pk>/delete/', views.LandDeleteView.as_view(), name='land_delete'),
    
    # ========================================
    # إدارة المباني
    # ========================================
    path('buildings/', views.BuildingListView.as_view(), name='building_list'),
    path('buildings/create/', views.BuildingCreateView.as_view(), name='building_create'),
    path('buildings/<int:pk>/', views.BuildingDetailView.as_view(), name='building_detail'),
    path('buildings/<int:pk>/update/', views.BuildingUpdateView.as_view(), name='building_update'),
    path('buildings/<int:pk>/delete/', views.BuildingDeleteView.as_view(), name='building_delete'),
    
    # ========================================
    # إدارة الوحدات
    # ========================================
    path('units/', views.UnitListView.as_view(), name='unit_list'),
    path('units/create/', views.UnitCreateView.as_view(), name='unit_create'),
    path('units/<int:pk>/', views.UnitDetailView.as_view(), name='unit_detail'),
    path('units/<int:pk>/update/', views.UnitUpdateView.as_view(), name='unit_update'),
    path('units/<int:pk>/delete/', views.UnitDeleteView.as_view(), name='unit_delete'),
    
    # ========================================
    # إدارة المستأجرين
    # ========================================
    path('tenants/', views.TenantListView.as_view(), name='tenant_list'),
    path('tenants/create/', views.TenantCreateView.as_view(), name='tenant_create'),
    path('tenants/<int:pk>/', views.TenantDetailView.as_view(), name='tenant_detail'),
    path('tenants/<int:pk>/update/', views.TenantUpdateView.as_view(), name='tenant_update'),
    path('tenants/<int:pk>/delete/', views.TenantDeleteView.as_view(), name='tenant_delete'),
    
    # ========================================
    # إدارة العقود
    # ========================================
    path('contracts/', views.ContractListView.as_view(), name='contract_list'),
    path('contracts/create/', views.ContractCreateView.as_view(), name='contract_create'),
    path('contracts/<int:pk>/', views.ContractDetailView.as_view(), name='contract_detail'),
    path('contracts/<int:pk>/update/', views.ContractUpdateView.as_view(), name='contract_update'),
    path('contracts/<int:pk>/activate/', views.ContractActivateView.as_view(), name='contract_activate'),
    path('contracts/<int:pk>/terminate/', views.ContractTerminateView.as_view(), name='contract_terminate'),
        
    # ========================================
    # إدارة الدفعات - Receipt Management
    # ========================================

    # 1️⃣ URLs الثابتة أولاً (Static URLs First)
    path('receipts/create/', views.ReceiptCreateView.as_view(), name='receipt_create'),

    # 2️⃣ قائمة السندات (List)
    path('receipts/', views.ReceiptListView.as_view(), name='receipt_list'),

    # 3️⃣ URLs الديناميكية (Dynamic URLs with <int:pk>)
    path('receipts/<int:pk>/', views.ReceiptDetailView.as_view(), name='receipt_detail'),
    path('receipts/<int:pk>/update/', views.ReceiptUpdateView.as_view(), name='receipt_update'),
    path('receipts/<int:pk>/delete/', views.ReceiptDeleteView.as_view(), name='receipt_delete'),
    path('receipts/<int:pk>/post/', views.ReceiptPostView.as_view(), name='receipt_post'),
    path('receipts/<int:pk>/cancel/', views.ReceiptCancelView.as_view(), name='receipt_cancel'),
    path('receipts/<int:pk>/print/', views.ReceiptPrintView.as_view(), name='receipt_print'),
    path('receipts/<int:pk>/pdf/', views.ReceiptPDFView.as_view(), name='receipt_pdf'),

    # ========================================
    # التعديلات علي العقود
    # ========================================


    # List & Detail
    path('modifications/', ModificationListView.as_view(), name='modification_list'),
    path('modifications/<int:pk>/', ModificationDetailView.as_view(), name='modification_detail'),
    
    # Create
    path('modifications/create/extension/', ExtensionCreateView.as_view(), name='create_extension'),
    path('modifications/create/rent-increase/', RentIncreaseCreateView.as_view(), name='create_rent_increase'),
    path('modifications/create/rent-decrease/', RentDecreaseCreateView.as_view(), name='create_rent_decrease'),
    path('modifications/create/discount/', DiscountCreateView.as_view(), name='create_discount'),
    path('modifications/create/vat/', VATCreateView.as_view(), name='create_vat'),
    path('modifications/create/termination/', TerminationCreateView.as_view(), name='create_termination'),
    
    # Update & Delete
    path('modifications/<int:pk>/edit/', ModificationUpdateView.as_view(), name='edit_modification'),
    path('modifications/<int:pk>/delete/', ModificationDeleteView.as_view(), name='delete_modification'),
    
    # Apply
    path('modifications/<int:pk>/apply/', ApplyModificationView.as_view(), name='apply_modification'),
    
    # Contract-specific
    path('contracts/<int:contract_id>/modifications/', ContractModificationsView.as_view(), name='contract_modifications'),
    

    # ========================================
    # التقارير
    # ========================================
    path('reports/', views.ReportDashboardView.as_view(), name='report_dashboard'),
    path('reports/active-contracts/', views.ActiveContractsReportView.as_view(), name='report_active_contracts'),
    path('reports/tenants-due/', views.TenantsDueReportView.as_view(), name='report_tenants_due'),
    path('reports/contracts-expiring/', views.ContractsExpiringReportView.as_view(), name='report_contracts_expiring'),
    path('reports/occupancy/', views.OccupancyReportView.as_view(), name='report_occupancy'),
    path('reports/revenue/', views.RevenueReportView.as_view(), name='report_revenue'),

    path('reports/rep/', tenants_report_view, name='report_rep'),
    path('reports/rep/export-excel/', export_tenants_report_excel, name='export_tenants_excel'),
    path('reports/rep/export-pdf/', export_tenants_report_pdf, name='export_tenants_pdf'),
    

    path('contracts/<int:pk>/statement/',ContractStatementView.as_view(),name='contract_statement'),
    path('contracts/<int:pk>/statement/print/',ContractStatementPrintView.as_view(),name='contract_statement_print'),
    path('contracts/<int:pk>/statement/api/',ContractStatementAPIView.as_view(),name='contract_statement_api'),



    # ========================================
    # النسخ الاحتياطي
    # ========================================
    path('backups/', BackupListView.as_view(), name='backup_list'),
    path('backups/create/', BackupCreateView.as_view(), name='backup_create'),
    path('backups/create-sql/', BackupCreateSQLView.as_view(), name='backup_create_sql'),
    path('backups/restore/', BackupRestoreView.as_view(), name='backup_restore'),
    path('backups/<int:pk>/download/', BackupDownloadView.as_view(), name='backup_download'),
    path('backups/<int:pk>/delete/', BackupDeleteView.as_view(), name='backup_delete'),

    # ========================================
    # الإشعارات
    # ========================================
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/mark-read/', views.NotificationMarkReadView.as_view(), name='notification_mark_read'),
    

]