# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'MediaFile'
        db.create_table('ttg_mediafile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('added_at', self.gf('django.db.models.fields.DateField')()),
            ('local_name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('file_type', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('ttg', ['MediaFile'])


    def backwards(self, orm):
        
        # Deleting model 'MediaFile'
        db.delete_table('ttg_mediafile')


    models = {
        'ttg.mediafile': {
            'Meta': {'object_name': 'MediaFile'},
            'added_at': ('django.db.models.fields.DateField', [], {}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        }
    }

    complete_apps = ['ttg']
