from PySide import QtCore

config_dir = None
debug_mode = False

def GetConfigDir():
    if config_dir == None: return QtCore.QDir.homePath() + QtCore.QDir.separator() + ".awd"
    else: return config_dir
    
def GetDatabaseName():
    return "database.s3db"

def GetConfigName():
    return "settings"