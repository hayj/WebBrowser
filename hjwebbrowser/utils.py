# coding: utf-8

from systemtools.basics import *
from datatools.jsonreader import *
from datatools.url import *
from datatools.csvreader import *
from systemtools.basics import *
from systemtools.file import *
from systemtools.logger import log, logInfo, logWarning, logWarning, logError, Logger
from systemtools.location import *
from systemtools.system import *
import selenium
from selenium import webdriver
import sh
import random
import html2text
import re
import ipgetter
from threading import Thread, Lock
import math
import numpy
from enum import Enum
from error404detector.detector import *

def tryUrlToCrawlingElement(url):
    if isinstance(url, str):
        return CrawlingElement(url)
    else:
        return url

def convertBrowserResponse(response, browser, nice=True):
    """
        This function convert a Browser response (using html()) to a HTTPBrowser response
    """
    newResponse = {}
    niceValue = 200
    if not nice:
        niceValue = 0
    if browser.proxy is not None:
        newResponse["proxy"] = browser.proxy["ip"]
    newResponse["html"] = response["html"]
    newResponse["lastUrl"] = response["lastUrl"]
    newResponse["url"] = response["crawlingElement"].data
    newResponse["historyCount"] = None
    newResponse["redirected"] = newResponse["url"] != newResponse["lastUrl"]
    if response["status"] == REQUEST_STATUS.success:
        newResponse["status"] = 200
    elif response["status"] == REQUEST_STATUS.error404:
        newResponse["status"] = 404
    elif response["status"] == REQUEST_STATUS.timeout:
        newResponse["status"] = 0
    elif response["status"] == REQUEST_STATUS.timeoutWithContent:
        newResponse["status"] = 200
    elif response["status"] == REQUEST_STATUS.refused:
        newResponse["status"] = niceValue
    elif response["status"] == REQUEST_STATUS.duplicate:
        newResponse["status"] = niceValue
    elif response["status"] == REQUEST_STATUS.invalid:
        newResponse["status"] = niceValue
    else:
        newResponse["status"] = 0
    return newResponse

def httpBrowserToBrowserStatus(status):
    """
        This function convert a HTTPBrowser status to a Browser status
        pls handle duplicate invalid timeout timeoutWithContent exception yourself
    """
    if status == 200:
        return REQUEST_STATUS.success
    elif status == 404 or status == 403:
        return REQUEST_STATUS.error404
    else:
        return REQUEST_STATUS.refused

class CrawlingElement():
    """
        https://stackoverflow.com/questions/390250/elegant-ways-to-support-equivalence-equality-in-python-classes/25176504#25176504
    """
    TYPE = Enum("TYPE", "notUniqueUrl uniqueUrl pipedMessage")
    def __init__(self, data, extraData=None, type=TYPE.uniqueUrl):
        """
            data can be an url or a piped message (dict)
            extraData can be any dict
        """
        self.data = data
        self.type = type
        self.extraData = extraData
    def __eq__(self, other):
        return self.data == other.data
    def __hash__(self):
        return 0
    def __lt__(self, other):
        return str(self.data) < str(other.data)
    def __repr__(self):
        return str(self.data)
    def __str__(self):
        return listToStr({"data": self.data,
                          "extraData": self.extraData,
                          "type": self.type})
    def toString(self):
        if self.data is not None:
            return str(self.data)
        else:
            return str(self)


def generateAjaxRandomURLs(n=10):
    for i in range(n):
        yield generateAjaxRandomURL()

def generateAjaxRandomURL():
    return "http://localhost/testajax/demo.php?id=" + getRandomStr() + "#page1"

def isRefused(html, lastUrl):
    if html is None or html.strip() == "" or lastUrl is None or lastUrl.strip() == "" :
        return True
    if html == "<html><head></head><body></body></html>" \
    or html == "<html xmlns=\"http://www.w3.org/1999/xhtml\"><head></head><body></body></html>" \
    or lastUrl == "about:blank" \
    or "could not be retrieved</title>" in html:
        return True
    return False

def isInvalidHtml(html):
    if html is None or len(html) < 100:
        return True
    titleResult = re.finditer("<title(.*)</title>", html.lower(), re.DOTALL | re.IGNORECASE)
    if titleResult is None:
        return True
    titleResult = list(titleResult)
    if len(titleResult) == 0:
        return True
    if "You have been blocked" in html:
        return True
    return False

error404Detector = None
def is404Error(html, fast=False):
    global error404Detector
    if fast:
        return is404ErrorFastFunct(html)
    else:
        if error404Detector is None:
            error404Detector = Error404Detector()
        return error404Detector.is404(html)


def is404ErrorFastFunct(html, debug=False):
#     strToFile(html, getExecDirectory(__file__) + "/tmp/test.html")
#     exit()
    # If we found any of this in the first "<title(.*)</title>", it's a 404:
    match404Title = ["404", "not found", "Moved Temporarily", "401 Unauthorized", "403 Forbidden", "Request Timeout", "Too Many Requests", "Service Unavailable", "404 ", " 404"]
    titleResult = re.finditer("<title(.*)</title>", html, re.DOTALL)
    if titleResult is None:
        return True
    titleResult = list(titleResult)
    if len(titleResult) == 0:
        return True
    title = None
    for current in titleResult:
        title = current.group(1)
        if title is None:
            return True
        if len(title) >= 1:
            title = title[1:]
        title = title.lower()
        break
    for current in match404Title:
        if current.lower() in title:
            if debug:
                print(">>>>> " + current)
            return True
    # Or if any of this is in the body:
    match404Body = ["404 not found", "page not found", "404<", ">404", "Moved Temporarily", "401 Unauthorized", "403 Forbidden", "Request Timeout", "Too Many Requests", "Service Unavailable"]
    htmlLower = html.lower()
    for current in match404Body:
        if current.lower() in htmlLower:
            if debug:
                print(">>>>> " + current)
            return True
    # Else we return True
    return False


proxiesDataSubDir = "/Misc/crawling/proxies"

def getProxiesPath(proxiesPath=None):
    if proxiesPath is not None:
        return proxiesPath
    else:
        return dataDir() + proxiesDataSubDir + "/proxies-renew.txt"

def getIP():
    return ipgetter.myip()

def getRandomProxy(proxiesPath=None):
    proxiesPath = getProxiesPath(proxiesPath)
    allProxies = getProxies(proxiesPath)
    return random.choice(allProxies)

def getProxies(proxiesPath=None, removeFailedProxies=True, defaultType="http"):
    proxiesPath = getProxiesPath(proxiesPath)
    # If the file exist, we parse it, one proxie by line (165.231.108.5:80:user:pass)
    if fileExists(proxiesPath):
        proxies = []
        proxiesTextList = fileToStrList(proxiesPath)
        for current in proxiesTextList:
            try:
                if current.strip() != "":
                    theTuple = current.split(":")
                    theDict = {}
                    theDict["ip"] = theTuple[0]
                    theDict["port"] = theTuple[1]
                    theDict["user"] = theTuple[2]
                    theDict["password"] = theTuple[3]
                    theDict["type"] = defaultType
                    proxies.append(theDict)
            except Exception as e:
                pass
        if removeFailedProxies:
            failedPath = dataDir() + proxiesDataSubDir + "/proxies-failed.txt"
            if isFile(failedPath):
                proxiesFailed = getProxies(proxiesPath=failedPath, removeFailedProxies=False)
                proxies = listSubstract(proxies, proxiesFailed)
        return proxies
    return None

def testIsHtmlOK():
    for currentPath in sortedGlob(getExecDirectory(__file__) + "/data-test/*.html"):
        print(currentPath)
        text = fileToStr(currentPath)
        print(isHtmlOk(text))

def proxyToDict(proxyStr, defaultType="http"):
    theDict = {}
    theTuple = proxyStr.split(":")
    theDict["ip"] = theTuple[0]
    theDict["port"] = theTuple[1]
    theDict["user"] = None
    theDict["password"] = None
    if len(theTuple) > 2:
        theDict["user"] = theTuple[2]
        theDict["password"] = theTuple[3]
    theDict["type"] = defaultType
    return theDict

def proxyToStr(proxyDict):
    user = ""
    if dictContains(proxyDict, "user"):
        user += ":" + proxyDict["user"] + ":" + proxyDict["password"]
    proxyStr = proxyDict["ip"] + ":" + proxyDict["port"] + user
    return proxyStr

def getProxiesProd():
    return getProxies(dataDir() + proxiesDataSubDir + "/proxies-prod.txt")
def getProxiesTest():
    return getProxies(dataDir() + proxiesDataSubDir + "/proxies-test.txt")
def getProxiesRenew():
    return getProxies(dataDir() + proxiesDataSubDir + "/proxies-renew.txt")
def getProxiesLinkedin():
    return getProxies(dataDir() + proxiesDataSubDir + "/proxies-linkedin.txt")
def getAllProxies(*args, **kwargs):
    return getProxiesAll(*args, **kwargs)
def getProxiesAll():
    return getProxiesRenew() + getProxiesLinkedin()


if __name__ == '__main__':
#     testIsHtmlOK()
#     proxies = getProxies(dataDir() + proxiesDataSubDir + "/proxies-renew.txt")
    proxies = getProxiesRenew()
    print(len(proxies))






