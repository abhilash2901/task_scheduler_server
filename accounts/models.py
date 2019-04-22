# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class Role(models.Model):
    role_name = models.CharField(max_length=100)

    def __str__(self):
        return self.role_name


class UserDetails(models.Model):
    user = models.OneToOneField(User,related_name='user_details')
    email_password = models.CharField(max_length=60)
    token_pickle = models.FileField(upload_to='media',null=True,blank=True)
    credential = models.FileField(upload_to='media')
    phone_number = models.CharField(max_length=20)
    role = models.ForeignKey(Role, related_name='users')
    address = models.CharField(max_length=500)
    auth_url = models.CharField(max_length=500,null=True,blank=True)
    time_for_job = models.CharField(max_length=100)
    is_email_authenticated = models.BooleanField(default=False)

    def __str__(self):
        return self.user.email+">>"+self.role.role_name

    def can_add_technician(self):
        """
        
        :return: 
        """
        status = False
        if self.role.role_name == 'Admin':
            status = True
        return status


# class TechnicianSchedule(models.Model):
#     technician = models.ForeignKey(UserDetails,related_name='technician')
#     start_datetime = models.DateTimeField()
#     end_datetime = models.DateTimeField()
#     job_title = models.CharField(max_length=500,null=True,blank=True)
#     description = models.CharField(max_length=500,null=True,blank=True)
#     customer_address = models.CharField(max_length=500)
#
#     def __str__(self):
#         return self.customer_address


class TechnicianAppointments(models.Model):

    technician = models.ForeignKey(UserDetails, related_name='technician_appointments')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    title = models.CharField(max_length=500)
    location = models.CharField(max_length=1000)
