from django import forms

class TechnicianAdd(forms.Form):
    first_name = forms.CharField(label='First name', max_length=100)
    last_name = forms.CharField(label='Last name', max_length=100)
    email = forms.EmailField(label='Email', max_length=100)
    address = forms.CharField(label='Address', max_length=500)
    email_password = forms.CharField(label='email_password', max_length=60)
    # time_for_job = forms.CharField(label='Time For Job', max_length=100)
    # credentials = forms.FileField()
    phone_number = forms.CharField(label='Phone Number', max_length=500)

    def __init__(self, *args, **kwargs):
        # Get 'initial' argument if any
        initial_arguments = kwargs.get('initial', None)
        updated_initial = {}
        if initial_arguments:
            updated_initial['first_name'] = initial_arguments.user.first_name
            updated_initial['last_name'] = initial_arguments.user.last_name
            updated_initial['email_password'] = initial_arguments.email_password
            updated_initial['phone_number'] = initial_arguments.phone_number
            # updated_initial['credentials'] = initial_arguments.credential
            updated_initial['email'] = initial_arguments.user.email
            updated_initial['address'] = initial_arguments.address
            updated_initial['time_for_job'] = initial_arguments.time_for_job

        kwargs.update(initial=updated_initial)
        super(TechnicianAdd, self).__init__(*args, **kwargs)


class CustomerAdd(forms.Form):

    first_name = forms.CharField(label='First name', max_length=100)
    last_name = forms.CharField(label='Last name', max_length=100)
    email = forms.EmailField(label='Email', max_length=100)
    address = forms.CharField(label='Address', max_length=500)
    time_for_job = forms.CharField(label='Time For Job', max_length=100)

    def __init__(self, *args, **kwargs):
        # Get 'initial' argument if any
        initial_arguments = kwargs.get('initial', None)
        updated_initial = {}
        if initial_arguments:

            # updated_initial['first_name'] = initial_arguments.user.first_name
            # updated_initial['last_name'] = initial_arguments.user.last_name
            # updated_initial['email'] = initial_arguments.user.email
            updated_initial['address'] = initial_arguments.address
            updated_initial['time_for_job'] = initial_arguments.time_for_job

        kwargs.update(initial=updated_initial)
        super(CustomerAdd, self).__init__(*args, **kwargs)