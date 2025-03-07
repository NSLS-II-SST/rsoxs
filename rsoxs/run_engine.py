from nbs_bl.run_engine import create_run_engine
from nbs_bl.beamline import GLOBAL_BEAMLINE as bl

RE = create_run_engine(setup=True)

"""redis_md_settings = bl.settings.get("redis").get("md")

mdredis = redis.Redis(
    redis_md_settings.get("host", "info.sst.nsls2.bnl.gov"),
    port=redis_md_settings.get("port", 6379),
    db=redis_md_settings.get("db", 0),
)"""
# RE.md = RedisStatusDict(mdredis, prefix=redis_md_settings.get("prefix", ""))
RE.md = bl.md
md = RE.md  ## The contents from md are added into the start document for the scan metadata in Tiled.
# GLOBAL_USER_STATUS.add_status("USER_MD", RE.md)
