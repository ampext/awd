from datetime import datetime
from collections import namedtuple
from itertools import repeat
from helper import GetDomain
import httplib
import hashlib
import urllib
import hmac
import base64
import xml.dom.minidom

RESTRequest = namedtuple("RESTRequest", ["method", "host", "url", "params"])
AWSRequestError = namedtuple("AWSRequestError", ["code", "message"])

class AWSError(Exception):
    def __init__(self, text, request = "", errors = []):
        self.text = text
        self.request = request
        self.errors = errors
        
    def __str__(self):
        return self.text
        
    def GetErrors(self):
        return self.errors

    def GetFullDescription(self):
        result = self.text

        if self.errors:
            result += ". Errors: " + ", ".join(list(map(lambda e : "{0} ({1})".format(e.message, e.code), self.errors)))

        return result

def CreateRESTSignature(text, key):
    mac = hmac.new(key, text, hashlib.sha256)
    sig = base64.b64encode(mac.digest())

    return urllib.quote(sig)

def CreateRESTRequest(params_dict, country):
    params_list = []
    
    for k, v in params_dict.iteritems():
        params_list.append(k + "=" + urllib.quote(v))
    
    params_list.sort()
    params = "&".join(params_list)
    
    return RESTRequest("GET", "webservices.amazon." + GetDomain(country), "/onca/xml", params)

def FillParams(params_dict, accessKey, secretKey, associateTag):
    params_dict["Service"] = "AWSECommerceService"
    params_dict["AWSAccessKeyId"] = accessKey
    params_dict["AssociateTag"] = associateTag
    params_dict["Timestamp"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

def DoAWSRequest(params_dict, country, accessKey, secretKey, associateTag):
    FillParams(params_dict, accessKey, secretKey, associateTag)
    rest = CreateRESTRequest(params_dict, country)
    signature = CreateRESTSignature("\n".join(rest), secretKey)
    params = rest.params + "&Signature=" + signature
    request_url = rest.host + rest.url + "?" + params
    
    try:
        connection = httplib.HTTPConnection(rest.host)
        connection.request(rest.method, rest.url + "?" + params)
        result = connection.getresponse()
        content = result.read()
        connection.close()

    except Exception as e:
        raise AWSError(str(e), request_url, [])
    
    if result.status != 200:
        text = "server returns code " + str(result.status)
        errors = []
   
        errors = GetErrorsFromResponse(xml.dom.minidom.parseString(content))
        raise AWSError(text, request_url, errors)
    
    return content, request_url


def GetPrice(asins, country, accessKey, secretKey, associateTag):
    if len(asins) == 0 or not country: return []
    
    asins = map(unicode.encode, asins)
    country = country.encode()
    
    maxAsins = 10
    asinsList = SplitList(asins, maxAsins)
    prices = []
    params = {}

    for asins in asinsList:
        params["Operation"] = "ItemLookup"    
        params["ResponseGroup"] = "OfferFull"   
        params["ItemId"] = ",".join(asins)
        
        result, request_url = DoAWSRequest(params, country, accessKey, secretKey, associateTag)
        
        doc = xml.dom.minidom.parseString(result)
        errors = GetErrorsFromResponse(doc)

        if not IsValidRequest(doc): raise AWSError("Invalid response", request_url, errors)
        
        try: prices = prices + GetPricesFromResponse(doc)
        except Exception, e: raise AWSError(str(e), request_url)

    return (prices, errors)

def GetAttributes(asin, country, accessKey, secretKey, associateTag):
    if not asin: return {}
    
    params = {}
    params["Operation"] = "ItemLookup"    
    params["ResponseGroup"] = "ItemAttributes"   
    params["ItemId"] = asin
    
    result, request_url = DoAWSRequest(params, country, accessKey, secretKey, associateTag)

    doc = xml.dom.minidom.parseString(result)
    errors = GetErrorsFromResponse(doc)

    if not IsValidRequest(doc): raise AWSError("Invalid request", request_url, errors)
    
    try: return GetAttributesFromResponse(doc)
    except Exception, e: raise AWSError(str(e), request_url)

def GetImageUrls(asin, country, accessKey, secretKey, associateTag):
    if not asin: return {}
    
    params = {}
    params["Operation"] = "ItemLookup"    
    params["ResponseGroup"] = "Images"   
    params["ItemId"] = asin
    
    result, request_url = DoAWSRequest(params, country, accessKey, secretKey, associateTag)

    doc = xml.dom.minidom.parseString(result)
    errors = GetErrorsFromResponse(doc)

    if not IsValidRequest(doc): raise AWSError("Invalid request", request_url, errors)
    
    try: return GetImageUrlsFromResponse(doc)
    except Exception, e: raise AWSError(str(e), request_url)

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

def IsValidRequest(doc):
    validNode = FindNodeByPath(doc.documentElement, "ItemLookupResponse/Items/Request/IsValid", True)
    if not validNode or GetFirstChildNodeValue(validNode) != "True": return False

    return True

def GetErrorsFromResponse(doc):
    errors = []
   
    errorsNode = FindNodeByPath(doc.documentElement, "ItemLookupResponse/Items/Request/Errors", True)
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
    return AWSRequestError(GetFirstChildNodeValue(codeNode),GetFirstChildNodeValue(msgNode))

def GetPricesFromResponse(doc):  
    prices = []

    itemsNode = FindNodeByPath(doc.documentElement, "ItemLookupResponse/Items", True)
    if not itemsNode: raise Exception("Items not found")

    itemNodes = FindChildNodes(itemsNode, "Item")

    for itemNode in itemNodes:  
        asinNode = FindChildNode(itemNode, "ASIN")
        if not asinNode: raise Exception("ASIN node not found")
        
        asin = GetFirstChildNodeValue(asinNode)
        if not asin: raise Exception("ASIN node has not value")
        
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
        
        prices.append([asin, GetFirstChildNodeValue(amountNode), GetFirstChildNodeValue(currencyNode)])
        
        itemNode = itemNode.nextSibling   
    
    return prices

def GetAttributesFromResponse(doc):
    attrs = {}

    itemsNode = FindNodeByPath(doc.documentElement, "ItemLookupResponse/Items", True)
    if not itemsNode: raise Exception("Items not found")

    itemNodes = FindChildNodes(itemsNode, "Item")

    for itemNode in itemNodes:  
        asinNode = FindChildNode(itemNode, "ASIN")
        if not asinNode: raise Exception("ASIN node not found")
        
        asin = GetFirstChildNodeValue(asinNode)
        if not asin: raise Exception("ASIN node has not value")
        
        attrs[asin] = {}
        
        attrsNode = FindChildNode(itemNode, "ItemAttributes")
        if not attrsNode: raise Exception("ItemAttributes node not found")
        
        for node in attrsNode.childNodes:
            if not node.hasChildNodes(): continue
            elif node.firstChild.nodeType == node.TEXT_NODE: attrs[node.nodeName] = node.firstChild.nodeValue
            else:
                name = node.nodeName
                node2 = node.firstChild
                
                while node2 and node2.nodeType != node2.TEXT_NODE:
                    name = name + "/" + node2.nodeName                   
                    node2 = node2.firstChild
                    
                if node2 and node2.nodeType == node2.TEXT_NODE: attrs[name] = node2.nodeValue
                else: print("Missing text node for attribute")
        
        itemNode = itemNode.nextSibling   
        
    return attrs

def GetImageUrlsFromResponse(doc):
    urls = {}
    
    itemsNode = FindNodeByPath(doc.documentElement, "ItemLookupResponse/Items", True)
    if not itemsNode: raise Exception("Items not found")

    itemNodes = FindChildNodes(itemsNode, "Item")

    for itemNode in itemNodes:  
        asinNode = FindChildNode(itemNode, "ASIN")
        if not asinNode: raise Exception("ASIN node not found")
        
        asin = GetFirstChildNodeValue(asinNode)
        if not asin: raise Exception("ASIN node has not value")
        
        smallImageNode = FindChildNode(itemNode, "SmallImage")
        mediumImageNode = FindChildNode(itemNode, "MediumImage")
        largeImageNode = FindChildNode(itemNode, "LargeImage")
        
        asinUrls = {}
        
        if smallImageNode:
            urlNode =  FindChildNode(smallImageNode, "URL")
            if urlNode: asinUrls["S"] = GetFirstChildNodeValue(urlNode)

        if mediumImageNode:
            urlNode =  FindChildNode(mediumImageNode, "URL")
            if urlNode: asinUrls["M"] = GetFirstChildNodeValue(urlNode)
            
        if largeImageNode:
            urlNode =  FindChildNode(largeImageNode, "URL")
            if urlNode: asinUrls["L"] = GetFirstChildNodeValue(urlNode)
               
               
        urls[asin] = asinUrls
        
    return urls
    
    
def FindChildNode(parent, name):
    if not parent or not parent.hasChildNodes(): return None

    for child in parent.childNodes:
        if child.nodeType == child.ELEMENT_NODE and child.nodeName == name: return child
         
    return None

def FindChildNodes(parent, name):
    result = []

    for child in parent.childNodes:
        if child.nodeType == child.ELEMENT_NODE and child.nodeName == name:
            result.append(child)
         
    return result

def GetFirstChildNodeValue(node):
    if not node.hasChildNodes(): return None
    if node.firstChild.nodeType != node.TEXT_NODE: return None
    
    return node.firstChild.nodeValue

def FindNodeByPath(parent, path, include_parent):
    if not path: return None

    if include_parent:
        name, sep, next_path = path.partition("/")

        if parent.nodeName == name:
            if not next_path: return parent
            else: path = next_path

    nodes = [parent]
    paths = [path]

    while nodes:
        current_node = nodes.pop()
        current_path = paths.pop()
        found_nodes = []

        name, sep, next_path = current_path.partition("/")

        for node in current_node.childNodes:
            if node.nodeName == name:
                if not next_path: return node
                else: found_nodes.append(node)
        
        if not found_nodes: return None
        else:
            nodes.extend(found_nodes)
            paths.extend(list(repeat(next_path, len(found_nodes))))