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

    def setup_880F(self):
        '''Setup a sample of the August 880FLEX line

        The 880 has non-timing nodes, and a stop with duplicate stop abbrs
        '''

        self.schedules['880F'] = """\
Stop Trips
~~~~~~~~~~

SignUp:       AUG 2012
Service:      1
Line:         880
Exception:    Off
Printed:      08-21-2012 15:18

Direction:    From Downtown

Pattern    DAS1             6BUE      11PE   11Uti               WHM
          DBAY1   Ch5SB   6stBld   11stPeo   11Uti   Utic12st    WHM
~~~~~~~  ~~~~~~  ~~~~~~  ~~~~~~~  ~~~~~~~~  ~~~~~~  ~~~~~~~~~  ~~~~~

     01   20:00   20:01    20:01     20:06   20:08      20:08  20:43
"""
        self.lines['880F'] = self.signup.line_set.create(
            line_color=8388608, line_name="Southeast Nightline FLEX",
            line_id=2921, line_type="FL", line_abbr="880FLEX")
        self.linedirs['880F-0'] = self.lines['880F'].linedirection_set.create(
            name="From Downtown", linedir_id=29210)
        self.patterns['880F-01'] = self.linedirs['880F-0'].pattern_set.create(
            pattern_id=11562, name='01', raw_pattern=[], fixed_pattern=[])
        # DAS1 / DBAY1 - Timing node
        self.stops[6639] = self.signup.stop_set.create(
            stop_id=6639, site_name="Denver Avenue Station", in_service=True,
            lon='-95.993314', node_abbr="DBAY1", stop_abbr="DBAY1",
            lat='36.151795', stop_name="DAS Bay1")
        self.nodes[738] = self.signup.node_set.create(
            node_id=738, abbr='DAS1', name="DAS BAY 01")
        self.nodes[738].stops.add(self.stops[6639])
        self.linedirs['880F-0'].stopbyline_set.create(
            node=self.nodes[738], stop=self.stops[6639], seq=1)
        self.patterns['880F-01'].stopbypattern_set.create(
            node=self.nodes[738], stop=self.stops[6639], seq=1,
            linedir=self.linedirs['880F-0'])
        # Ch5SB - Stop
        self.stops[3732] = self.signup.stop_set.create(
            stop_id=3732, in_service=True, lon='-95.992378',
            stop_abbr="Ch5SB", lat='36.150491', stop_name="Cheyenne/5th S-SW")
        # 6BUE/6stBld - Non-timing node
        self.stops[6392] = self.signup.stop_set.create(
            stop_id=6392, in_service=True, lon='-95.990804',
            node_abbr="6BUE", stop_abbr="6stBld",
            lat='36.149946', stop_name="W 6Th St&S Boulder Ave")
        self.nodes[856] = self.signup.node_set.create(
            node_id=856, abbr='6BuE', name='6th/Boulder E-SW')
        self.nodes[856].stops.add(self.stops[6392])
        # 11PE/11stPeo - Non-timing node
        self.stops[5109] = self.signup.stop_set.create(
            stop_id=5109, in_service=True, lon='-95.975297',
            node_abbr="11PE", stop_abbr="11stPeo", lat='36.147825',
            stop_name="E 11th St S&S Peoria Ave")
        self.nodes[38] = self.signup.node_set.create(
            node_id=38, abbr='11Pe', name='11th/Peoria')
        self.nodes[38].stops.add(self.stops[5109])
        # 11stPeo - Distracter stop
        self.stops[5032] = self.signup.stop_set.create(
            stop_id=5032, in_service=True, lon='-95.975924',
            stop_abbr="11stPeo", lat='36.147984',
            stop_name="E 11th St S&S Peoria Ave")
        # 11PeWB - Out-of-service stop on same node
        self.stops[579] = self.signup.stop_set.create(
            stop_id=579, in_service=False, lon='-95.975928',
            stop_abbr='11PeWB', lat='36.148119', stop_name='11th/Peoria W-NW')
        self.nodes[38].stops.add(self.stops[579])
        # 11Uti/11Uti - Timing node
        self.stops[4156] = self.signup.stop_set.create(
            stop_id=4156, in_service=True, lon='-95.967461',
            node_abbr="11Uti", stop_abbr="11Uti", lat='36.148139',
            stop_name="11 & Utica")
        self.nodes[705] = self.signup.node_set.create(
            node_id=705, abbr="11Uti", name="11 & Utica")
        self.nodes[705].stops.add(self.stops[4156])
        self.linedirs['880F-0'].stopbyline_set.create(
            stop=self.stops[4156], node=self.nodes[705], seq=2)
        self.patterns['880F-01'].stopbypattern_set.create(
            stop=self.stops[4156], node=self.nodes[705], seq=2,
            linedir=self.linedirs['880F-0'])
        # 11Uti distractor node
        self.stops[5124] = self.signup.stop_set.create(
            stop_id=5124, in_service=True, lon='-95.966769',
            node_abbr="11UTI", stop_abbr="11Utic", lat='36.147773',
            stop_name="E 11th St S&S Utica Ave")
        self.nodes[705].stops.add(self.stops[5124])
        # Utic12st - Non-timing stop with 2 matches
        self.stops[5856] = self.signup.stop_set.create(
            stop_id=5856, site_name="Hill Crest Medical Center",
            in_service=True, lon='-95.967189', stop_abbr="Utic12st",
            lat='36.146219', stop_name="S Utica Ave&E 12th St S")
        self.stops[5857] = self.signup.stop_set.create(
            stop_id=5857, site_name="Benedict Park", in_service=True,
            lon='-95.967205', stop_abbr="Utic12st", lat='36.145453',
            stop_name="S Utica Ave&E 12th St S")
        # WHM/WHM - Timing node
        self.stops[133] = self.signup.stop_set.create(
            stop_id=133, in_service=True, lon='-95.882372', node_abbr="WHM",
            stop_abbr="WHM", lat='36.065248',
            stop_name="Woodland Hills (SEARS)")
        self.nodes[515] = self.signup.node_set.create(
            node_id=133, abbr="WHM", name="Woodland Hills")
        self.nodes[515].stops.add(self.stops[133])
        self.linedirs['880F-0'].stopbyline_set.create(
            stop=self.stops[133], node=self.nodes[515], seq=3)
        self.patterns['880F-01'].stopbypattern_set.create(
            stop=self.stops[133], node=self.nodes[515], seq=3,
            linedir=self.linedirs['880F-0'])

    def assert_expected_trip_object_counts_100(self):
        self.assertEqual(self.signup.service_set.count(), 1)
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
        # 123Ar/Arch124a - Timing node
        self.assertEqual(ts0.seq, 0)
        self.assertEqual(ts0.tripday, tripday)
        self.assertEqual(ts0.stop_abbr, 'Arch124a')
        self.assertEqual(ts0.stop, self.stops[5498])
        self.assertEqual(ts0.node_abbr, '123Ar')
        self.assertEqual(ts0.node, self.nodes[635])
        # Adm106p - Stop
        self.assertEqual(ts1.seq, 1)
        self.assertEqual(ts1.tripday, tripday)
        self.assertEqual(ts1.stop_abbr, 'Adm106p')
        self.assertEqual(ts1.stop, self.stops[5440])
        self.assertEqual(ts1.node_abbr, '')
        self.assertEqual(ts1.node, None)
        # Adm/MemE / AdmMem - Timing Node
        self.assertEqual(ts2.tripday, tripday)
        self.assertEqual(ts2.seq, 2)
        self.assertEqual(ts2.stop_abbr, 'AdmMem')
        self.assertEqual(ts2.stop, self.stops[5478])
        self.assertEqual(ts2.node_abbr, 'Adm/MemE')
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
        line = self.lines['100']
        line.line_type='FL'
        line.save()
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
        line = self.lines['100']
        line.line_type='FL'
        line.save()
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
        line = self.lines['100']
        line.line_type='FL'
        line.save()
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
        line = self.lines['100']
        line.line_type='FL'
        line.save()
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
        self.assertEqual(ts2.node, self.nodes[736])

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

    def test_880F_non_timing_nodes(self):
        '''For some flex lines, nodes are not timing nodes'''
        self.setup_880F()
        mtta.models.mockable_open(
            '880F.txt').AndReturn(StringIO.StringIO(self.schedules['880F']))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, '880F.txt')
        self.mox.VerifyAll()
        service = self.signup.service_set.get()
        tripday = TripDay.objects.get()
        self.assertEqual(tripday.linedir, self.linedirs['880F-0'])
        self.assertEqual(tripday.service, service)
        ts0, ts1, ts2, ts3, ts4, ts5, ts6 = TripStop.objects.all()
        # DAS1 / DBAY1 - Timing node
        self.assertEqual(ts0.seq, 0)
        self.assertEqual(ts0.tripday, tripday)
        self.assertEqual(ts0.stop_abbr, 'DBAY1')
        self.assertEqual(ts0.stop, self.stops[6639])
        self.assertEqual(ts0.node_abbr, 'DAS1')
        self.assertEqual(ts0.node, self.nodes[738])
        # Ch5SB - Non-timing stop
        self.assertEqual(ts1.seq, 1)
        self.assertEqual(ts1.tripday, tripday)
        self.assertEqual(ts1.stop_abbr, 'Ch5SB')
        self.assertEqual(ts1.stop, self.stops[3732])
        self.assertEqual(ts1.node_abbr, '')
        self.assertEqual(ts1.node, None)
        # 6BUE/6stBld - Non-timing node
        self.assertEqual(ts2.tripday, tripday)
        self.assertEqual(ts2.seq, 2)
        self.assertEqual(ts2.stop_abbr, '6stBld')
        self.assertEqual(ts2.stop, self.stops[6392])
        self.assertEqual(ts2.node_abbr, '6BUE')
        self.assertEqual(ts2.node, self.nodes[856])
        # 11PE/11stPeo - Non-timing node
        self.assertEqual(ts3.tripday, tripday)
        self.assertEqual(ts3.seq, 3)
        self.assertEqual(ts3.stop_abbr, '11stPeo')
        self.assertEqual(ts3.stop, self.stops[5109])
        self.assertEqual(ts3.node_abbr, '11PE')
        self.assertEqual(ts3.node, self.nodes[38])
        # 11Uti/11Uti - Timing node
        self.assertEqual(ts4.tripday, tripday)
        self.assertEqual(ts4.seq, 4)
        self.assertEqual(ts4.stop_abbr, '11Uti')
        self.assertEqual(ts4.stop, self.stops[4156])
        self.assertEqual(ts4.node_abbr, '11Uti')
        self.assertEqual(ts4.node, self.nodes[705])
        # Utic12st - Non-timing stop with 2 matches
        self.assertEqual(ts5.tripday, tripday)
        self.assertEqual(ts5.seq, 5)
        self.assertEqual(ts5.stop_abbr, 'Utic12st')
        self.assertEqual(ts5.stop, None)
        self.assertEqual(ts5.node_abbr, '')
        self.assertEqual(ts5.node, None)
        # WHM/WHM - Timing node
        self.assertEqual(ts6.tripday, tripday)
        self.assertEqual(ts6.seq, 6)
        self.assertEqual(ts6.stop_abbr, 'WHM')
        self.assertEqual(ts6.stop, self.stops[133])
        self.assertEqual(ts6.node_abbr, 'WHM')
        self.assertEqual(ts6.node, self.nodes[515])
        trip = Trip.objects.get()
        self.assertEqual(trip.seq, 0)
        self.assertEqual(trip.tripday, tripday)
        self.assertEqual(trip.pattern, self.patterns['880F-01'])
        tt0, tt1, tt2, tt3, tt4, tt5, tt6 = TripTime.objects.all()
        self.assertEqual(tt0.trip, trip)
        self.assertEqual(tt0.tripstop, ts0)
        self.assertEqual(tt0.time, '20:00')
        self.assertEqual(tt1.trip, trip)
        self.assertEqual(tt1.tripstop, ts1)
        self.assertEqual(tt1.time, '20:01')
        self.assertEqual(tt2.trip, trip)
        self.assertEqual(tt2.tripstop, ts2)
        self.assertEqual(tt2.time, '20:01')
        self.assertEqual(tt3.trip, trip)
        self.assertEqual(tt3.tripstop, ts3)
        self.assertEqual(tt3.time, '20:06')
        self.assertEqual(tt4.trip, trip)
        self.assertEqual(tt4.tripstop, ts4)
        self.assertEqual(tt4.time, '20:08')
        self.assertEqual(tt5.trip, trip)
        self.assertEqual(tt5.tripstop, ts5)
        self.assertEqual(tt5.time, '20:08')
        self.assertEqual(tt6.trip, trip)
        self.assertEqual(tt6.tripstop, ts6)
        self.assertEqual(tt6.time, '20:43')
        
    def test_880F_bad_node(self):
        '''For some flex lines, the stop matches but the node doesn't
        
        In Aug 2012 signup, the schedule node is StFr/StFrSB, but the timing
        point (node 1037, stop 1286) is  STFRSB/StFrSB. Stop 1286's node_abbr
        is 'STFRSB' as well.  So, we just match by the stop abbreviation.
        '''
        
        self.setup_880F()
        # Setup the new node
        self.stops[1286] = self.signup.stop_set.create(
            stop_id=1286, in_service=True, lat='36.071389', lon='-95.920445',
            node_abbr='STFRSB', stop_abbr='StFrSB',
            stop_name='Saint Francis Hosp S-SW')
        self.nodes[1037] = self.signup.node_set.create(
            node_id=1037, abbr='STFRSB', name='ST FRANCIS SOUTHBOUND')
        self.nodes[1037].stops.add(self.stops[1286])
        # Replace the 11Uti/11Uti timing node
        self.linedirs['880F-0'].stopbyline_set.filter(seq=2).update(
            stop=self.stops[1286], node=self.nodes[1037])
        self.patterns['880F-01'].stopbypattern_set.filter(seq=2).update(
            stop=self.stops[1286], node=self.nodes[1037])
        schedule = """\
Stop Trips
~~~~~~~~~~

SignUp:       AUG 2012
Service:      1
Line:         880
Exception:    Off
Printed:      08-21-2012 15:18

Direction:    From Downtown

Pattern    DAS1             6BUE      11PE     StFr               WHM
          DBAY1   Ch5SB   6stBld   11stPeo   StFrSB   Utic12st    WHM
~~~~~~~  ~~~~~~  ~~~~~~  ~~~~~~~  ~~~~~~~~  ~~~~~~~  ~~~~~~~~~  ~~~~~

     01   20:00   20:01    20:01     20:06    20:08      20:08  20:43
"""
        
        mtta.models.mockable_open(
            '880F.txt').AndReturn(StringIO.StringIO(schedule))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, '880F.txt')
        self.mox.VerifyAll()
        ts4 = TripStop.objects.get(seq=4)
        self.assertEqual(ts4.stop_abbr, 'StFrSB')
        self.assertEqual(ts4.stop, self.stops[1286])
        self.assertEqual(ts4.node_abbr, 'StFr')
        self.assertEqual(ts4.node, self.nodes[1037])
        self.assertTrue(ts4.scheduled, True)

