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
        self.stop1 = Stop.objects.create(
            signup=self.signup, stop_id=5498, stop_abbr='Arch124a',
            node_abbr='123ARCH', lon='-95.83969', lat='36.162776',
            stop_name='E Archer St&N 124th E Ave/N 123Rd E', in_service=True)
        self.stop2 = Stop.objects.create(
            signup=self.signup, stop_id=5440, stop_abbr='Adm106p',
            lat='36.160832', lon='-95.858432',
            stop_name='E Admiral Pl&N 106th E Pl/S 106Th E', in_service=True)
        self.stop3 = Stop.objects.create(
            signup=self.signup, stop_id=5478, stop_abbr='AdmMem',
            site_name='Phillips 66', node_abbr='ADM/MEME',
            lon='-95.887364', lat='36.160834',
            stop_name='E Admiral Pl&N Memorial Dr/S Memori', in_service=True)
        self.line100 = Line.objects.create(
            signup=self.signup, line_id=2893, line_abbr=100,
            line_name='Admiral', line_color=12910532, line_type='FX')
        self.line100dir0 = LineDirection.objects.create(
            line=self.line100, linedir_id=28930, name='To Downtown')
        self.node1 = Node.objects.create(
            node_id=635, abbr='123Ar', name='123rd E/Archer')
        self.node1.stops.add(self.stop1)
        self.node3 = Node.objects.create(
            node_id=736, abbr='Adm/MemE', name='ADMIRAL PL/MEMORIAL P W-NW')
        self.node3.stops.add(self.stop3)
        self.sbl1 = StopByLine.objects.create(
            linedir=self.line100dir0, stop=self.stop1, node=self.node1, seq=1)
        self.sbl2 = StopByLine.objects.create(
            linedir=self.line100dir0, stop=self.stop2, seq=2)
        self.sbl3 = StopByLine.objects.create(
            linedir=self.line100dir0, stop=self.stop3, node=self.node3, seq=3)
        self.pattern = Pattern.objects.create(
            linedir=self.line100dir0, name='01', pattern_id=11431,
            raw_pattern=[[300, 500]])
        self.schedule =     """\
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
        self.mox.StubOutWithMock(mtta.models, 'mockable_open')

    def tearDown(self):
        self.mox.UnsetStubs()
    
    def assert_expected_trip_object_counts(self):
        self.assertEqual(Service.objects.count(), 1)
        self.assertEqual(TripDay.objects.count(), 1)
        self.assertEqual(TripStop.objects.count(), 3)
        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(TripTime.objects.count(), 3)

    def test_import_schedule_basic(self):
        mtta.models.mockable_open(
            'test.txt').AndReturn(StringIO.StringIO(self.schedule))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, 'test.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts()
        service = Service.objects.get()
        self.assertEqual(service.service_id, 1)
        tripday = TripDay.objects.get()
        self.assertEqual(tripday.linedir, self.line100dir0)
        self.assertEqual(tripday.service, service)
        ts0, ts1, ts2 = TripStop.objects.all()
        self.assertEqual(ts0.seq, 0)
        self.assertEqual(ts0.tripday, tripday)
        self.assertEqual(ts0.stop, self.stop1)
        self.assertEqual(ts0.node, self.node1)
        self.assertEqual(ts1.seq, 1)
        self.assertEqual(ts1.tripday, tripday)
        self.assertEqual(ts1.stop, self.stop2)
        self.assertEqual(ts1.node, None)
        self.assertEqual(ts2.tripday, tripday)
        self.assertEqual(ts2.seq, 2)
        self.assertEqual(ts2.stop, self.stop3)
        self.assertEqual(ts2.node, self.node3)
        trip = Trip.objects.get()
        self.assertEqual(trip.seq, 0)
        self.assertEqual(trip.tripday, tripday)
        self.assertEqual(trip.pattern, self.pattern)
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

    def test_import_schedule_node_on_stop(self):
        '''The import succeeds if the node abbr is on the stop instead'''
        self.stop1.node_abbr = '123Ar'
        self.stop1.save()
        self.sbl1.node = None
        self.sbl1.save()
        mtta.models.mockable_open(
            'test.txt').AndReturn(StringIO.StringIO(self.schedule))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, 'test.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts()
        ts0, ts1, ts2 = TripStop.objects.all()
        self.assertEqual(ts0.stop, self.stop1)
        self.assertEqual(ts0.node, None)
        self.assertEqual(ts2.stop, self.stop3)
        self.assertEqual(ts2.node, self.node3)

    def test_import_schedule_sbl_is_just_nodes_two_candidates(self):
        '''
        StopByPattern is just nodes, a stop-only column has two matches.
        The import succeeds, but there is no assigned stop, and the column
        won't be exported.
        
        In Aug 2012 signup, 508 was just nodes, but some stops were ambiguous
        '''
        self.sbl2.delete()
        self.sbl3.seq = 2
        self.sbl3.save()
        stop4 = Stop.objects.create(
            signup=self.signup, stop_id=self.stop2.stop_id + 1,
            stop_abbr=self.stop2.stop_abbr, site_name=self.stop2.site_name,
            lon=self.stop2.lon, lat=self.stop2.lat,
            stop_name=self.stop2.stop_name, in_service=True)
        
        mtta.models.mockable_open(
            'test.txt').AndReturn(StringIO.StringIO(self.schedule))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, 'test.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts()
        ts1 = TripStop.objects.get(seq=1)
        self.assertEqual(ts1.stop, None)

    def test_import_schedule_sbl_is_just_nodes_one_in_service_candidate(self):
        '''
        StopByPattern is nodes, a stop-only column has one in-service option.
        The in-service stop is assigned, and the column will be exported.
        
        In Aug 2012 signup, 508 was just nodes, but some stops were ambiguous
        '''
        self.sbl2.delete()
        self.sbl3.seq = 2
        self.sbl3.save()
        stop4 = Stop.objects.create(
            signup=self.signup, stop_id=self.stop2.stop_id + 1,
            stop_abbr=self.stop2.stop_abbr, site_name=self.stop2.site_name,
            lon=self.stop2.lon, lat=self.stop2.lat,
            stop_name=self.stop2.stop_name, in_service=False)

        mtta.models.mockable_open(
            'test.txt').AndReturn(StringIO.StringIO(self.schedule))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, 'test.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts()
        ts1 = TripStop.objects.get(seq=1)
        self.assertEqual(ts1.stop, self.stop2)

    def test_import_schedule_sbl_is_just_nodes(self):
        '''
        The import succeeds if the StopByLine is just nodes
        
        In Aug 2012 signup, 508 was just nodes, but some stops were unique
        '''
        self.sbl2.delete()
        self.sbl3.seq = 2
        self.sbl3.save()
        mtta.models.mockable_open(
            'test.txt').AndReturn(StringIO.StringIO(self.schedule))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, 'test.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts()
        tripday = TripDay.objects.get()
        ts0, ts1, ts2 = TripStop.objects.all()
        self.assertEqual(ts0.stop, self.stop1)
        self.assertEqual(ts0.node, self.node1)
        self.assertEqual(ts1.seq, 1)
        self.assertEqual(ts1.tripday, tripday)
        self.assertEqual(ts1.stop, self.stop2)
        self.assertEqual(ts1.node, None)
        self.assertEqual(ts2.tripday, tripday)
        self.assertEqual(ts2.seq, 2)
        self.assertEqual(ts2.stop, self.stop3)
        self.assertEqual(ts2.node, self.node3)

    def test_import_schedule_sbl_has_wrong_nodes(self):
        '''
        StopByLine has a bad node, but the stop is found

        In Aug 2012 signup, 508 was just nodes, and wrong
        '''
        self.sbl2.delete()
        self.sbl3.seq = 2
        self.sbl3.save()
        self.schedule = self.schedule.replace('Adm/MemE', 'ADMMEM')
        mtta.models.mockable_open(
            'test.txt').AndReturn(StringIO.StringIO(self.schedule))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, 'test.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts()
        tripday = TripDay.objects.get()
        ts0, ts1, ts2 = TripStop.objects.all()
        self.assertEqual(ts0.stop, self.stop1)
        self.assertEqual(ts0.node, self.node1)
        self.assertEqual(ts1.seq, 1)
        self.assertEqual(ts1.tripday, tripday)
        self.assertEqual(ts1.stop, self.stop2)
        self.assertEqual(ts1.node, None)
        self.assertEqual(ts2.tripday, tripday)
        self.assertEqual(ts2.seq, 2)
        self.assertEqual(ts2.stop, self.stop3)
        self.assertEqual(ts2.node, None)

    def test_import_schedule_flex(self):
        '''Schedule NNN matches NNNFLEX, like 508 -> 508FLEX'''
        self.schedule = self.schedule.replace(
            'Line:         100', 'Line:         100S')
        self.line100.line_abbr = '100SFLX'
        self.line100.save()
        mtta.models.mockable_open(
            'test.txt').AndReturn(StringIO.StringIO(self.schedule))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, 'test.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts()

    def test_import_schedule_sflx(self):
        '''Schedule NNNS matches NNNSFLX, like 860S -> 860SFLX'''
        self.schedule = self.schedule.replace(
            'Line:         100', 'Line:         100S')
        self.line100.line_abbr = '100SFLX'
        self.line100.save()
        mtta.models.mockable_open(
            'test.txt').AndReturn(StringIO.StringIO(self.schedule))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, 'test.txt')
        self.mox.VerifyAll()
        self.assert_expected_trip_object_counts()
