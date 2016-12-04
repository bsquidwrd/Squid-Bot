from django import forms
from django.contrib.auth.models import User


class UpdateAccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].help_text = "Check this box if you want to delete your account."
        self.fields['is_active'].label = "Delete Account?"
        self.initial['is_active'] = not(self.initial['is_active'])

    def clean_is_active(self):
        # Reverses true/false for your form prior to validation
        #
        # You can also raise a ValidationError here if you receive
        # a value you don't want, to prevent the form's is_valid
        # method from return true if, say, the user hasn't chosen
        # to deactivate their account
        is_active = not(self.cleaned_data["is_active"])
        return is_active
