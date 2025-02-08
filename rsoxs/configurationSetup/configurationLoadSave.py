
from rsoxs_scans.configurationLoadSaveSanitize import loadConfigurationSpreadsheet_Local, saveConfigurationSpreadsheet_Local
from ..startup import rsoxs_config


def loadSheet(filePath):
    configuration = loadConfigurationSpreadsheet_Local(filePath)
    rsoxs_config["bar"] = configuration
    print("Replaced persistent configuration with configuration loaded from file path: " + str(filePath))
    return

def saveSheet(filePath, fileLabel):
    saveConfigurationSpreadsheet_Local(configuration=rsoxs_config["bar"], filePath=filePath, fileLabel=fileLabel)
    return
