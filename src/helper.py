from PySide import QtCore, QtGui

import os

config_dir = None
debug_mode = False
countryIcons = {}

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

def GetAmazonCountries():
    return ["us", "uk", "de", "fr", "jp", "ca", "cn"]

def GetLocaleName(country):
    if country == "us": 
        if os.name == "nt": return "us_US"
        else: return "en_US"
        
    if country == "uk": 
        if os.name == "nt": return "eng_UK"
        else: return "en_GB"
    
    if country == "de": 
        if os.name == "nt": return "deu_deu"
        else: return "de_DE"
    
    if country == "fr": 
        if os.name == "nt": return "fr-FR"
        else: return "fr_FR"
    
    if country == "jp": 
        if os.name == "nt": return "ja-JP"
        else: return "ja_JP"
    
    if country == "ca": 
        if os.name == "nt": return "fr-CA"
        else: return "fr_CA"
    
    if country == "cn": 
        if os.name == "nt": return "zh-TW"
        else: return "zh_TW"
    
    return ""

def InitCountryIcons():
    for country in GetAmazonCountries():
        countryIcons[country] = QtGui.QIcon("images" + QtCore.QDir.separator() + country + ".png")
        

def GetCountryIcon(country):
    if countryIcons.has_key(country): return countryIcons[country]
    return None