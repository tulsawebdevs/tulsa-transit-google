import StringIO

from django.test import TestCase
import mox

from mtta.models import (
    SignUp, Line, LineDirection, Pattern, Stop, Node, StopByLine,
    StopByPattern, Service, TripDay, TripStop, Trip, TripTime)
import mtta.models


class TripDayTest(TestCase):

    def setUp(self):
        self.mox = mox.Mox()
        self.signup = SignUp.objects.create(name=SignUp._unset_name)
        self.service = Service.objects.create(
            signup=self.signup, service_id=1, monday=True, tuesday=True,
            wednesday=True, thursday=True, friday=True, saturday=False,
            sunday=False, start_date='2012-09-20', end_date='2013-12-31')
        self.schedules = dict()
        self.lines = dict()
        self.linedirs = dict()
        self.patterns = dict()
        self.stops = dict()
        self.nodes = dict()
        self.mox.StubOutWithMock(mtta.models, 'mockable_open')

    def tearDown(self):
        self.mox.UnsetStubs()

    def setup_100(self):
        '''Setup sample of Aug 2012 100

        A regular line with all stops in the StopByLine table
        '''
        self.schedules['100'] = """\
Stop Trips
~~~~~~~~~~

SignUp:       TEST SEP 2012
Service:      1
Line:         100
Exception:    Off
Printed:      09-09-2012 17:08

Direction:    To Downtown

Pattern      123Ar            Adm/MemE
          Arch124a   Adm106p    AdmMem
~~~~~~~  ~~~~~~~~~  ~~~~~~~~  ~~~~~~~~

     01       7:00      7:30      8:00

"""
        self.lines['100'] = self.signup.line_set.create(
            line_id=2893, line_abbr=100, line_name='Admiral',
            line_color=12910532, line_type='FX')
        self.linedirs['100-0'] = self.lines['100'].linedirection_set.create(
            linedir_id=28930, name='To Downtown')
        self.patterns['100-01'] = self.linedirs['100-0'].pattern_set.create(
            name='01', pattern_id=11431, raw_pattern=[[300, 500]])

        # 123Ar/Arch124a - Timing node
        self.stops[5498] = self.signup.stop_set.create(
            stop_id=5498, stop_abbr='Arch124a',
            node_abbr='123ARCH', lon='-95.83969', lat='36.162776',
            stop_name='E Archer St&N 124th E Ave/N 123Rd E', in_service=True)
        self.nodes[635] = self.signup.node_set.create(
            node_id=635, abbr='123Ar', name='123rd E/Archer')
        self.nodes[635].stops.add(self.stops[5498])
        self.linedirs['100-0'].stopbyline_set.create(
            stop=self.stops[5498], node=self.nodes[635], seq=1)
        self.patterns['100-01'].stopbypattern_set.create(
            stop=self.stops[5498], node=self.nodes[635], seq=1,
            linedir=self.linedirs['100-0'])

        # Adm106p - Stop
        self.stops[5440] = self.signup.stop_set.create(
            stop_id=5440, stop_abbr='Adm106p',
            lat='36.160832', lon='-95.858432',
            stop_name='E Admiral Pl&N 106th E Pl/S 106Th E', in_service=True)
        self.linedirs['100-0'].stopbyline_set.create(
            stop=self.stops[5440], seq=2)
        self.patterns['100-01'].stopbypattern_set.create(
            stop=self.stops[5440], seq=2, linedir=self.linedirs['100-0'])

        # Adm/MemE / AdmMem - Timing Node
        self.stops[5478] = self.signup.stop_set.create(
            stop_id=5478, stop_abbr='AdmMem',
            site_name='Phillips 66', node_abbr='ADM/MEME',
            lon='-95.887364', lat='36.160834',
            stop_name='E Admiral Pl&N Memorial Dr/S Memori', in_service=True)
        self.nodes[736] = self.signup.node_set.create(
            node_id=736, abbr='Adm/MemE', name='ADMIRAL PL/MEMORIAL P W-NW')
        self.nodes[736].stops.add(self.stops[5478])
        self.linedirs['100-0'].stopbyline_set.create(
            stop=self.stops[5478], node=self.nodes[736], seq=3)
        self.patterns['100-01'].stopbypattern_set.create(
            stop=self.stops[5478], node=self.nodes[736], seq=3,
            linedir=self.linedirs['100-0'])

    def assert_expected_trip_object_counts_100(self):
        self.assertEqual(
            Service.objects.filter(signup=self.signup).count(), 1)
        self.assertEqual(TripDay.objects.count(), 1)
        self.assertEqual(TripStop.objects.count(), 3)
        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(TripTime.objects.count(), 3)

    def test_import_100_basic(self):
        self.setup_100()
        mtta.models.mockable_open(
            '100.txt').AndReturn(StringIO.StringIO(self.schedules['100']))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, '100.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts_100()
        service = Service.objects.get(signup=self.signup)
        self.assertEqual(service.service_id, 1)
        tripday = TripDay.objects.get()
        self.assertEqual(tripday.linedir, self.linedirs['100-0'])
        self.assertEqual(tripday.service, service)
        ts0, ts1, ts2 = TripStop.objects.all()
        self.assertEqual(ts0.seq, 0)
        self.assertEqual(ts0.tripday, tripday)
        self.assertEqual(ts0.stop, self.stops[5498])
        self.assertEqual(ts0.node, self.nodes[635])
        self.assertEqual(ts1.seq, 1)
        self.assertEqual(ts1.tripday, tripday)
        self.assertEqual(ts1.stop, self.stops[5440])
        self.assertEqual(ts1.node, None)
        self.assertEqual(ts2.tripday, tripday)
        self.assertEqual(ts2.seq, 2)
        self.assertEqual(ts2.stop, self.stops[5478])
        self.assertEqual(ts2.node, self.nodes[736])
        trip = Trip.objects.get()
        self.assertEqual(trip.seq, 0)
        self.assertEqual(trip.tripday, tripday)
        self.assertEqual(trip.pattern, self.patterns['100-01'])
        tt0, tt1, tt2 = TripTime.objects.all()
        self.assertEqual(tt0.trip, trip)
        self.assertEqual(tt0.tripstop, ts0)
        self.assertEqual(tt0.time, '7:00')
        self.assertEqual(tt1.trip, trip)
        self.assertEqual(tt1.tripstop, ts1)
        self.assertEqual(tt1.time, '7:30')
        self.assertEqual(tt2.trip, trip)
        self.assertEqual(tt2.tripstop, ts2)
        self.assertEqual(tt2.time, '8:00')

    def test_import_schedule_100_node_on_stop(self):
        '''The import succeeds if the node abbr is on the stop instead'''
        self.setup_100()
        stop1 = self.stops[5498]
        stop1.node_abbr = '123Ar'
        stop1.save()
        StopByLine.objects.filter(stop=stop1).update(node=None)
        mtta.models.mockable_open(
            '100.txt').AndReturn(StringIO.StringIO(self.schedules['100']))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, '100.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts_100()
        ts0, ts1, ts2 = TripStop.objects.all()
        self.assertEqual(ts0.stop, stop1)
        self.assertEqual(ts0.node, None)
        self.assertEqual(ts2.stop, self.stops[5478])
        self.assertEqual(ts2.node, self.nodes[736])

    def test_import_schedule_sbl_is_just_nodes_two_candidates(self):
        '''
        StopByPattern is just nodes, a stop-only column has two matches.
        The import succeeds, but there is no assigned stop, and the column
        won't be exported.

        In Aug 2012 signup, 508 was just nodes, but some stops were ambiguous
        '''
        self.setup_100()
        stop2 = self.stops[5440]
        StopByLine.objects.filter(stop=stop2).delete()
        StopByPattern.objects.filter(stop=stop2).delete()
        stop3 = self.stops[5478]
        StopByLine.objects.filter(stop=stop3).update(seq=2)
        stop4 = Stop.objects.create(
            signup=self.signup, stop_id=stop2.stop_id + 1,
            stop_abbr=stop2.stop_abbr, site_name=stop2.site_name,
            lon=stop2.lon, lat=stop2.lat, stop_name=stop2.stop_name,
            in_service=True)
        mtta.models.mockable_open(
            '100.txt').AndReturn(StringIO.StringIO(self.schedules['100']))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, '100.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts_100()
        ts1 = TripStop.objects.get(seq=1)
        self.assertEqual(ts1.stop, None)

    def test_import_schedule_sbl_is_just_nodes_one_in_service_candidate(self):
        '''
        StopByPattern is nodes, a stop-only column has one in-service option.
        The in-service stop is assigned, and the column will be exported.

        In Aug 2012 signup, 508 was just nodes, but some stops were ambiguous
        '''
        self.setup_100()
        stop2 = self.stops[5440]
        StopByLine.objects.filter(stop=stop2).delete()
        StopByPattern.objects.filter(stop=stop2).delete()
        stop3 = self.stops[5478]
        StopByLine.objects.filter(stop=stop3).update(seq=2)
        stop4 = Stop.objects.create(
            signup=self.signup, stop_id=stop2.stop_id + 1,
            stop_abbr=stop2.stop_abbr, site_name=stop2.site_name,
            lon=stop2.lon, lat=stop2.lat, stop_name=stop2.stop_name,
            in_service=False)

        mtta.models.mockable_open(
            '100.txt').AndReturn(StringIO.StringIO(self.schedules['100']))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, '100.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts_100()
        ts1 = TripStop.objects.get(seq=1)
        self.assertEqual(ts1.stop, stop2)

    def test_import_schedule_100_sbl_is_just_nodes(self):
        '''
        The import succeeds if the StopByLine is just nodes

        In Aug 2012 signup, 508 was just nodes, but some stops were unique
        '''
        self.setup_100()
        stop2 = self.stops[5440]
        StopByLine.objects.filter(stop=stop2).delete()
        StopByPattern.objects.filter(stop=stop2).delete()
        stop3 = self.stops[5478]
        StopByLine.objects.filter(stop=stop3).update(seq=2)
        mtta.models.mockable_open(
            '100.txt').AndReturn(StringIO.StringIO(self.schedules['100']))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, '100.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts_100()
        tripday = TripDay.objects.get()
        ts0, ts1, ts2 = TripStop.objects.all()
        self.assertEqual(ts0.stop, self.stops[5498])
        self.assertEqual(ts0.node, self.nodes[635])
        self.assertEqual(ts1.seq, 1)
        self.assertEqual(ts1.tripday, tripday)
        self.assertEqual(ts1.stop, stop2)
        self.assertEqual(ts1.node, None)
        self.assertEqual(ts2.tripday, tripday)
        self.assertEqual(ts2.seq, 2)
        self.assertEqual(ts2.stop, stop3)
        self.assertEqual(ts2.node, self.nodes[736])

    def test_import_schedule_sbl_has_wrong_nodes(self):
        '''
        StopByLine has a bad node, but the stop is found

        In Aug 2012 signup, 508 was just nodes, and wrong
        '''
        self.setup_100()
        stop2 = self.stops[5440]
        StopByLine.objects.filter(stop=stop2).delete()
        StopByPattern.objects.filter(stop=stop2).delete()
        stop3 = self.stops[5478]
        StopByLine.objects.filter(stop=stop3).update(seq=2)
        schedule = self.schedules['100'].replace('Adm/MemE', 'ADMMEM')
        mtta.models.mockable_open(
            '100.txt').AndReturn(StringIO.StringIO(schedule))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, '100.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts_100()
        tripday = TripDay.objects.get()
        ts0, ts1, ts2 = TripStop.objects.all()
        self.assertEqual(ts0.stop, self.stops[5498])
        self.assertEqual(ts0.node, self.nodes[635])
        self.assertEqual(ts1.seq, 1)
        self.assertEqual(ts1.tripday, tripday)
        self.assertEqual(ts1.stop, stop2)
        self.assertEqual(ts1.node, None)
        self.assertEqual(ts2.tripday, tripday)
        self.assertEqual(ts2.seq, 2)
        self.assertEqual(ts2.stop, stop3)
        self.assertEqual(ts2.node, None)

    def test_import_schedule_flex(self):
        '''Schedule NNN matches NNNFLEX, like 508 -> 508FLEX'''
        self.setup_100()
        line = self.lines['100']
        line.line_abbr = '100FLEX'
        line.save()
        mtta.models.mockable_open(
            '100.txt').AndReturn(StringIO.StringIO(self.schedules['100']))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, '100.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts_100()

    def test_import_schedule_sflx(self):
        '''Schedule NNNS matches NNNSFLX, like 860S -> 860SFLX'''
        self.setup_100()
        schedule = self.schedules['100'].replace(
            'Line:         100', 'Line:         100S')
        line = self.lines['100']
        line.line_abbr = '100SFLX'
        line.save()
        mtta.models.mockable_open(
            '100.txt').AndReturn(StringIO.StringIO(schedule))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, '100.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts_100()
