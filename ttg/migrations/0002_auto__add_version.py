# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Version'
        db.create_table('ttg_version', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('mediafile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ttg.MediaFile'])),
        ))
        db.send_create_signal('ttg', ['Version'])


    def backwards(self, orm):
        # Deleting model 'Version'
        db.delete_table('ttg_version')


    models = {
        'ttg.mediafile': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'MediaFile'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'ttg.version': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Version'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mediafile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ttg.MediaFile']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '12'})
        }
    }

    complete_apps = ['ttg']