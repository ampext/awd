from PySide import QtCore, QtGui, QtSql
from datetime import datetime
from collections import namedtuple
from aws import AWSError, GetPrice

import helper
import locale

UpdateResult = namedtuple("UpdateResult", ["total", "changed", "failed", "error"])

def safe_int(str_val, def_val = 0):
    try: return int(str_val)
    except ValueError: return def_val

def CheckDatabase(filename):
    if not QtCore.QFile.exists(filename): return False
    
    db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(filename)
    
    return db.open()

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
    #query.exec_(query_str)
    
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
        if len(error) > max_length: results.append(error[:max_length] + "...")
        else: results.append(error)

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

def CheckASINPrices(asin):
    query = QtSql.QSqlQuery()
    query.prepare("SELECT * FROM prices WHERE asin = :asin")
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

def FormatPrice(price, country):
    if price <= 0: return "n/a"
    
    loc = locale.getlocale()
    
    try:
        locale.setlocale(locale.LC_ALL, helper.GetLocaleName(country))
        price = locale.currency(price / 100.0)
    except:
        price = str(price / 100.0)
        print("WARNING: can not set locale with name " + helper.GetLocaleName(country))
    finally:
        locale.setlocale(locale.LC_ALL, loc)

    return price

def UpdateAllItems(accessKey, secretKey, associateTag):   
    query = QtSql.QSqlQuery()
    query.exec_("SELECT * FROM main")
    
    if query.lastError().isValid():
        return UpdateResult(0, 0, 0, "SQL Error: {0}".format(query.lastError().text()))
    
    items = {}
    total = 0
    changed = 0
    
    while query.next():
        record = query.record()
        asin = record.field("asin").value()
        country = record.field("country").value()
        
        if not items.has_key(country): items[country] = []
        items[country].append(asin)
        
        total += 1

    failed = total
    all_errors = set()
    
    for country in items.keys():
        try:
            prices, errors = GetPrice(items[country], country, accessKey, secretKey, associateTag)
            
            for e in errors:
                all_errors.add("response error: {0} ({1})".format(e.message, e.code))

            for price in prices:
                if UpdateItem(price[0], price[1], price[2]):
                    changed += 1
             
            failed -= len(prices)
                
        except AWSError, e:
            all_errors.add(e.GetFullDescription())

    return UpdateResult(total, changed, failed, FormatAWSErrors(all_errors, 100))

def UpdateMainTable():
    
    try:
        items = GetAllItems()
        
        for item in items:
            title = item[0]
            asin = item[1]
            current_price = GetItemPrice(asin)
            last_price = GetItemLastPrice(asin)
            min_price = GetItemMinPrice(asin)
            max_price = GetItemMaxPrice(asin)
            
            if current_price < 0 or last_price < 0:
                print("bad price values for {0} asin".format(asin))
                current_price = 0
                last_price = 0
            
            print("asin, price, last, min, max -> {0}, {1}, {2}, {3}, {4}".format(asin, current_price, last_price, min_price, max_price))
            
            query = QtSql.QSqlQuery()
            query.prepare("UPDATE main SET price = :price, last = :last, min = :min, max = :max WHERE asin = :asin")
            query.bindValue(":asin", asin)
            query.bindValue(":price", current_price)
            query.bindValue(":last", last_price)
            query.bindValue(":min", min_price)
            query.bindValue(":max", max_price)
            query.exec_()

            if query.lastError().isValid(): raise Exception(query.lastError().text())
        
    except Exception, e:
        print("failed to update main table: {0}".format(str(e)))

def GetItemPrice(asin):
    """Returns -1 if no price present for specified asin"""
    query = QtSql.QSqlQuery()
    query.prepare("SELECT price, MAX(date) FROM prices WHERE asin = :asin")
    query.bindValue(":asin", asin)
    query.exec_()
    
    if query.lastError().isValid(): raise Exception(query.lastError().text())

    if query.next():
        if query.record().isNull(0): return -1
        return safe_int(query.record().field("price").value())

    return 0

def GetItemLastPrice(asin):
    """Returns -1 if no price present for specified asin"""
    query = QtSql.QSqlQuery()
    query.prepare("SELECT price, MAX(date) date FROM prices WHERE asin = :asin")
    query.bindValue(":asin", asin)
    query.exec_()
    
    if query.lastError().isValid(): raise Exception(query.lastError().text())
    if not query.next(): return -1

    if query.record().isNull(0): return -1

    current_price = query.record().field("price").value()
    current_date = query.record().field("date").value()
    
    query.prepare("SELECT price, MAX(date) date FROM prices WHERE asin = :asin AND date != :date")
    query.bindValue(":asin", asin)
    query.bindValue(":date", current_date)
    query.exec_()
    
    if query.lastError().isValid(): raise Exception(query.lastError().text())

    if query.next():
        if query.record().isNull(0): return current_price
        else: return safe_int(query.record().field("price").value())

    return safe_int(current_price)
    
def GetItemMaxPrice(asin):
    query = QtSql.QSqlQuery()
    query.prepare("SELECT MAX(price) max_price FROM prices WHERE asin = :asin AND price != 0")
    query.bindValue(":asin", asin)
    query.exec_()
    
    if query.lastError().isValid(): raise Exception(query.lastError().text())

    if query.next():
        if query.record().isNull(0): return 0
        return safe_int(query.record().field("max_price").value())
    
    return 0

def GetItemMinPrice(asin):
    query = QtSql.QSqlQuery()
    query.prepare("SELECT MIN(price) min_price FROM prices WHERE asin = :asin AND price != 0")
    query.bindValue(":asin", asin)
    query.exec_()
    
    if query.lastError().isValid(): raise Exception(query.lastError().text())
    if query.next():
        if query.record().isNull(0): return 0
        return safe_int(query.record().field("min_price").value())

    return 0
    
def UpdateItem(asin, price, currency):
    current_price = safe_int(price)
    last_price = GetItemPrice(asin)
    
    if last_price < 0: last_price = current_price
    elif last_price == current_price: return False

    query = QtSql.QSqlQuery()
    query.prepare("INSERT INTO prices (asin, price, currency, date) VALUES(:asin, :price, :currency, :date)")
    query.bindValue(":asin", asin)
    query.bindValue(":price", price)
    query.bindValue(":currency", currency)
    query.bindValue(":date", datetime.today().replace(microsecond = 0).isoformat())
    query.exec_()

    if query.lastError().isValid(): raise Exception(query.lastError().text())
    
    min_price = GetItemMinPrice(asin)
    max_price = GetItemMaxPrice(asin)
    
    query.prepare("UPDATE main SET price = :price, last = :last, min = :min, max = :max, currency = :currency WHERE asin = :asin")
    query.bindValue(":asin", asin)
    query.bindValue(":price", current_price)
    query.bindValue(":last", last_price)
    query.bindValue(":min", min_price)
    query.bindValue(":max", max_price)
    query.bindValue(":currency", currency)
    query.exec_()

    if query.lastError().isValid(): raise Exception(query.lastError().text())

    return True

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