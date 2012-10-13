from django import forms

from mtta.tasks import import_mtta_signup
from ttg.models import MediaFile

import sys
if sys.version_info >= (2, 7, 0):
    from zipfile import is_zipfile
else:
    from zipfile import _EndRecData

    
    def _check_zipfile(fp):
        try:
            if _EndRecData(fp):
                return True         # file has correct magic number
        except IOError:
            pass
        return False


    def is_zipfile(filename):
        """Quickly see if a file is a ZIP file by checking the magic number.

        The filename argument may be a file or file-like object too.
        """
        result = False
        try:
            if hasattr(filename, "read"):
                result = _check_zipfile(fp=filename)
            else:
                with open(filename, "rb") as fp:
                    result = _check_zipfile(fp)
        except IOError:
            pass
        return result


class UploadFileForm(forms.ModelForm):
    '''Form for uploading a file'''

    class Meta:
        model = MediaFile
        fields = ('file_type', 'file')

    def clean_file(self):
        file = self.files['file']
        file.open()
        if not is_zipfile(file):
            raise forms.ValidationError('Uploaded files must be ZIP format.')
        return self.cleaned_data['file']

    def save(self, *args, **kwargs):
        self.instance.source = MediaFile.UPLOADED
        instance = super(UploadFileForm, self).save(*args, **kwargs)
        if instance.file_type == MediaFile.MTTA_SIGNUP:
            import_mtta_signup.delay(instance.id)
        return instance
