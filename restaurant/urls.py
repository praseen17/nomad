from django.urls import path
from . import views

urlpatterns = [
    # Owner dashboard & sub-pages
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/workers/', views.owner_workers, name='owner_workers'),
    path('owner/menu/', views.owner_menu, name='owner_menu'),
    path('owner/tables/', views.owner_tables, name='owner_tables'),
    path('owner/invoices/', views.owner_invoices, name='owner_invoices'),
    path('owner/analytics/', views.owner_analytics, name='owner_analytics'),
    path('owner/reviews/', views.owner_reviews, name='owner_reviews'),
    path('owner/qr-menu/', views.owner_qr_menu, name='owner_qr_menu'),
    path('owner/settings/', views.owner_settings, name='owner_settings'),

    # Manager dashboard
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/workers/', views.manager_workers, name='manager_workers'),
    path('manager/menu/', views.manager_menu, name='manager_menu'),
    path('manager/tables/', views.manager_tables, name='manager_tables'),
    path('manager/invoices/', views.manager_invoices, name='manager_invoices'),
    path('manager/qr-menu/', views.manager_qr_menu, name='manager_qr_menu'),

    # Asst Manager
    path('asst-manager/', views.asst_manager_dashboard, name='asst_manager_dashboard'),

    # Receptionist
    path('reception/', views.reception_dashboard, name='reception_dashboard'),
    path('reception/billing/<int:table_id>/', views.reception_billing, name='reception_billing'),
    path('reception/invoices/', views.reception_invoices, name='reception_invoices'),

    # Waiter
    path('waiter/', views.waiter_dashboard, name='waiter_dashboard'),
    path('waiter/table/<int:table_id>/', views.waiter_table, name='waiter_table'),

    # Chef
    path('chef/', views.chef_dashboard, name='chef_dashboard'),

    # Super Admin
    path('superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/restaurants/', views.superadmin_restaurants, name='superadmin_restaurants'),
    path('superadmin/pending/', views.superadmin_pending, name='superadmin_pending'),
    path('superadmin/approve/<int:restaurant_id>/', views.superadmin_approve, name='superadmin_approve'),
    path('superadmin/reject/<int:restaurant_id>/', views.superadmin_reject, name='superadmin_reject'),
    path('superadmin/audit-log/', views.superadmin_audit, name='superadmin_audit'),
    path('superadmin/broadcast/', views.superadmin_broadcast, name='superadmin_broadcast'),
]
