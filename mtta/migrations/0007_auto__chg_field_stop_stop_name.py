# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Stop.stop_name'
        db.alter_column(u'mtta_stop', 'stop_name', self.gf('django.db.models.fields.CharField')(max_length=100))

    def backwards(self, orm):

        # Changing field 'Stop.stop_name'
        db.alter_column(u'mtta_stop', 'stop_name', self.gf('django.db.models.fields.CharField')(max_length=50))

    models = {
        u'mtta.agencyinfo': {
            'Meta': {'object_name': 'AgencyInfo'},
            'fare_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'timezone': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'mtta.fare': {
            'Meta': {'object_name': 'Fare'},
            'cost': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_name_ipattern': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'mtta.feedinfo': {
            'Meta': {'object_name': 'FeedInfo'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        u'mtta.line': {
            'Meta': {'ordering': "('line_id',)", 'unique_together': "(('signup', 'line_id'),)", 'object_name': 'Line'},
            'attributes': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            'fare': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Fare']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_abbr': ('django.db.models.fields.CharField', [], {'max_length': '8', 'db_index': 'True'}),
            'line_color': ('django.db.models.fields.IntegerField', [], {}),
            'line_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'line_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'line_type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.SignUp']"})
        },
        u'mtta.linedirection': {
            'Meta': {'ordering': "('linedir_id',)", 'unique_together': "(('linedir_id', 'line'),)", 'object_name': 'LineDirection'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Line']"}),
            'linedir_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'mtta.node': {
            'Meta': {'ordering': "('node_id',)", 'object_name': 'Node'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'node_abbr': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'node_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'node_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.SignUp']"}),
            'stops': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'nodes'", 'symmetrical': 'False', 'to': u"orm['mtta.Stop']"})
        },
        u'mtta.pattern': {
            'Meta': {'unique_together': "(('linedir', 'pattern_id'),)", 'object_name': 'Pattern'},
            'fixed_pattern': ('django.db.models.fields.TextField', [], {'default': "'[]'", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linedir': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.LineDirection']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'pattern_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'raw_pattern': ('django.db.models.fields.TextField', [], {'default': "'[]'"})
        },
        u'mtta.service': {
            'Meta': {'ordering': "('signup', 'service_id')", 'unique_together': "(('signup', 'service_id'),)", 'object_name': 'Service'},
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'friday': ('django.db.models.fields.BooleanField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'monday': ('django.db.models.fields.BooleanField', [], {}),
            'saturday': ('django.db.models.fields.BooleanField', [], {}),
            'service_id': ('django.db.models.fields.IntegerField', [], {}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.SignUp']", 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'sunday': ('django.db.models.fields.BooleanField', [], {}),
            'thursday': ('django.db.models.fields.BooleanField', [], {}),
            'tuesday': ('django.db.models.fields.BooleanField', [], {}),
            'wednesday': ('django.db.models.fields.BooleanField', [], {})
        },
        u'mtta.serviceexception': {
            'Meta': {'object_name': 'ServiceException'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'exception_type': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Service']"})
        },
        u'mtta.shapeattribute': {
            'Meta': {'object_name': 'ShapeAttribute'},
            'attributes': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.SignUp']"})
        },
        u'mtta.signup': {
            'Meta': {'object_name': 'SignUp'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'feeds': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['multigtfs.Feed']", 'through': u"orm['mtta.SignupExport']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'mtta.signupexport': {
            'Meta': {'object_name': 'SignupExport'},
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['multigtfs.Feed']"}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.SignUp']"}),
            'started': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'mtta.stop': {
            'Meta': {'ordering': "('signup', 'stop_id')", 'unique_together': "(('signup', 'stop_id'),)", 'object_name': 'Stop'},
            'attributes': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            'facing_dir': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_service': ('django.db.models.fields.BooleanField', [], {}),
            'lat': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '8'}),
            'lon': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '8'}),
            'node_abbr': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.SignUp']"}),
            'site_name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'stop_abbr': ('django.db.models.fields.CharField', [], {'max_length': '8', 'db_index': 'True'}),
            'stop_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'stop_name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'mtta.stopbyline': {
            'Meta': {'ordering': "('linedir', 'seq')", 'unique_together': "(('stop', 'linedir', 'seq'),)", 'object_name': 'StopByLine'},
            'attributes': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linedir': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.LineDirection']"}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Node']", 'null': 'True', 'blank': 'True'}),
            'seq': ('django.db.models.fields.IntegerField', [], {}),
            'stop': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Stop']"})
        },
        u'mtta.stopbypattern': {
            'Meta': {'ordering': "('pattern', 'seq')", 'unique_together': "(('stop', 'linedir', 'pattern', 'seq'),)", 'object_name': 'StopByPattern'},
            'attributes': ('django.db.models.fields.TextField', [], {'default': "'[]'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linedir': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.LineDirection']"}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Node']", 'null': 'True', 'blank': 'True'}),
            'pattern': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Pattern']"}),
            'seq': ('django.db.models.fields.IntegerField', [], {}),
            'stop': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Stop']"})
        },
        u'mtta.transfer': {
            'Meta': {'object_name': 'Transfer'},
            'from_stop': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transfer_from_set'", 'to': u"orm['mtta.Stop']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'min_transfer_time': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'signup': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.SignUp']"}),
            'to_stop': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transfer_to_set'", 'to': u"orm['mtta.Stop']"}),
            'transfer_type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'})
        },
        u'mtta.trip': {
            'Meta': {'ordering': "('tripday', 'seq', 'pattern')", 'unique_together': "(('tripday', 'seq', 'pattern'),)", 'object_name': 'Trip'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pattern': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Pattern']"}),
            'seq': ('django.db.models.fields.IntegerField', [], {}),
            'tripday': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.TripDay']"})
        },
        u'mtta.tripday': {
            'Meta': {'ordering': "('linedir', 'service')", 'unique_together': "(('linedir', 'service'),)", 'object_name': 'TripDay'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linedir': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.LineDirection']"}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Service']"})
        },
        u'mtta.tripstop': {
            'Meta': {'ordering': "('tripday', 'seq')", 'unique_together': "(('tripday', 'seq'),)", 'object_name': 'TripStop'},
            'arrival': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'departure'", 'unique': 'True', 'null': 'True', 'to': u"orm['mtta.TripStop']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Node']", 'null': 'True', 'blank': 'True'}),
            'node_abbr': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
            'scheduled': ('django.db.models.fields.BooleanField', [], {}),
            'seq': ('django.db.models.fields.IntegerField', [], {}),
            'stop': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Stop']", 'null': 'True', 'blank': 'True'}),
            'stop_abbr': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'tripday': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.TripDay']"})
        },
        u'mtta.triptime': {
            'Meta': {'ordering': "('trip', 'tripstop', 'time')", 'unique_together': "(('trip', 'tripstop'),)", 'object_name': 'TripTime'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'trip': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.Trip']"}),
            'tripstop': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mtta.TripStop']"})
        },
        'multigtfs.feed': {
            'Meta': {'object_name': 'Feed', 'db_table': "'feed'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['mtta']