from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
User = get_user_model()

from .models import (
    QuestionTypeProgramTestCase,
    QuestionTypeFunctionTestCase
)


# class DebugInputForm(forms.Form):
#     # TODO: Can we have input fields without length limits
#     params_input = forms.CharField(
#         max_length=100,
#         required=False
#     )
#     debug_input = forms.CharField(
#         max_length=500,
#         widget=forms.Textarea({'rows': 2, 'cols': 30}),
#         required=False
#     )

# class TestCaseForm(forms.ModelForm):
#     test_input = forms.CharField(max_length=500, widget=forms.Textarea({'rows': 2, 'cols': 30}), required=False)
#     expected_output = forms.CharField(max_length=500, widget=forms.Textarea({'rows': 2, 'cols': 30}), required=False)

#     class Meta:
#         model = TestCase
#         fields = ('__all__')

class QuestionTypeProgramTestCaseForm(forms.ModelForm):
    test_input = forms.CharField(max_length=500, widget=forms.Textarea({'rows': 2, 'cols': 30}), required=False)
    expected_output = forms.CharField(max_length=500, widget=forms.Textarea({'rows': 2, 'cols': 30}), required=False)

    class Meta:
        model = QuestionTypeProgramTestCase
        fields = ('__all__')


class QuestionTypeFunctionTestCaseForm(forms.ModelForm):
    test_input = forms.CharField(max_length=500, widget=forms.Textarea({'rows': 2, 'cols': 30}), required=False)
    expected_output = forms.CharField(max_length=500, widget=forms.Textarea({'rows': 2, 'cols': 30}), required=False)

    class Meta:
        model = QuestionTypeFunctionTestCase
        fields = ('__all__')
