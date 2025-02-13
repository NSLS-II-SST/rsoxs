from .detectors import RSOXSGreatEyesDetector


def WaxsDetectorFactory(*args, **kwargs):
    waxs_det = RSOXSGreatEyesDetector(*args, **kwargs)
    waxs_det.cam.read_attrs = ["acquire_time"]
    waxs_det.transform_type = 1
    waxs_det.cam.ensure_nonblocking()
    waxs_det.setup_cam()
    waxs_det.stats1.name = "WAXS fullframe"
    return waxs_det
