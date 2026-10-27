import unittest
from types import SimpleNamespace
from tracking import BlinkDetector, GazeCalibration, eye_measurements


class BlinkTests(unittest.TestCase):
    def setUp(self):
        self.detector=BlinkDetector(.18)
        self.detector.baseline=.3
        self.now=1
        self.feed(.3,.3)

    def feed(self,ear,duration):
        events=0
        for _ in range(round(duration/.02)):
            self.now+=.02
            events+=self.detector.update(ear,self.now)
        return events

    def test_one_shot_while_closed_rearms_only_after_open(self):
        self.assertEqual(self.feed(.1,1.5),1)
        self.assertEqual(self.feed(.1,1.5),0)
        self.feed(.3,.25)
        self.assertEqual(self.feed(.1,.3),1)

    def test_natural_blink_ignored(self):
        self.assertEqual(self.feed(.1,.08),0)
        self.assertEqual(self.feed(.3,.3),0)

    def test_lost_face_never_fires_or_rearms_closed(self):
        self.feed(.1,.12)
        self.assertFalse(self.detector.update(None,self.now+.02))
        self.assertEqual(self.feed(.1,1),0)
        self.feed(.3,.3)
        self.assertEqual(self.feed(.1,.3),1)

    def test_frame_stall_cancels_pending_blink(self):
        self.feed(.1,.1)
        self.now+=1
        self.assertFalse(self.detector.update(.1,self.now))
        self.assertEqual(self.feed(.1,.5),0)

    def test_duplicate_frame_cannot_complete_blink(self):
        self.feed(.1,.1)
        for _ in range(50):self.assertFalse(self.detector.update(.1,self.now))

    def test_hysteresis_prevents_threshold_jitter(self):
        self.feed(.1,.08)
        self.feed(.21,.08)  # Between closing and opening limits.
        self.assertEqual(self.feed(.1,.1),1)

    def test_cold_start_requires_open_samples_then_rearm(self):
        d=BlinkDetector()
        for i in range(40):self.assertFalse(d.update(.3 if i%10 else .1,i*.04))
        self.assertAlmostEqual(d.baseline,.3)
        self.assertFalse(d.armed)
        self.assertFalse(d.update(.1,1.6))

    def test_reset_preserves_calibration(self):
        self.detector.reset()
        self.assertEqual(self.detector.baseline,.3)
        self.assertFalse(self.detector.armed)


class GazeTests(unittest.TestCase):
    def test_fits_both_axes_and_clamps_screen(self):
        g=GazeCalibration()
        points=[((x-.5)*.2,(y-.5)*.12) for x,y in g.TARGETS]
        self.assertTrue(g.fit(points))
        x,y=g.map((.04,-.024))
        self.assertAlmostEqual(x,.7)
        self.assertAlmostEqual(y,.3)
        self.assertEqual(g.map((100,100)),(1,1))

    def test_still_eyes_do_not_pass_calibration(self):
        self.assertFalse(GazeCalibration().fit([(.01,.01)]*5))

    def test_pixel_aspect_correct_ear(self):
        def landmarks(width,height):
            lm=[SimpleNamespace(x=0.,y=0.) for _ in range(478)]
            for left,right,t1,b1,t2,b2,iris,offset in [(33,133,160,144,158,153,468,100),(362,263,385,380,387,373,473,200)]:
                for index,x,y in [(left,0,0),(right,40,0),(t1,10,-6),(b1,10,6),(t2,30,-6),(b2,30,6),(iris,20,0)]:
                    lm[index]=SimpleNamespace(x=(offset+x)/width,y=(100+y)/height)
            return lm
        ear,gaze=eye_measurements(landmarks(640,480),640,480)
        other,_=eye_measurements(landmarks(1280,720),1280,720)
        self.assertAlmostEqual(ear,.3)
        self.assertAlmostEqual(other,ear)
        self.assertAlmostEqual(gaze[0],0)
        self.assertAlmostEqual(gaze[1],0)


if __name__=='__main__':unittest.main()
