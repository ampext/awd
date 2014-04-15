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

def GetDomain(country):
    if country == "us": return "com"
    if country == "uk": return "co.uk"
    if country == "de": return "de"
    if country == "fr": return "fr"
    if country == "jp": return "co.jp"
    if country == "ca": return "ca"
    if country == "cn": return "cn"
    return ""