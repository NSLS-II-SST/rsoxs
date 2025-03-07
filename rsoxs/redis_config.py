import redis  ## In-memory (RAM) databases that persists on disk even if Bluesky is restarted
from redis_json_dict import RedisJSONDict
from nbs_bl.beamline import GLOBAL_BEAMLINE as bl


redis_config_settings = bl.settings.get("redis").get("config", {})
rsoxsredis = redis.Redis(
    redis_config_settings.get("host", "info.sst.nsls2.bnl.gov"),
    port=redis_config_settings.get("port", 60737),
    db=redis_config_settings.get("db", 1),
)
rsoxs_config = RedisJSONDict(rsoxsredis, prefix=redis_config_settings.get("prefix", "rsoxs-"))