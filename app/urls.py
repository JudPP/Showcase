from app import views
from .viewsets import UserViewSet, AppointmentViewSet, PrescriptionsViewSet
from django.urls import path, include
from rest_framework import routers, viewsets
from rest_framework.authtoken import views as rest_views

router = routers.DefaultRouter()
router.register(r'api/user', UserViewSet)
router.register(r'api/appointments', AppointmentViewSet)
router.register(r'api/prescriptions', PrescriptionsViewSet)


urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/login/',views.login_user, name='login'),
    path('register/', views.register, name='register'),
    path('register/staff', views.staff_register, name='staff_register'),
    path('logout/',views.logout_user, name='logout'),
    path('dashboard/',views.dashboard, name='dashboard'),
    path('schedule/',views.schedule, name='schedule'),
    path('prescriptions/',views.prescriptions, name='prescriptions'),
    path('prescriptions/issue',views.prescription_issue, name='prescription_issue'),
    path('appointment',views.appointment, name='appointment'),
    path('prescriptions/repeat', views.prescription_repeat, name='prescription_repeat'),
    path('prescriptions/approval', views.prescription_approval, name='prescription_approval'),
    path('search/', views.patient_search, name='patient_search'),
    path('search/<str:patient_username>', views.patient_data, name='patient_data'),
    path('user/', views.user_list, name='user_list'),
    path('user/<int:id>', views.user_update, name='user_update'),
    path('user/<int:id>/delete', views.user_delete, name='user_delete'),
    path('user/<int:id>/approve', views.user_approve, name='user_approve'),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', rest_views.obtain_auth_token),
    path('pdf/',views.invoice_download, name='invoice_download'),
    path('pdf_prescription/',views.invoice_prescription_download, name='invoice_prescription_download'),
    path('clear-schedule/', views.clear_google_schedule, name='clear_schedule'),
    path('turnover', views.turnover, name='turnover'),
    path('turnover/pdf/<str:date>', views.turnover_download, name='turnover_download'),
    path('cancel_appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('appointment/payment/<int:appointment_id>', views.payment, name='payment'),
    path('prescriptions/payment/<int:prescription_id>', views.payment_pres, name='payment_pres'),
    path('wipe-users/', views.wipe_users, name='wipe_users'),
    path('forward_appointment/<int:appointment_id>/', views.forward_appointment, name='forward_appointment'),
]