from datetime import datetime
import httplib
import hashlib
import urllib
import hmac
import base64
import xml.dom.minidom
import db_helper

class AWSError(Exception):
    def __init__(self, text, request = "", errors = []):
        self.text = text
        self.request = request
        self.errors = errors
        
    def __str__(self):
        return self.text
        
    def GetErrors(self):
        return self.errors
    
def CreateRESTSignature(text, key):
    mac = hmac.new(key, text, hashlib.sha256)
    sig = base64.b64encode(mac.digest())

    return urllib.quote(sig)

def MakeRESTString(params, country):
    params = params.split("&")
    params.sort()
    return ["GET", "webservices.amazon." +  db_helper.GetDomain(country), "/onca/xml", "&".join(params)]

def GetPrice(asins, country, accessKey, secretKey, associateTag):
    if len(asins) == 0 or country == "": return []
    
    asins = map(unicode.encode, asins)
    country = country.encode()
    
    maxAsins = 10
    asinsList = SplitList(asins, maxAsins)
    prices = []
   
    for asins in asinsList:
        params = "Service=AWSECommerceService&Operation=ItemLookup&AWSAccessKeyId=" + accessKey + "&AssociateTag=" + associateTag + "&ResponseGroup=OfferFull&ItemId=" + ",".join(asins)
        params += "&Timestamp=" + datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        params = urllib.quote(params, "=&")
        rest = MakeRESTString(params, country)
        signature = CreateRESTSignature("\n".join(rest), secretKey)
        params = rest[3]
        params += "&Signature=" + signature
        
        connection = httplib.HTTPConnection(rest[1])
        connection.request(rest[0], rest[2] + "?" + params)
        
        request_url = rest[1] + rest[2] + "?" + params
        res = connection.getresponse()
        
        if res.status != 200 : 
            text = "server returns code " + str(res.status)
            errors = []
            
            error = ParseLookupErrorResponse(xml.dom.minidom.parseString(res.read()))
            if error.has_key("msg"): errors.append(error)
            
            raise AWSError(text, request_url, errors)
        
        doc = xml.dom.minidom.parseString(res.read())
        if not IsValidResponse(doc): raise AWSError("Invalid response", request_url, GetErrors(doc))
        
        try: prices = prices + GetPricesFromResponse(doc)
        except Exception, e: raise AWSError(str(e), request_url)
        
        connection.close()
        
        errors = GetErrors(doc)
        print(request_url)
    
    return (prices, errors)

def SplitList(lst, size):
    n = len(lst) / size
    r = len(lst) % size

    start = 0
    end = max(size, r)
    sub_list = []

    for i in xrange(n + 1):
        if start >= len(lst): break
        sub_list.append(lst[start:end])

        start = start + size
        if i == n + 1: end = len(lst)
        else: end = end + size

    return sub_list

def IsValidResponse(doc):
    validNode = doc.getElementsByTagName("IsValid")[0]
    if not validNode: return False
    
    return GetFirstChildNodeValue(validNode) == "True"

def GetErrors(doc):
    errors = []
   
    if not doc.getElementsByTagName("Errors"): return errors
    
    errorsNode = doc.getElementsByTagName("Errors")[0]
    if not errorsNode: return errors

    errorNode = FindChildNode(errorsNode, "Error")
    
    while errorNode != None:
        error = ParseErrorNode(errorNode)
        if error != None: errors.append(error)
        errorNode = errorNode.nextSibling

    return errors

def ParseErrorNode(errorNode):
    codeNode = FindChildNode(errorNode, "Code")
    msgNode = FindChildNode(errorNode, "Message")
    
    if not codeNode or not msgNode: return None
    return {"code" : GetFirstChildNodeValue(codeNode), "msg" : GetFirstChildNodeValue(msgNode)}
    
def ParseLookupErrorResponse(doc):
    responseNode = doc.getElementsByTagName("ItemLookupErrorResponse")[0]
    if not responseNode: return {}
    
    errorNode = FindChildNode(responseNode, "Error")
    if not errorNode: return {}
    
    return ParseErrorNode(errorNode)

def GetPricesFromResponse(doc):  
    prices = []

    itemsNode = doc.getElementsByTagName("Items")[0]
    if not itemsNode: raise Exception("Items node not found")
    
    requestNode = FindChildNode(itemsNode, "Request")
    if not requestNode: raise Exception("Request node not found")
    
    itemNode = requestNode.nextSibling
    
    if itemNode == None: raise Exception("Items not found")
    
    while itemNode != None:
        if itemNode.nodeType != itemNode.ELEMENT_NODE or itemNode.nodeName != "Item":
            itemNode = itemNode.nextSibling
            continue
        
        asinNode = FindChildNode(itemNode, "ASIN")
        if not asinNode: raise Exception("ASIN node not found")
        
        offersNode = FindChildNode(itemNode, "Offers")
        if not offersNode:
            itemNode = itemNode.nextSibling
            continue

        offerNode = FindChildNode(offersNode, "Offer")
        if not offerNode:
            itemNode = itemNode.nextSibling
            continue
        
        listingNode = FindChildNode(offerNode, "OfferListing")
        if not listingNode:
            itemNode = itemNode.nextSibling
            continue
        
        priceNode = FindChildNode(listingNode, "Price")
        if not priceNode:
            itemNode = itemNode.nextSibling
            continue
        
        amountNode = FindChildNode(priceNode, "Amount")
        if not amountNode:
            itemNode = itemNode.nextSibling
            continue
        
        currencyNode = FindChildNode(priceNode, "CurrencyCode")
        if not currencyNode:
            itemNode = itemNode.nextSibling
            continue
        
        prices.append([GetFirstChildNodeValue(asinNode), GetFirstChildNodeValue(amountNode), GetFirstChildNodeValue(currencyNode)])
        
        itemNode = itemNode.nextSibling   
    
    return prices
    
def FindChildNode(parent, name):
    if not parent.hasChildNodes(): return None

    for child in parent.childNodes:
        if child.nodeType == child.ELEMENT_NODE and child.nodeName == name: return child
         
    return None

def GetFirstChildNodeValue(node):
    if not node.hasChildNodes(): return None
    if node.firstChild.nodeType != node.TEXT_NODE: return None
    
    return node.firstChild.nodeValue