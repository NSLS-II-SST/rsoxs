from sst_funcs.printing import run_report
from sst_base.cameras import StandardProsilica, ColorProsilicaWithTIFFV33

run_report(__file__)

Side_cam = StandardProsilica("XF:07ID1-ES:1{Scr:2}", name="RSoXS Sample Area Camera")
DetS_cam = StandardProsilica("XF:07ID1-ES:1{Scr:3}", name="WAXS Detector Area Camera")
Izero_cam = StandardProsilica("XF:07ID1-ES:1{Scr:1}", name="Izero YAG Camera")
Sample_cam = StandardProsilica("XF:07ID1-ES:1{Scr:4}", name="RSoXS Sample Area Camera")
SampleViewer_cam = ColorProsilicaWithTIFFV33(
    "XF:07ID1-ES:1{Scr:5}",
    name="Sample Imager Detector Area Camera",
    read_attrs=["tiff"],
)
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
all_standard_pros = [SampleViewer_cam, Sample_cam, DetS_cam, Izero_cam]
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
