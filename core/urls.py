from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('departments/', views.departments, name='departments'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    path('departments/<int:pk>/', views.department_detail, name='department_detail'),
    path('doctors/', views.doctors, name='doctors'),
    path('doctors/<int:pk>/delete/', views.doctor_delete, name='doctor_delete'),
    path('appointments/book/', views.book_appointment, name='book_appointment'),
    path('appointments/<int:pk>/delete/', views.appointment_delete, name='appointment_delete'),
    # Patient Management URLs
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/create/', views.patient_create, name='patient_create'),
    path('patients/<int:pk>/delete/', views.patient_delete, name='patient_delete'),
    path('patients/<int:pk>/edit/', views.patient_update, name='patient_update'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    # Health Record URLs
    path('health-records/create/', views.health_record_create, name='health_record_create'),
    path('health-records/create/<int:patient_pk>/', views.health_record_create, name='health_record_create_for_patient'),
    path('health-records/<int:pk>/', views.health_record_detail, name='health_record_detail'),
]


