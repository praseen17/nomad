from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('login/', views.owner_login, name='owner_login'),
    path('signup/', views.owner_signup, name='owner_signup'),
    path('signup/success/', views.signup_success, name='signup_success'),
    path('logout/', views.user_logout, name='logout'),
    path('staff/login/', views.staff_login, name='staff_login'),
    path('superadmin/login/', views.superadmin_login, name='superadmin_login'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('menu/<slug:slug>/', views.customer_menu, name='customer_menu'),
    path('review/<uuid:token>/', views.review_page, name='review_page'),
    path('review/thanks/', views.review_thanks, name='review_thanks'),
]
