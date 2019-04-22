# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from accounts.models import Role,UserDetails,TechnicianAppointments

admin.site.register(Role)
admin.site.register(UserDetails)
admin.site.register(TechnicianAppointments)
