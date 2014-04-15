from PySide import QtCore, QtGui, QtSql
from datetime import datetime
from aws import AWSError, GetPrice
import sys
import os
import helper
import locale

def safe_int(str_val, def_val = 0):
    try: return int(str_val)
    except ValueError: return def_val

def CheckDatabase(filename):
    if not QtCore.QFile.exists(filename): return False
    
    db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(filename)
    
    if not db.open(): return False
    return True

def SetupDatabase():
    dir = QtCore.QDir()
    db_filename = helper.GetConfigDir() + QtCore.QDir.separator() + helper.GetDatabaseName()

    if not QtCore.QFile.exists(helper.GetConfigDir()): dir.mkpath(helper.GetConfigDir())
    if not QtCore.QFile.exists(db_filename): CreateDatabase(db_filename)
    else: CreateConnection(db_filename)

def CreateConnection(filename):
    db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(filename)
    
    if not db.open():
        QtGui.QMessageBox.critical(None, "Cannot open database", "Unable to establish a database connection")
        return False
        
    return True

def GetLastInsertedId():
    query = QtSql.QSqlQuery()
    query.exec_("SELECT last_insert_rowid()")
    
    if query.next(): return int(query.record().field(0).value())
    else: return -1

def CreateDatabase(filename):
    db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(filename)
    db.open()
    
    query = QtSql.QSqlQuery()
    
    query_str = """CREATE TABLE [main] ([id] INTEGER  PRIMARY KEY AUTOINCREMENT NOT NULL,
                                        [asin] VARCHAR(16) NOT NULL, 
                                        [label] VARCHAR(256) NOT NULL, 
                                        [price] INTEGER DEFAULT '0' NULL,
                                        [last] INTEGER DEFAULT '0' NULL, 
                                        [min] INTEGER DEFAULT '0' NULL, 
                                        [max] INTEGER DEFAULT '0' NULL,
                                        [currency] VARCHAR(8) DEFAULT '' NULL,
                                        [country] VARCHAR(4) NOT NULL)"""
    query.exec_(query_str)
    
    if LastError(query, True): return False

    query_str = """CREATE TABLE [prices] ([id] INTEGER  PRIMARY KEY AUTOINCREMENT NOT NULL, 
                                          [asin] VARCHAR(16) NOT NULL, 
                                          [price] INTEGER NOT NULL,
                                          [currency] VARCHAR(8) NOT NULL,
                                          [date] VARCHAR(16) NOT NULL)"""
    query.exec_(query_str)
    
    if LastError(query, True): return False
    return True

def LastError(query, show = False):
    if query.lastError().isValid() :
        if show: QtGui.QMessageBox.warning(None, "Errors while query executing", query.lastError().text())
        return True
    return False

def FormatAWSErrors(errors, max_length):
    results = []

    for error in errors:
        if len(error.message) > max_length: results.append(error.message[:max_length] + "...")
        else: results.append(error.message)

    if len(results) > 0: return "\n".join(results)
    return ""

def AddItem(asin, label, country):
    if CheckASIN(asin): return False
    
    query = QtSql.QSqlQuery()
    query.prepare("INSERT INTO main (asin, label, country) VALUES(:asin, :label, :country)")
    query.bindValue(":asin", asin)
    query.bindValue(":label", label)
    query.bindValue(":country", country)
    query.exec_()
    
    if LastError(query, True): return False
    return True

def EditItemLabel(asin, label):
    query = QtSql.QSqlQuery()
    query.prepare("UPDATE main SET label = :label WHERE asin = :asin")
    query.bindValue(":asin", asin)
    query.bindValue(":label", label)
    query.exec_()

    if LastError(query, True): return False
    return True

def DeleteItem(asin):
    query = QtSql.QSqlQuery()
    query.prepare("DELETE FROM main WHERE asin = :asin")
    query.bindValue(":asin", asin)
    query.exec_()

    if LastError(query, True): return False
    
    query.prepare("DELETE FROM prices WHERE asin = :asin")
    query.bindValue(":asin", asin)
    query.exec_()

    if LastError(query, True): return False
    return True
    
def CheckASIN(asin):
    query = QtSql.QSqlQuery()
    query.prepare("SELECT * FROM main WHERE asin = :asin")
    query.bindValue(":asin", asin)
    query.exec_()
    
    if query.next(): return True
    return False

def GetItemLabelAndCountry(asin):
    query = QtSql.QSqlQuery()
    query.prepare("SELECT * FROM main WHERE asin = :asin")
    query.bindValue(":asin", asin)
    query.exec_()
    
    if LastError(query, True): return ""
    if not query.next(): return ""
    
    return [query.record().field("label").value(), query.record().field("country").value()] 

def GetItemCountry(asin):
    query = QtSql.QSqlQuery()
    query.prepare("SELECT country FROM main WHERE asin = :asin")
    query.bindValue(":asin", asin)
    query.exec_()
    
    if LastError(query, True): return ""
    if not query.next(): return ""
    
    return query.record().field("country").value()

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

def FormatPrice(price, country):
    loc = locale.getlocale()
    try:
        locale.setlocale(locale.LC_ALL, GetLocaleName(country))
        price = locale.currency(price / 100.0)
    except:
        price = str(price / 100.0)
        print("WARNING: can not set locale with name " + GetLocaleName(country))
    finally:
        locale.setlocale(locale.LC_ALL, loc)

    return price

def UpdateDatabase(accessKey, secretKey, associateTag):
    cntr = 0
    up = 0
    down = 0
    
    try:
        query = QtSql.QSqlQuery()
        query.exec_("SELECT * FROM main")
        
        if query.lastError().isValid(): return [cntr, up, down, "SQL Error: " + query.lastError().text()]
        
        items = {}
        src_set = set()
        aws_set = set()
        
        while query.next():
            record = query.record()
            asin = record.field("asin").value()
            country = record.field("country").value()
            
            if not items.has_key(country): items[country] = []
            items[country].append(asin)
            
            src_set.add(asin)
            
        all_errors = []
        
        for country in items.keys():
            prices, errors = GetPrice(items[country], country, accessKey, secretKey, associateTag)
            all_errors += errors

            for price in prices:
                res = UpdateItem(price[0], price[1], price[2])
                aws_set.add(price[0])
                
                if res == -1: down = down + 1
                elif res == 1: up = up + 1  
                cntr = cntr + 1

        for asin in src_set ^ aws_set:
            UpdateItem(asin, 0, "n/a")

        return [cntr, up, down, FormatAWSErrors(all_errors, 50)]
    
    except AWSError, error:
        error_lst = FormatAWSErrors(error.GetErrors(), 50)
        error_msg = "Error: " + str(error)
        
        if len(error_lst) > 0: error_msg = error_msg + "\n" + error_lst
        return [cntr, up, down, error_msg]
    
def GetMaxItemPrice(asin):
    query = QtSql.QSqlQuery()
    query.prepare("SELECT MAX(price) max FROM prices WHERE asin = :asin AND price != 0")
    query.bindValue(":asin", asin)
    query.exec_()
    
    if query.lastError().isValid(): raise Exception(query.lastError().text())
    if query.next(): return safe_int(query.record().field("max").value())
    
    return 0

def GetMinItemPrice(asin):
    query = QtSql.QSqlQuery()
    query.prepare("SELECT MIN(price) min FROM prices WHERE asin = :asin AND price != 0")
    query.bindValue(":asin", asin)
    query.exec_()
    
    if query.lastError().isValid(): raise Exception(query.lastError().text())
    if query.next(): return safe_int(query.record().field("min").value())
        
    return 0
    
def UpdateItem(asin, price, currency):
    price = int(price)
    last_price = 0
    
    query = QtSql.QSqlQuery()
    query.prepare("SELECT price, MAX(date) FROM prices WHERE asin = :asin")
    query.bindValue(":asin", asin)
    query.exec_()
    
    if query.lastError().isValid(): raise Exception(query.lastError().text())
    if query.next() and query.record().field("price").value() != "":
        last_price = int( query.record().field("price").value())
        if last_price == price: return 0

    query.prepare("INSERT INTO prices (asin, price, currency, date) VALUES(:asin, :price, :currency, :date)")
    query.bindValue(":asin", asin)
    query.bindValue(":price", price)
    query.bindValue(":currency", currency)
    query.bindValue(":date", datetime.today().replace(microsecond = 0).isoformat())
    query.exec_()

    if query.lastError().isValid(): raise Exception(query.lastError().text())
    
    query.prepare("SELECT price, last FROM main WHERE asin = :asin")
    query.bindValue(":asin", asin)
    query.exec_()
    
    if query.lastError().isValid(): raise Exception(query.lastError().text())
    
    last = 0
    current_price = 0
    
    if query.next(): 
        last = safe_int(query.record().field("last").value())
        current_price = safe_int(query.record().field("price").value())
    if last == 0: last = price
    if current_price == 0: current_price = price
    
    isUp = False
    isDown = False
    
    if price < current_price: isDown = True
    if price > current_price: isUp = True
    
    if current_price != price:
        last = current_price
        current_price = price
    
    min = GetMinItemPrice(asin)
    max = GetMaxItemPrice(asin)
    
    query.prepare("UPDATE main SET price = :price, last = :last, min = :min, max = :max, currency = :currency WHERE asin = :asin")
    query.bindValue(":asin", asin)
    query.bindValue(":price", current_price)
    query.bindValue(":last", last)
    query.bindValue(":min", min)
    query.bindValue(":max", max)
    query.bindValue(":currency", currency)
    query.exec_()

    if query.lastError().isValid(): raise Exception(query.lastError().text())
    
    if isDown: return -1
    elif isUp: return 1
    return 0

def GetAllItems():
    query = QtSql.QSqlQuery()
    query.prepare("SELECT label, asin, country FROM main")
    query.exec_()
    
    items = []
    
    if query.lastError().isValid(): return items
    
    while query.next():
        label = query.record().field("label").value()
        asin = query.record().field("asin").value()
        country = query.record().field("country").value()
        
        items.append([label, asin, country])

    return items
    
def RemoveSequentialDuplicates(values):
    return [x for i, x in enumerate(values) if i == 0 or (i > 0 and x != values[i - 1])]

def GetNLastPriceChanges(asin, n):
    query = QtSql.QSqlQuery()

    prices = []
    end_date = ""

    while len(prices) < n:
        if end_date == "": query.prepare("SELECT price, date FROM prices WHERE asin = :asin AND price != 0 ORDER BY date DESC LIMIT :n")
        else:
            query.prepare("SELECT price, date FROM prices WHERE asin = :asin AND price != 0 AND date < :date ORDER BY date DESC LIMIT :n")
            query.bindValue(":date", end_date)

        query.bindValue(":asin", asin)
        query.bindValue(":n", n)
        query.exec_()

        if query.lastError().isValid() or not query.first(): break
        query.previous()

        while query.next():
            prices.append(safe_int(query.record().field("price").value()))
            end_date = query.record().field("date").value()

        prices = RemoveSequentialDuplicates(prices)

    prices.reverse()
    return prices