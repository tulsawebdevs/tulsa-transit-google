from zipfile import is_zipfile

from django import forms

from mtta.tasks import import_mtta_signup
from ttg.models import MediaFile


class UploadFileForm(forms.ModelForm):
    '''Form for uploading a file'''

    class Meta:
        model = MediaFile
        fields = ('file_type', 'file')

    def clean_file(self):
        if not is_zipfile(self.files['file']):
            raise forms.ValidationError('Uploaded files must be ZIP format.')
        return self.cleaned_data['file']

    def save(self, *args, **kwargs):
        self.instance.source = MediaFile.UPLOADED
        instance = super(UploadFileForm, self).save(*args, **kwargs)
        if instance.file_type == MediaFile.IMPORT_FILE:
            import_mtta_signup.delay(instance.id)
        return instance

