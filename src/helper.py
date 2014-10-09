from PySide import QtCore, QtGui

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

def ReadColorValue(settings, key, def_color):
    """
    @type def_color: QtGui.QColor
    """
    if not settings.contains(key):
        settings.setValue(key, def_color.name())

    color = QtGui.QColor(settings.value(key, def_color.name()))

    if color.isValid(): return color
    return def_color

def to_bool(value):
    if isinstance(value, unicode): return value.lower() == "true"
    return bool(value)