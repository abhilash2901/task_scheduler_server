"""task_scheduler URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin,auth
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from accounts.views import DashboardView, login, logout, TechnicianView, AddTechnicianView, CustomerView, \
    AddCustomerView, EditCustomerView, EditTechnicianView, AssignTechnicianView, TechnicianAvailability

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$', DashboardView.as_view(),name='dashboard'),
    url(r'manage-technicians', TechnicianView.as_view(),name='manage_technicians'),
    url(r'manage-customers', CustomerView.as_view(),name='manage_customers'),
    url(r'technician-availability/(?P<technician_pk>\d+)', TechnicianAvailability.as_view(),name='technician_availability'),
    url(r'add-technicians', AddTechnicianView.as_view(),name='add_technicians'),
    url(r'edit-technicians/(?P<customer_pk>\d+)/$', EditTechnicianView.as_view(),name='edit_technicians'),
    url(r'add-customers', AddCustomerView.as_view(),name='add_customers'),
    url(r'edit-customers/(?P<customer_pk>\d+)/$', EditCustomerView.as_view(),name='edit_customers'),
    url(r'assign-technician/(?P<customer_pk>\d+)/$', AssignTechnicianView.as_view(),name='assign_technician'),
    url(r'login', login,name='login'),

    url(r'user-logout', logout,name='logout'),
]

urlpatterns += staticfiles_urlpatterns()