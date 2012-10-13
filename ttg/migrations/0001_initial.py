# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MediaFile'
        db.create_table('ttg_mediafile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('file_type', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('ttg', ['MediaFile'])


    def backwards(self, orm):
        # Deleting model 'MediaFile'
        db.delete_table('ttg_mediafile')


    models = {
        'ttg.mediafile': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'MediaFile'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        }
    }

    complete_apps = ['ttg']