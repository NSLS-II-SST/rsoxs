from .detectors import RSOXSGreatEyesDetector


## Defines waxs_det and sets it up at the same time to guarantee that it is set up as soon as it is loaded.
## Guarantees that waxs_det is never attempted to be accessed before it actually gets loaded.
def WaxsDetectorFactory(*args, **kwargs):
    waxs_det = RSOXSGreatEyesDetector(*args, **kwargs)
    waxs_det.cam.read_attrs = ["acquire_time"]
    waxs_det.transform_type = 1
    waxs_det.cam.ensure_nonblocking()
    waxs_det.setup_cam()
    waxs_det.stats1.name = "WAXS fullframe"
    return waxs_det
