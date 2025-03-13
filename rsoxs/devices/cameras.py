from nslsii.ad33 import StatsPluginV33
from ophyd.areadetector.base import EpicsSignalWithRBV as SignalWithRBV
from ophyd import Component as Cpt
from ophyd import EpicsSignalRO

from nbs_bl.beamline import GLOBAL_BEAMLINE as bl
from nbs_bl.printing import run_report
from sst_base.cameras import StandardProsilicaV33, TIFFPluginWithProposalDirectory

run_report(__file__)



class StatsWCentroid(StatsPluginV33):
    centroid_total = Cpt(EpicsSignalRO,'CentroidTotal_RBV',kind='hinted')
    profile_avg_x = Cpt(EpicsSignalRO,'ProfileAverageX_RBV',kind='hinted')
    profile_avg_y = Cpt(EpicsSignalRO,'ProfileAverageY_RBV',kind='hinted')

def StandardProsilicawstatsFactory(*args, camera_name="", date_template="%Y/%m/%d", **kwargs):
    class StandardProsilicawstats(StandardProsilicaV33):
        tiff = Cpt(
            TIFFPluginWithProposalDirectory,
            suffix="TIFF1:",
            md=bl.md,
            camera_name=camera_name,
            date_template=date_template,
            read_attrs=["time_stamp"],
        )
        stats1 = Cpt(StatsWCentroid, "Stats1:", kind='hinted')
        stats2 = Cpt(StatsWCentroid, "Stats2:", read_attrs=["total"])
        stats3 = Cpt(StatsWCentroid, "Stats3:", read_attrs=["total"])
        stats4 = Cpt(StatsWCentroid, "Stats4:", read_attrs=["total"])
        stats5 = Cpt(StatsWCentroid, "Stats5:", read_attrs=["total","centroid_total", "profile_avg_x", "profile_avg_y"])

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    return StandardProsilicawstats(*args, **kwargs)

def configure_cameras():
    SampleViewer_cam.cam.ensure_nonblocking()
    crosshair = Sample_cam.over1.overlay_1
    Sample_cam.over1.overlay_1.position_y.kind = "hinted"
    Sample_cam.over1.overlay_1.position_x.kind = "hinted"
    crosshair.x = crosshair.position_x
    crosshair.y = crosshair.position_y
    #
    crosshair_side = Side_cam.over1.overlay_1
    crosshair_side.x = crosshair_side.position_x
    crosshair_side.y = crosshair_side.position_y
    crosshair_side.x.kind = "hinted"
    crosshair_side.y.kind = "hinted"
    #
    crosshair_saxs = DetS_cam.over1.overlay_1
    crosshair_saxs.x = crosshair_saxs.position_x
    crosshair_saxs.y = crosshair_saxs.position_y
    crosshair_saxs.x.kind = "hinted"
    crosshair_saxs.y.kind = "hinted"
    #
    #



    def crosshair_on():
        crosshair.use.set(1)


    #
    #


    def crosshair_off():
        crosshair.use.set(0)


    #
    #
    all_standard_pros = [SampleViewer_cam, Sample_cam, DetS_cam, izero_cam]
    for camera in all_standard_pros:
        # camera.read_attrs = ['stats1', 'stats2', 'stats3', 'stats4', 'stats5']
        # getattr(camera, s).kind = 'normal'
        [
            setattr(getattr(camera, s), "kind", "normal")
            for s in ["stats1", "stats2", "stats3", "stats4", "stats5"]
        ]
        # camera.tiff.read_attrs = []  # leaving just the 'image'
        for stats_name in ["stats1", "stats2", "stats3", "stats4", "stats5"]:
            stats_plugin = getattr(camera, stats_name)
            stats_plugin.read_attrs = ["total"]
            # camera.stage_sigs[stats_plugin.blocking_callbacks] = 1
        # The following 2 lines should be used when not running AD V33
        # camera.stage_sigs[camera.roi1.blocking_callbacks] = 1
        #     #camera.stage_sigs[camera.trans1.blocking_callbacks] = 1
        #
        #     #The following line should only be used when running AD V33
        #   camera.cam.ensure_nonblocking()
        camera.stage_sigs[camera.cam.trigger_mode] = "Fixed Rate"


    SampleViewer_cam.tiff.kind = "normal"