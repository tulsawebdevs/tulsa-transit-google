from django import forms

from models import MediaFile

class UploadFileForm(forms.ModelForm):
    '''Form for uploading a file'''
        
    upload = forms.FileField()

    class Meta:
        model = MediaFile
        fields = ('file_type',)

