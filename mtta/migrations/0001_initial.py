# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SignUp'
        db.create_table('mtta_signup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('mtta', ['SignUp'])

        # Adding model 'SignupExport'
        db.create_table('mtta_signupexport', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('signup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.SignUp'])),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['multigtfs.Feed'])),
            ('started', self.gf('django.db.models.fields.DateTimeField')()),
            ('finished', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('mtta', ['SignupExport'])

        # Adding model 'ShapeAttribute'
        db.create_table('mtta_shapeattribute', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('signup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.SignUp'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('attributes', self.gf('django.db.models.fields.TextField')(default=[])),
        ))
        db.send_create_signal('mtta', ['ShapeAttribute'])

        # Adding model 'AgencyInfo'
        db.create_table('mtta_agencyinfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('timezone', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('lang', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('fare_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('mtta', ['AgencyInfo'])

        # Adding model 'FeedInfo'
        db.create_table('mtta_feedinfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('lang', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
        ))
        db.send_create_signal('mtta', ['FeedInfo'])

        # Adding model 'Line'
        db.create_table('mtta_line', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('attributes', self.gf('django.db.models.fields.TextField')(default=[])),
            ('signup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.SignUp'])),
            ('line_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('line_abbr', self.gf('django.db.models.fields.CharField')(max_length=8, db_index=True)),
            ('line_name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('line_color', self.gf('django.db.models.fields.IntegerField')()),
            ('line_type', self.gf('django.db.models.fields.CharField')(max_length=2)),
        ))
        db.send_create_signal('mtta', ['Line'])

        # Adding unique constraint on 'Line', fields ['signup', 'line_id']
        db.create_unique('mtta_line', ['signup_id', 'line_id'])

        # Adding model 'LineDirection'
        db.create_table('mtta_linedirection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('linedir_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('line', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Line'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('mtta', ['LineDirection'])

        # Adding unique constraint on 'LineDirection', fields ['linedir_id', 'line']
        db.create_unique('mtta_linedirection', ['linedir_id', 'line_id'])

        # Adding model 'Pattern'
        db.create_table('mtta_pattern', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pattern_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('linedir', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.LineDirection'])),
            ('raw_pattern', self.gf('django.db.models.fields.TextField')(default=[])),
            ('fixed_pattern', self.gf('django.db.models.fields.TextField')(default=[], blank=True)),
        ))
        db.send_create_signal('mtta', ['Pattern'])

        # Adding unique constraint on 'Pattern', fields ['linedir', 'pattern_id']
        db.create_unique('mtta_pattern', ['linedir_id', 'pattern_id'])

        # Adding model 'Stop'
        db.create_table('mtta_stop', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('attributes', self.gf('django.db.models.fields.TextField')(default=[])),
            ('signup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.SignUp'])),
            ('stop_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('stop_abbr', self.gf('django.db.models.fields.CharField')(max_length=8, db_index=True)),
            ('stop_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('node_abbr', self.gf('django.db.models.fields.CharField')(max_length=8, blank=True)),
            ('site_name', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('facing_dir', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
            ('lat', self.gf('django.db.models.fields.DecimalField')(max_digits=13, decimal_places=8)),
            ('lon', self.gf('django.db.models.fields.DecimalField')(max_digits=13, decimal_places=8)),
            ('in_service', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('mtta', ['Stop'])

        # Adding unique constraint on 'Stop', fields ['signup', 'stop_id']
        db.create_unique('mtta_stop', ['signup_id', 'stop_id'])

        # Adding model 'Node'
        db.create_table('mtta_node', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('signup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.SignUp'])),
            ('node_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('node_abbr', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('node_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('mtta', ['Node'])

        # Adding M2M table for field stops on 'Node'
        db.create_table('mtta_node_stops', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('node', models.ForeignKey(orm['mtta.node'], null=False)),
            ('stop', models.ForeignKey(orm['mtta.stop'], null=False))
        ))
        db.create_unique('mtta_node_stops', ['node_id', 'stop_id'])

        # Adding model 'StopByLine'
        db.create_table('mtta_stopbyline', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('attributes', self.gf('django.db.models.fields.TextField')(default=[])),
            ('stop', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Stop'])),
            ('linedir', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.LineDirection'])),
            ('seq', self.gf('django.db.models.fields.IntegerField')()),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Node'], null=True, blank=True)),
        ))
        db.send_create_signal('mtta', ['StopByLine'])

        # Adding unique constraint on 'StopByLine', fields ['stop', 'linedir', 'seq']
        db.create_unique('mtta_stopbyline', ['stop_id', 'linedir_id', 'seq'])

        # Adding model 'StopByPattern'
        db.create_table('mtta_stopbypattern', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('attributes', self.gf('django.db.models.fields.TextField')(default=[])),
            ('stop', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Stop'])),
            ('linedir', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.LineDirection'])),
            ('pattern', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Pattern'])),
            ('seq', self.gf('django.db.models.fields.IntegerField')()),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Node'], null=True, blank=True)),
        ))
        db.send_create_signal('mtta', ['StopByPattern'])

        # Adding unique constraint on 'StopByPattern', fields ['stop', 'linedir', 'pattern', 'seq']
        db.create_unique('mtta_stopbypattern', ['stop_id', 'linedir_id', 'pattern_id', 'seq'])

        # Adding model 'Service'
        db.create_table('mtta_service', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('signup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.SignUp'], null=True, blank=True)),
            ('service_id', self.gf('django.db.models.fields.IntegerField')()),
            ('monday', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('tuesday', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('wednesday', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('thursday', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('friday', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('saturday', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('sunday', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('start_date', self.gf('django.db.models.fields.DateField')()),
            ('end_date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('mtta', ['Service'])

        # Adding unique constraint on 'Service', fields ['signup', 'service_id']
        db.create_unique('mtta_service', ['signup_id', 'service_id'])

        # Adding model 'ServiceException'
        db.create_table('mtta_serviceexception', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Service'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('exception_type', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('mtta', ['ServiceException'])

        # Adding model 'TripDay'
        db.create_table('mtta_tripday', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('linedir', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.LineDirection'])),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Service'])),
        ))
        db.send_create_signal('mtta', ['TripDay'])

        # Adding unique constraint on 'TripDay', fields ['linedir', 'service']
        db.create_unique('mtta_tripday', ['linedir_id', 'service_id'])

        # Adding model 'TripStop'
        db.create_table('mtta_tripstop', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tripday', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.TripDay'])),
            ('stop', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Stop'], null=True, blank=True)),
            ('stop_abbr', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Node'], null=True, blank=True)),
            ('node_abbr', self.gf('django.db.models.fields.CharField')(max_length=8, blank=True)),
            ('seq', self.gf('django.db.models.fields.IntegerField')()),
            ('scheduled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('arrival', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='departure', unique=True, null=True, to=orm['mtta.TripStop'])),
        ))
        db.send_create_signal('mtta', ['TripStop'])

        # Adding unique constraint on 'TripStop', fields ['tripday', 'seq']
        db.create_unique('mtta_tripstop', ['tripday_id', 'seq'])

        # Adding model 'Trip'
        db.create_table('mtta_trip', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tripday', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.TripDay'])),
            ('pattern', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Pattern'])),
            ('seq', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('mtta', ['Trip'])

        # Adding unique constraint on 'Trip', fields ['tripday', 'seq', 'pattern']
        db.create_unique('mtta_trip', ['tripday_id', 'seq', 'pattern_id'])

        # Adding model 'TripTime'
        db.create_table('mtta_triptime', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('trip', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.Trip'])),
            ('tripstop', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mtta.TripStop'])),
            ('time', self.gf('django.db.models.fields.CharField')(max_length=5)),
        ))
        db.send_create_signal('mtta', ['TripTime'])

        # Adding unique constraint on 'TripTime', fields ['trip', 'tripstop']
        db.create_unique('mtta_triptime', ['trip_id', 'tripstop_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'TripTime', fields ['trip', 'tripstop']
        db.delete_unique('mtta_triptime', ['trip_id', 'tripstop_id'])

        # Removing unique constraint on 'Trip', fields ['tripday', 'seq', 'pattern']
        db.delete_unique('mtta_trip', ['tripday_id', 'seq', 'pattern_id'])

        # Removing unique constraint on 'TripStop', fields ['tripday', 'seq']
        db.delete_unique('mtta_tripstop', ['tripday_id', 'seq'])

        # Removing unique constraint on 'TripDay', fields ['linedir', 'service']
        db.delete_unique('mtta_tripday', ['linedir_id', 'service_id'])

        # Removing unique constraint on 'Service', fields ['signup', 'service_id']
        db.delete_unique('mtta_service', ['signup_id', 'service_id'])

        # Removing unique constraint on 'StopByPattern', fields ['stop', 'linedir', 'pattern', 'seq']
        db.delete_unique('mtta_stopbypattern', ['stop_id', 'linedir_id', 'pattern_id', 'seq'])

        # Removing unique constraint on 'StopByLine', fields ['stop', 'linedir', 'seq']
        db.delete_unique('mtta_stopbyline', ['stop_id', 'linedir_id', 'seq'])

        # Removing unique constraint on 'Stop', fields ['signup', 'stop_id']
        db.delete_unique('mtta_stop', ['signup_id', 'stop_id'])

        # Removing unique constraint on 'Pattern', fields ['linedir', 'pattern_id']
        db.delete_unique('mtta_pattern', ['linedir_id', 'pattern_id'])

        # Removing unique constraint on 'LineDirection', fields ['linedir_id', 'line']
        db.delete_unique('mtta_linedirection', ['linedir_id', 'line_id'])

        # Removing unique constraint on 'Line', fields ['signup', 'line_id']
        db.delete_unique('mtta_line', ['signup_id', 'line_id'])

        # Deleting model 'SignUp'
        db.delete_table('mtta_signup')

        # Deleting model 'SignupExport'
        db.delete_table('mtta_signupexport')

        # Deleting model 'ShapeAttribute'
        db.delete_table('mtta_shapeattribute')

        # Deleting model 'AgencyInfo'
        db.delete_table('mtta_agencyinfo')

        # Deleting model 'FeedInfo'
        db.delete_table('mtta_feedinfo')

        # Deleting model 'Line'
        db.delete_table('mtta_line')

        # Deleting model 'LineDirection'
        db.delete_table('mtta_linedirection')

        # Deleting model 'Pattern'
        db.delete_table('mtta_pattern')

        # Deleting model 'Stop'
        db.delete_table('mtta_stop')

        # Deleting model 'Node'
        db.delete_table('mtta_node')

        # Removing M2M table for field stops on 'Node'
        db.delete_table('mtta_node_stops')

        # Deleting model 'StopByLine'
        db.delete_table('mtta_stopbyline')

        # Deleting model 'StopByPattern'
        db.delete_table('mtta_stopbypattern')

        # Deleting model 'Service'
        db.delete_table('mtta_service')

        # Deleting model 'ServiceException'
        db.delete_table('mtta_serviceexception')

        # Deleting model 'TripDay'
        db.delete_table('mtta_tripday')

        # Deleting model 'TripStop'
        db.delete_table('mtta_tripstop')

        # Deleting model 'Trip'
        db.delete_table('mtta_trip')

        # Deleting model 'TripTime'
        db.delete_table('mtta_triptime')


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