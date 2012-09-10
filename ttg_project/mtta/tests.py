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
            stop_name='E Archer St&N 124th E Ave/N 123Rd E')
        self.stop2 = Stop.objects.create(
            signup=self.signup, stop_id=5440, stop_abbr='Adm106p',
            lat='36.160832', lon='-95.858432',
            stop_name='E Admiral Pl&N 106th E Pl/S 106Th E')
        self.stop3 = Stop.objects.create(
            signup=self.signup, stop_id=5478, stop_abbr='AdmMem',
            site_name='Phillips 66', node_abbr='ADM/MEME',
            lon='-95.887364', lat='36.160834',
            stop_name='E Admiral Pl&N Memorial Dr/S Memori')
        self.line100 = Line.objects.create(
            signup=self.signup, line_id=2893, line_abbr=100, 
            line_name='Admiral', line_color=12910532, line_type='FX')
        self.line100dir0 = LineDirection.objects.create(
            line=self.line100, linedir_id=28930, name='To Downtown')
        self.node1 = Node.objects.create(
            node_id=635, stop=self.stop1, abbr='123Ar', name='123rd E/Archer')
        self.node3 = Node.objects.create(
            node_id=736, stop=self.stop3, abbr='Adm/MemE',
            name='ADMIRAL PL/MEMORIAL P W-NW')
        self.sbl1 = StopByLine.objects.create(
            linedir=self.line100dir0, stop=self.stop1, node=self.node1, seq=1)
        self.sbl2 = StopByLine.objects.create(
            linedir=self.line100dir0, stop=self.stop2, seq=2)
        self.sbl3 = StopByLine.objects.create(
            linedir=self.line100dir0, stop=self.stop3, node=self.node3, seq=3)
        self.pattern = Pattern.objects.create(
            linedir=self.line100dir0, name='01', pattern_id=11431,
            raw_pattern=[[300, 500]])

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_import_schedule_basic(self):
        schedule = """\
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
        mtta.models.mockable_open(
            'test.txt').AndReturn(StringIO.StringIO(schedule))
        self.mox.ReplayAll()
        TripDay.import_schedule(self.signup, 'test.txt')
        self.mox.VerifyAll()
        
        # TODO: Check DB values
    
    def test_import_schedule_flex(self):
        # TODO: Check that schedule 580 matches line 508FLEX
        pass

    def test_import_schedule_sflx(self):
        # TODO: Check that schedule 860 matches 860SFLX
        pass
