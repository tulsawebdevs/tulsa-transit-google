# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Fare'
        db.create_table('mtta_fare', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('cost', self.gf('django.db.models.fields.DecimalField')(max_digits=5, decimal_places=2)),
            ('line_name_ipattern', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
        ))
        db.send_create_signal('mtta', ['Fare'])

        # Adding field 'Line.fare'
        db.add_column('mtta_line', 'fare',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Fare'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'Fare'
        db.delete_table('mtta_fare')

        # Deleting field 'Line.fare'
        db.delete_column('mtta_line', 'fare_id')


    models = {
        'mtta.agencyinfo': {
            'Meta': {'object_name': 'AgencyInfo'},
            'fare_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'timezone': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'mtta.fare': {
            'Meta': {'object_name': 'Fare'},
            'cost': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_name_ipattern': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'mtta.feedinfo': {
            'Meta': {'object_name': 'FeedInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'mtta.line': {
            'Meta': {'ordering': "('line_id',)", 'unique_together': "(('signup', 'line_id'),)", 'object_name': 'Line'},
            'attributes': ('django.db.models.fields.TextField', [], {'default': '[]'}),
            'fare': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Fare']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_abbr': ('django.db.models.fields.CharField', [], {'max_length': '8', 'db_index': 'True'}),
            'line_color': ('django.db.models.fields.IntegerField', [], {}),
            'line_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'line_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'line_type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.SignUp']"})
        },
        'mtta.linedirection': {
            'Meta': {'ordering': "('linedir_id',)", 'unique_together': "(('linedir_id', 'line'),)", 'object_name': 'LineDirection'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Line']"}),
            'linedir_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'mtta.node': {
            'Meta': {'ordering': "('node_id',)", 'object_name': 'Node'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'node_abbr': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'node_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'node_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.SignUp']"}),
            'stops': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'nodes'", 'symmetrical': 'False', 'to': "orm['mtta.Stop']"})
        },
        'mtta.pattern': {
            'Meta': {'unique_together': "(('linedir', 'pattern_id'),)", 'object_name': 'Pattern'},
            'fixed_pattern': ('django.db.models.fields.TextField', [], {'default': '[]', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linedir': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.LineDirection']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'pattern_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'raw_pattern': ('django.db.models.fields.TextField', [], {'default': '[]'})
        },
        'mtta.service': {
            'Meta': {'ordering': "('signup', 'service_id')", 'unique_together': "(('signup', 'service_id'),)", 'object_name': 'Service'},
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'friday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'monday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'saturday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'service_id': ('django.db.models.fields.IntegerField', [], {}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.SignUp']", 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'sunday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'thursday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tuesday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'wednesday': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'mtta.serviceexception': {
            'Meta': {'object_name': 'ServiceException'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'exception_type': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Service']"})
        },
        'mtta.shapeattribute': {
            'Meta': {'object_name': 'ShapeAttribute'},
            'attributes': ('django.db.models.fields.TextField', [], {'default': '[]'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.SignUp']"})
        },
        'mtta.signup': {
            'Meta': {'object_name': 'SignUp'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'feeds': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['multigtfs.Feed']", 'through': "orm['mtta.SignupExport']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'mtta.signupexport': {
            'Meta': {'object_name': 'SignupExport'},
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['multigtfs.Feed']"}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.SignUp']"}),
            'started': ('django.db.models.fields.DateTimeField', [], {})
        },
        'mtta.stop': {
            'Meta': {'ordering': "('signup', 'stop_id')", 'unique_together': "(('signup', 'stop_id'),)", 'object_name': 'Stop'},
            'attributes': ('django.db.models.fields.TextField', [], {'default': '[]'}),
            'facing_dir': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_service': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lat': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '8'}),
            'lon': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '8'}),
            'node_abbr': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.SignUp']"}),
            'site_name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'stop_abbr': ('django.db.models.fields.CharField', [], {'max_length': '8', 'db_index': 'True'}),
            'stop_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'stop_name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'mtta.stopbyline': {
            'Meta': {'ordering': "('linedir', 'seq')", 'unique_together': "(('stop', 'linedir', 'seq'),)", 'object_name': 'StopByLine'},
            'attributes': ('django.db.models.fields.TextField', [], {'default': '[]'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linedir': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.LineDirection']"}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Node']", 'null': 'True', 'blank': 'True'}),
            'seq': ('django.db.models.fields.IntegerField', [], {}),
            'stop': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Stop']"})
        },
        'mtta.stopbypattern': {
            'Meta': {'ordering': "('pattern', 'seq')", 'unique_together': "(('stop', 'linedir', 'pattern', 'seq'),)", 'object_name': 'StopByPattern'},
            'attributes': ('django.db.models.fields.TextField', [], {'default': '[]'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linedir': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.LineDirection']"}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Node']", 'null': 'True', 'blank': 'True'}),
            'pattern': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Pattern']"}),
            'seq': ('django.db.models.fields.IntegerField', [], {}),
            'stop': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Stop']"})
        },
        'mtta.trip': {
            'Meta': {'ordering': "('tripday', 'seq', 'pattern')", 'unique_together': "(('tripday', 'seq', 'pattern'),)", 'object_name': 'Trip'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pattern': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Pattern']"}),
            'seq': ('django.db.models.fields.IntegerField', [], {}),
            'tripday': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.TripDay']"})
        },
        'mtta.tripday': {
            'Meta': {'ordering': "('linedir', 'service')", 'unique_together': "(('linedir', 'service'),)", 'object_name': 'TripDay'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linedir': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.LineDirection']"}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Service']"})
        },
        'mtta.tripstop': {
            'Meta': {'ordering': "('tripday', 'seq')", 'unique_together': "(('tripday', 'seq'),)", 'object_name': 'TripStop'},
            'arrival': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'departure'", 'unique': 'True', 'null': 'True', 'to': "orm['mtta.TripStop']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Node']", 'null': 'True', 'blank': 'True'}),
            'node_abbr': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
            'scheduled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'seq': ('django.db.models.fields.IntegerField', [], {}),
            'stop': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Stop']", 'null': 'True', 'blank': 'True'}),
            'stop_abbr': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'tripday': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.TripDay']"})
        },
        'mtta.triptime': {
            'Meta': {'ordering': "('trip', 'tripstop', 'time')", 'unique_together': "(('trip', 'tripstop'),)", 'object_name': 'TripTime'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'trip': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.Trip']"}),
            'tripstop': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mtta.TripStop']"})
        },
        'multigtfs.feed': {
            'Meta': {'object_name': 'Feed', 'db_table': "'feed'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['mtta']