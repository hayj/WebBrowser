# coding: utf-8

from datatools.json import *
from datatools.url import *
from machinelearning.bandit import *
from machinelearning.function import *
from datatools.csvreader import *
from systemtools.basics import *
from systemtools.duration import *
from systemtools.file import *
from systemtools.logger import *
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
from hjwebbrowser.utils import *
from domainduplicate.domainduplicate import *
from enum import Enum
import time
from hjwebbrowser.utils import *
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
import zipfile
from collections import OrderedDict
import psutil


# sometime phantomjs driver block on a self.driver.get(url) even a timeout was set, for exemple these urls :
# ["http://nypost.com/2017/10/07/inside-the-mean-girls-culture-that-destroyed-sex-and-the-city/", "http://abcnews.go.com/Entertainment/wireStory/resignations-fallout-grow-embattled-producer-weinstein-50351532"]
# When you use phantomjs on these urls, the get take an infinite time, so a memory heap in the crawler
# And when we use a python thread timeout on the get, we can't quit() the driver...
# And we can't kill the browser in command line because we don't know which phantomjs it is...
# DONE DONE DONE DONE DONE DONE DONE DONE !!!!!!!!! with pid and threaded timeouts

# TODO chrome header (user agent done, but other header element can't be set)

# TODO phantomjs is easily detected by google and others... why ?
# phantomjs is slow and less reliable but take less proc

# TODO Chrome probleme : too much proc...

# Par contre pour la détection de phantomjs par google aucune idée de comment ils font, je sais juste que c'est pas le header, c'est pas les proxies, c'est pas un comportement non humain puisqu'il y a juste une requête, ça doit être qqch de plus basique comme une option genre ne pas charger les image ou le cache qqch comme ça.


def queueMean(queue, defaultValue=0.0):
    if queue is None:
        return defaultValue
    l = list(queue)
    l = removeNone(l)
    if len(l) == 0:
        return defaultValue
    return sum(l) / len(l)


REQUEST_STATUS = Enum("REQUEST_STATUS", "success error404 timeout timeoutWithContent refused duplicate invalid exception")

DRIVER_TYPE = Enum("DRIVER_TYPE", "chrome phantomjs")


class Browser():
    """
        # html and get methods explanation:

        We have 2 scenaries:
         * You gave a htmlCallback to the __init__. This scenario is usefull if you want to consider
         the page download as a critical part (network bottleneck). And you also want to wait the ajax
         to be loaded but you don't consider this wait as a network bottleneck.
             * So you have to call "get" method, this will cacheLock the object,
             get the url, then start a thread, finally return True if the request succeeded.
             The thread will wait, call the "html" method (for the htmlCallback) and finally
             release the cacheLock.
         * You didn't give any callback:
              * You need to use "html" method and give an url. No thread will be executed.
              No cacheLock will be locked. "html" method will call "get" method and just return data
              to the caller.

        # Scrolling down before or after the ajax wait

        If, for instance you want to scroll down or other things in the browser, you can give
        callbacks to the browser : beforeAjaxSleepCallback and afterAjaxSleepCallback



        Paramètre de Chromium : Ne conserver les données locales que jusqu'à ce que je quitte ma session de navigation
    """

    headers = \
    {
        "Accept": \
        [
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    #         "*/*",
        ],
        # If we set this, we got encrypted web page source:
        "Accept-Encoding": \
        [
            "gzip, deflate, br",
            "br, gzip, deflate",
            "gzip, deflate",
        ],
        "Accept-Language": \
        [
#             "fr-fr",
            "en-US,*",
            "en-US,en;q=0.5",
            "en-US,en;q=0.9",
#             "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
#             "fr-FR,fr;q=0.8,en-US;q=0.6,en;q=0.4",
        ],
        "User-Agent": \
        [
#             "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0_3 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A432 Safari/604.1",
#             "Googlebot/2.1 (+http://www.google.com/bot.html)",
#             "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0", # laptop
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36", # laptop
            "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:16.0) Gecko/20120815 Firefox/16.0", # laptop
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36", # laptop
            "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.57 Safari/537.36", # laptop
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.57 Safari/537.36", # laptop
            "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
#             "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0_3 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) CriOS/61.0.3163.73 Mobile/15A432 Safari/602.1",
        ]
    }

    duplicates = DomainDuplicate()



    def __init__(
                    self,
                    driverType=DRIVER_TYPE.chrome,
                    chromeDriverPath=None,
                    phantomjsPath=None, # "/home/hayj/Programs/headlessbrowsers/phantomjs-2.1.1-linux-x86_64/bin/phantomjs",
                    logger=None,
                    proxy=None,
                    name=None,
                    verbose=True,
                    loadImages=False,
                    beforeAjaxSleepCallback=None,
                    afterAjaxSleepCallback=None,
                    htmlCallback=None,
                    defaultScore=None,
                    durationHistoryCount=60, # 60 is a good choice
                    pageLoadTimeout=25,
                    maxDuplicatePerDomain=20,
                    checkProxyTimeout=5,
                    ajaxSleep=1.0, # > 3.0 for production crawl task
                    useTimeoutGet=True, # Use False here, True is not yet well implemented
                    headless=False,
                    useFastError404Detection=False,
                    durationHistory=None,
                ):
        self.urlParser = URLParser()
        self.useFastError404Detection = useFastError404Detection
        self.useTimeoutGet = useTimeoutGet
        self.lastIsDuplicate = False
        self.maxDuplicatePerDomain = maxDuplicatePerDomain
        Browser.duplicates.setMaxDuplicates(self.maxDuplicatePerDomain)
        self.beforeAjaxSleepCallback = beforeAjaxSleepCallback
        self.afterAjaxSleepCallback = afterAjaxSleepCallback
        self.name = name
        if self.name is None:
            self.name = getRandomName()
        self.verbose = verbose
        self.logger = logger
        self.pageLoadTimeout = pageLoadTimeout
        self.defaultScore = defaultScore
        if self.defaultScore is None:
            self.defaultScore = self.pageLoadTimeout
        self.checkProxyTimeout = checkProxyTimeout
        self.ajaxSleep = ajaxSleep
        self.htmlCallback = htmlCallback
        self.lastGetIsOk = None
        self.crawlingElement = None
        self.durationHistoryCount = durationHistoryCount
        self.durationHistory = durationHistory
        if self.durationHistory is None:
            self.durationHistory = getFixedLengthQueue(self.durationHistoryCount)
        self.cacheLock = Lock()

        # Driver:
        self.driverType = driverType
        self.headless = headless
        if self.driverType == DRIVER_TYPE.phantomjs:
            self.headless = True
        self.chromeDriverPath = chromeDriverPath
        self.phantomjsPath = phantomjsPath
        self.driver = None
        self.proxy = proxy
        self.loadImages = loadImages
        self.initDriver()

    def setWindowSize(self, x, y):
        self.driver.set_window_size(x, y)
    def setWindowPosition(self, x, y):
        self.driver.set_window_position(x, y)

    def getCrawlerName(self):
        if self.driverType == DRIVER_TYPE.phantomjs:
            return "phantomjs"
        elif self.driverType == DRIVER_TYPE.chrome:
            return "chrome"

    def initDriver(self):
        if self.driver is not None:
            logInfo(self.name + " will be killed!", self)
            okQuit = self.quit()
            if okQuit:
                logInfo(self.name + " killed!", self)
            else:
                logInfo(self.name + " can not be killed properly!", self)
        logInfo(self.name + " initialization...", self)
        if self.driverType == DRIVER_TYPE.phantomjs:
            self.generatePhantomjsHeader()
            self.initSeleniumDriver()
        else:
            self.initSeleniumDriver()
        self.generateRandomWindow()


    def initSeleniumDriver(self, retry=True):
        try:
            if self.driverType == DRIVER_TYPE.chrome:
                params = self.getChromeServiceArgs()
                if self.chromeDriverPath is not None:
                    params["executable_path"] = self.chromeDriverPath
                self.driver = webdriver.Chrome(**params)
            elif self.driverType == DRIVER_TYPE.phantomjs:
                params = {}
                if self.phantomjsPath is not None:
                    params["executable_path"] = self.phantomjsPath
                params["service_args"] = self.getPhantomJSServiceArgs()
                self.driver = webdriver.PhantomJS(**params)
            else:
                raise Exception("Not yet implemented!")
            self.driver.set_page_load_timeout(self.pageLoadTimeout)
        except Exception as e:
            if retry:
                time.sleep(2)
                self.initSeleniumDriver(retry=False)
            else:
                logException(e, self, message=self.name + " driver can't be init", location="initSeleniumDriver")

    def clone(self):
        return Browser \
        (
            headless=self.headless,
            driverType=self.driverType,
            chromeDriverPath=self.chromeDriverPath,
            phantomjsPath=self.phantomjsPath,
            logger=self.logger,
            proxy=self.proxy,
            name=None,
            verbose=self.verbose,
            loadImages=self.loadImages,
            beforeAjaxSleepCallback=self.beforeAjaxSleepCallback,
            afterAjaxSleepCallback=self.afterAjaxSleepCallback,
            htmlCallback=self.htmlCallback,
            defaultScore=self.defaultScore,
            durationHistoryCount=self.durationHistoryCount,
            pageLoadTimeout=self.pageLoadTimeout,
            maxDuplicatePerDomain=self.maxDuplicatePerDomain,
            checkProxyTimeout=self.checkProxyTimeout,
            ajaxSleep=self.ajaxSleep,
            useTimeoutGet=self.useTimeoutGet,
            durationHistory=self.durationHistory,
        )

    def log(self, text):
        if self.logger is not None:
            log(text, self)
        else:
            print(text)

    def getProxy(self):
        return self.proxy

    def randomHeader(self, seedWithProxy=True):
        header = {}
        if self.proxy is None or not seedWithProxy:
            for key, values in Browser.headers.items():
                header[key] = random.choice(values)
        else:
            headers = dict(Browser.headers)
            headers = sortBy(headers, index=0)
            ip = self.proxy["ip"]
            ip = ip.replace(".", "")
            theSeed = int(ip)
            rd = Random()
            rd.setSeed(theSeed)
            for key, values in headers:
                choice = rd.getRandomInt(len(values) - 1)
                value = values[choice]
                header[key] = value
            rd.resetSeed()
        return header

    def generatePhantomjsHeader(self):
        header = self.randomHeader()
        userAgent = header["User-Agent"]
        del header["Accept-Encoding"]
        del header["User-Agent"]
        for key, value in header.items():
            capabilityKey = 'phantomjs.page.customHeaders.{}'.format(key)
            webdriver.DesiredCapabilities.PHANTOMJS[capabilityKey] = value
        webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.userAgent'] = userAgent

    def randomWindow(self, seedWithProxy=True):
        if self.proxy is None or not seedWithProxy:
            return (getRandomInt(1100, 2000), getRandomInt(800, 1200))
        else:
            ip = self.proxy["ip"]
            ip = ip.replace(".", "")
            theSeed = int(ip)
            randomInts = getRandomInt(900, 1300, seed=theSeed, count=2)
            width = randomInts[0] + 600
            height = randomInts[1]
            return (width, height)

    def generateRandomWindow(self):
        if self.driver is not None:
            (width, height) = self.randomWindow()
            self.driver.set_window_size(width, height)

    def getScrapedHeader(self):
        headerSources = \
        [
            ("https://www.whatismybrowser.com/detect/what-http-headers-is-my-browser-sending", ".table"),
#             ("http://www.procato.com/my+headers", ".containerInner"),
#             ("http://httpbin.org/headers", None),
        ]
        urlParser = self.urlParser
        allHeaders = {}
        for url, cssSelector in headerSources:
            try:
                domain = urlParser.getDomain(url, urlLevel=URLLEVEL.ALL)
                self.driver.get(url)
                if cssSelector is not None:
                    header = self.driver.find_element_by_css_selector(cssSelector).text
                    header = header.strip().split("\n")
                    newHeader = []
                    for current in header:
                        if not (current.lower().startswith("host") or current.lower().startswith("referer")):
                            newHeader.append(current)
                    header = newHeader
                else:
                    header = self.driver.page_source
                allHeaders[domain] = header
            except: pass
        return listToStr(allHeaders)

    def meanDuration(self):
        return queueMean(self.durationHistory, defaultValue=self.defaultScore)

    def getDriverData(self):
        lastUrl = None
        title = None
        html = None
        try:
            lastUrl = self.driver.current_url
            title = self.driver.title.strip()
            html = self.driver.page_source
        except Exception as e:
            if not isinstance(e, TimeoutException):
                logError(str(type(e)), self)
                logError("Exception location: browser.getDriverData()\n" + str(e), self)
#             else:
#                 logException(e, self)
        return (title, html, lastUrl)

    def acquire(self):
        self.cacheLock.acquire()

    def tryRelease(self):
        try:
            self.cacheLock.release()
        except Exception as e:
            logError("Exception location: browser.tryRelease()\n" + str(e), self)


    def timeoutGet(self, crawlingElement):
        if self.useTimeoutGet:
            def threadedGet():
                try:
                    self.driver.get(crawlingElement.data)
                except Exception as e:
                    if not isinstance(e, TimeoutException):
                        logException(e, self, location="threadedGet")
            theThread = Thread(target=threadedGet)
            theThread.start()
            theThread.join(1.3 * self.pageLoadTimeout)
            if theThread.isAlive():
                self.initDriver()
                raise Exception("The timeout didn't work.")
        else:
            self.driver.get(crawlingElement.data)

    @staticmethod
    def isGoodStatus(status):
        if status.name in "success error404 timeoutWithContent".split(" "):
            return True
        else:
            return False

    def get(self, crawlingElement, pipCallback=None):
        """
            This function return True if the request succeeded.
        """
        # We convert the url:
        crawlingElement = tryUrlToCrawlingElement(crawlingElement)

        # Here we have a callback, we have to cacheLock the object:
        if self.htmlCallback is not None:
            self.acquire()
        try:
            # And now we can get the html and retain time duration:
            tt = TicToc()
            tt.tic(display=False)
#             logInfo("Launching get for: " + str(url))
            if crawlingElement.type == CrawlingElement.TYPE.pipedMessage:
                pipCallback(self, crawlingElement) # Here the url is a piped message
            else:
                self.stopLoadingAndLoadBlank()
#                 logInfo("Get starting...", self)
                self.timeoutGet(crawlingElement)
#                 logInfo("Get DONE", self)
#             logInfo("get done for: " + str(url))

#             global debugCount
#             debugCount += 1

            # For chrome we must try to get the source to see if we are on a timeout exception:
            try:
                self.driver.page_source
            except Exception as e:
                if isinstance(e, TimeoutException):
                    raise TimeoutException()

            # We finally got something without exception, so we try to get data:
            (title, html, lastUrl) = self.getDriverData()

            # But here, if the status is not success, we set diffTime as the max:
            diffTime = tt.tic(display=False)
            if Browser.isGoodStatus(self.getStatus(True, crawlingElement, lastUrl, title, html)):
                diffTime = self.pageLoadTimeout

            # We add the score to the history:
            self.durationHistory.append(diffTime)

            # And we keep currentUrl and ok status for the "html()" method:
            self.currentCrawlingElement = crawlingElement
            self.lastGetIsOk = True
            self.lastIsDuplicate = False
            if title is not None and html is not None \
            and crawlingElement.type == CrawlingElement.TYPE.uniqueUrl:
                self.lastIsDuplicate = Browser.duplicates.isDuplicate \
                (
                    crawlingElement.data,
                    title,
                    html
                )

            # Finally we exec the finally statement and we return True (i.e. request ok):
            return True
        except Exception as e:
            if not isinstance(e, TimeoutException):
                logError("Exception location: browser.get()\n" + str(e), self)
            # Here we got a timeout, so we set the score as the badest:
            self.durationHistory.append(self.pageLoadTimeout)

            # And we keep url and ok status for the "html()" method:
            self.currentCrawlingElement = crawlingElement
            self.lastGetIsOk = False

            # Finally we exec the finally statement and we return False (i.e. failed):
            return False
        # The finally is executed before the return statement
        finally:
            # If the request succeeded:
            if self.lastGetIsOk:
                # First if this is a duplicates (i.e. a "you've been blocked" page for instance),
                # we don't need to sleep but we call the callback to keep aware the crawler:
                if self.lastIsDuplicate:
                    theThread = Thread(target=self.noAjaxSleepThenCallback)
                    theThread.start()
                # Then if we don't have any callback, the caller of this funct is the
                # "html()" method of this object, so we just need to sleep:
                elif self.htmlCallback is None:
                    self.doAjaxSleep()
                # Else if we actually have a right web page without timeout
                # We sleep and we call the callback:
                else:
                    theThread = Thread(target=self.ajaxSleepThenCallback)
                    theThread.start()
            # If we got a timeout, we don't need to sleep:
            else:
                # If there are no callback, we don't do anything:
                if self.htmlCallback is None:
                    pass
                # Else we don't sleep but call the callback:
                # Or we have to sleep because we can have a timeoutWithContent...
                else:
                    theThread = Thread(target=self.noAjaxSleepThenCallback)
                    theThread.start()
#             self.tryRelease()

    def timeoutStopLoadingAndLoadBlank(self):
        self.stopLoadingSucceded = False
        self.loadBlankSucceded = False
        def threadedSLLB():
            self.stopLoadingSucceded = self.stopLoading()
            self.loadBlankSucceded = self.loadBlank()
        theThread = Thread(target=threadedSLLB)
        theThread.start()
        theThread.join(15)
        if not self.loadBlankSucceded or theThread.isAlive():
            errorMessage = "Can't load blank for " + self.name
            logError(errorMessage, self)
            self.initDriver() # Kill the driver

    def stopLoadingAndLoadBlank(self):
        self.timeoutStopLoadingAndLoadBlank()

    def loadBlank(self):
        try:
            self.driver.get("about:blank")
            return True
        except Exception as e:
#             logException(e, self, location="Browser.loadBlank()")
            logError("Exception caught in Browser.loadBlank().", self)
            return False

    def stopLoading(self):
        try:
            self.driver.execute_script("window.stop();")
            self.driver.find_elements_by_css_selector("*")[0].send_keys(Keys.CONTROL + 'Escape')
            return True
        except Exception as e:
#             logException(e, self, location="Browser.stopLoading()")
            logError("Exception caught in Browser.stopLoading().", self)
            return False

    def doAjaxSleep(self):
        if self.beforeAjaxSleepCallback is not None:
            self.beforeAjaxSleepCallback(self)
        if self.ajaxSleep > 0.0:
            time.sleep(self.ajaxSleep)
        if self.afterAjaxSleepCallback is not None:
            self.afterAjaxSleepCallback(self)

    def noAjaxSleepThenCallback(self):
        try:
            self.html()
        except Exception as e:
            logError("Exception location: browser.noAjaxSleepThenCallback()\n" + str(e), self)
        self.tryRelease()

    def ajaxSleepThenCallback(self):
        self.doAjaxSleep()
        try:
            self.html()
        except Exception as e:
            logError("Exception location: browser.ajaxSleepThenCallback()\n" + str(e), self)
        # Here we terminated the sleep and the callback, so we can unlock the object:
        self.tryRelease()

    def isTimeoutWithContent(self, lastUrl, title, html):
        """
            Return False if it is a true timeout
            True instead (in case we got content)
        """
        if lastUrl is None or lastUrl.strip() == "" \
        or title is None or title.strip() == "" \
        or html is None or html.strip() == "" \
        or lastUrl == "about:blank":
            return False
        if "</body>" in html \
        and len(html) > 100:
            return True
        return False


    def getStatus(self, ok, crawlingElement, lastUrl, title, html):
        """
            The only difference to call this method in "get()" vs in "html()"
            is the the lastUrl can change du to js redirection...
            The html can change too, but it's not important to get the status
        """
        if not ok:
            if self.isTimeoutWithContent(lastUrl, title, html):
                currentStatus = self.getStatus(True, crawlingElement, lastUrl, title, html)
                if currentStatus == REQUEST_STATUS.success:
                    return REQUEST_STATUS.timeoutWithContent
                else:
                    return currentStatus
            else:
                return REQUEST_STATUS.timeout
        elif isRefused(html, lastUrl):
            return REQUEST_STATUS.refused
        elif isInvalidHtml(html):
            return REQUEST_STATUS.invalid
        elif is404Error(html, fast=self.useFastError404Detection):
            return REQUEST_STATUS.error404
        elif crawlingElement.type == CrawlingElement.TYPE.uniqueUrl \
        and Browser.duplicates.isDuplicate(lastUrl, title, html):
            return REQUEST_STATUS.duplicate
        else:
            return REQUEST_STATUS.success


    def html(self, crawlingElement=None):
        """
            This function return data. Call "get" method instead if you gave a htmlCallback.
        """
        # We convert the url:
        crawlingElement = tryUrlToCrawlingElement(crawlingElement)
        currentCrawlingElement = crawlingElement
        if currentCrawlingElement is None:
            currentCrawlingElement = self.currentCrawlingElement
        # We construct data:
        data = \
        {
            "proxy": self.getIp(),
            "crawlingElement": currentCrawlingElement,
            "url": str(currentCrawlingElement.data),
            "domain": self.urlParser.getDomain(currentCrawlingElement.data, urlLevel=URLLEVEL.SMART),
            "browser": self.driverType.name,
            "lastUrl": None,
            "lastUrlDomain": None,
            "html": None,
            "title": None,
            "status": None,
        }

        try:
            # Here it's the user who call this method:
            if crawlingElement is not None:
                ok = self.get(crawlingElement)
            # Here if the htmlCallback is not None, it's the get method which call html():
            elif self.htmlCallback is not None:
                crawlingElement = self.currentCrawlingElement
                # We convert the url:
                crawlingElement = tryUrlToCrawlingElement(crawlingElement)
                ok = self.lastGetIsOk
            else:
                logError("You can't be in both scenarios described in the doc.", self)
                exit()

            # No we try to get some data:
            (title, html, lastUrl) = self.getDriverData()

            # And we get the status:
            status = self.getStatus(ok, crawlingElement, lastUrl, title, html)

            # Now we got all data, so we can make the data dict:
            data["status"] = status
            data["lastUrl"] = lastUrl
            data["lastUrlDomain"] = self.urlParser.getDomain(lastUrl, urlLevel=URLLEVEL.SMART)
            data["html"] = html
            data["title"] = title

            # And we log informations:
            ip = " "
            if self.proxy is not None:
                ip = " (" + self.proxy["ip"] + ") "
            logInfo(str(status.name) + " from " + self.name + ip + str(crawlingElement.data), self)
            if status == REQUEST_STATUS.duplicate:
                logInfo("Title of the duplicated page: " + str(title), self)
        except Exception as e:
            logError("Exception location: browser.html()\n" + str(e), self)
            data["status"] = REQUEST_STATUS.exception
        # Now if we have a callback, we have to throw the data:
        if self.htmlCallback is not None:
            self.htmlCallback(data, self)
        # Or we just return it:
        else:
            return data
        return None

    def getIp(self):
        proxyForData = None
        if self.proxy is not None:
            proxyForData = self.proxy["ip"]
        return proxyForData

    def getUserAgent(self):
        return self.driver.execute_script("return navigator.userAgent")

    def setProxy(self, ip, port=80, user=None, password=None, type="http"):
        self.proxy = {}
        self.proxy["ip"] = ip
        self.proxy["port"] = port
        self.proxy["user"] = user
        self.proxy["password"] = password
        self.proxy["type"] = type




#     def launch(self, urlList):
#         if not isinstance(urlList, list):
#             urlList = [urlList]
#         if len(urlList) == 1 and (urlList[0] is None or urlList[0] == ""):
#             return None
#
#         for currentUrl in urlList:
#             self.driver.get(currentUrl)
#             return self.driver.page_source

    def getPids(self):
        pids = None
        # https://stackoverflow.com/questions/10752512/get-pid-of-browser-launched-by-selenium
        try:
            if self.driverType == DRIVER_TYPE.phantomjs:
                pids = [self.driver.service.process.pid]
            else:
                p = psutil.Process(self.driver.service.process.pid)
                pids = []
                for current in p.children(recursive=True):
                    pids.append(current.pid)
        except Exception as e:
            logException(e, self, location="getPids")
        return pids

    def killPids(self, pids):
        if pids is None or len(pids) == 0:
            return False
        atLeastOneFailed = False
        for pid in pids:
            try:
                p = psutil.Process(pid)
                p.kill() # or p.terminate()
            except Exception as e:
                if not isinstance(e, psutil.NoSuchProcess):
                    logException(e, self, location="Browser.killPids()")
                    atLeastOneFailed = True
        if atLeastOneFailed:
            return False
        else:
            return True

    def kill(self):
        pids = self.getPids()
        return self.killPids(pids)

    def close(self):
        self.quit()

    def timeoutQuit(self):
        def threadedQuit():
            self.driver.quit()
        theThread = Thread(target=threadedQuit)
        theThread.start()
        theThread.join(15)
        if theThread.isAlive():
            errorMessage = "Can't quit " + self.name
#             logError(errorMessage, self)
            raise Exception(errorMessage)

    def quit(self):
        closed = False
        i = 0
        while not closed and i < 3:
            try:
                pids = self.getPids()
                self.timeoutQuit()
                self.killPids(pids)
                closed = True
            except Exception as e:
#                 logException(e, self, location="browser.closed()")
                logError("Exception caught in Browser.quit().", self)
                closed = self.kill()
                if not closed:
                    time.sleep(0.2)
                    i += 1
        return closed

    def getPhantomJSServiceArgs(self):
        if self.proxy is None:
            return None
        params = \
        [
            '--proxy=' + self.proxy["ip"] + ':' + self.proxy["port"],
            '--proxy-type=http',
            '--proxy-auth=' + self.proxy["user"] + ':' + self.proxy["password"],
            '--load-images=no',
        ]
        if not self.loadImages:
            params.append('--load-images=no')
        return params

    def getChromeServiceArgs(self):
        """
            You can't use both a proxy auth and the headless option
            So the ip of the machine have to be whitlisted by your proxies provider
        """
        options = Options()
        if self.proxy is not None and not self.headless:
            manifest_json = """
            {
                "version": "1.0.0",
                "manifest_version": 2,
                "name": "Chrome Proxy",
                "permissions": [
                    "proxy",
                    "tabs",
                    "unlimitedStorage",
                    "storage",
                    "<all_urls>",
                    "webRequest",
                    "webRequestBlocking"
                ],
                "background": {
                    "scripts": ["background.js"]
                },
                "minimum_chrome_version":"22.0.0"
            }
            """

            background_js = """
            var config = {
                    mode: "fixed_servers",
                    rules: {
                      singleProxy: {
                        scheme: "http",
                        host: \"""" + self.proxy["ip"] + """\",
                        port: parseInt(""" + self.proxy["port"] + """)
                      },
                      bypassList: ["foobar.com"]
                    }
                  };

            chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

            function callbackFn(details) {
                return {
                    authCredentials: {
                        username: \"""" + self.proxy["user"] + """\",
                        password: \"""" + self.proxy["password"] + """\"
                    }
                };
            }

            chrome.webRequest.onAuthRequired.addListener(
                        callbackFn,
                        {urls: ["<all_urls>"]},
                        ['blocking']
            );
            """

            proxyPluginName = "proxy_auth_plugin"
            pluginTmpDir = tmpDir(subDir=proxyPluginName)
            purgeOldFiles(pluginTmpDir + "/" + proxyPluginName + "*.zip", 1000.0)
            pluginfile = pluginTmpDir + '/' + proxyPluginName + '_' + getRandomStr() + '.zip'

            with zipfile.ZipFile(pluginfile, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)

            options.add_extension(pluginfile)
        elif self.proxy is not None and self.headless:
            # Here you must whitelist you ip to don't need user password:
            options.add_argument('--proxy-server=' + self.proxy["ip"] + ":" + self.proxy["port"])

        options.add_argument("--start-maximized")

        if self.headless:
            options.add_argument('headless')

        (width, height) = self.randomWindow()
        options.add_argument('window-size=' + str(width) + 'x' + str(height))

        # Now we set the header:
        header = self.randomHeader()
        options.add_argument("user-agent=" + header["User-Agent"]) # WORKS
#         options.add_argument("accept=" + header["Accept"]) # Doesn't work
#         options.add_argument("accept-encoding=" + header["Accept-Encoding"]) # Doesn't work
        options.add_experimental_option('prefs', {'intl.accept_languages': "en-US,en"}) # WORKS but only en-US,en;q=0.9, it doesn't work with header["Accept-Language"]

        params = {}
        params["chrome_options"] = options
        return params


    def linkedInConnexion(self, user=u"opuire.malaire@tutanota.com", password=u"753êµ$UfD5"):
        """
        # class login-email et login-password find_element_by_class_name
        """
        usernameInput = self.browser.find_element_by_class_name("login-email")
        passwordInput = self.browser.find_element_by_class_name("login-password")

        usernameInput.send_keys(user)
        passwordInput.send_keys(password)

        self.browser.find_element_by_class_name("submit-button").click()

    def checkProxy(self):
        """
            This method return False if the proxy is not correctly set.
        """
        if self.proxy is None:
            logError("Proxy not correctly set.", self)
            return False
        else:
            webSiteList = \
            [
                "http://fr.geoipview.com",
                # On this web site with a proxy, the page load a lot of "near ip", so it's slow:
                # "http://www.localiser-ip.com",
                "http://www.mon-ip.com",
                "https://www.expressvpn.com/what-is-my-ip",
                "https://www.adresseip.com",
            ]

            def getWebSiteIP(url):
                try:
                    data = self.html(url)["html"]
                    ip = re.search("\d+[.]\d+[.]\d+[.]\d+", data).group(0)
                    return ip
                except Exception as e:
#                     logWarning("Ip not found in " + url + " " + str(e), self)
                    return None

            self.driver.set_page_load_timeout(self.checkProxyTimeout)
            previousAjaxSleep = self.ajaxSleep
            self.ajaxSleep = 0.0
            ipWhithoutProxy = getIP()
            success = False
            # log("This computer ip is " + ipWhithoutProxy, self)
            for current in webSiteList:
                proxyIP = getWebSiteIP(current)
                if proxyIP is not None:
                    if self.proxy["ip"] != proxyIP:
                        break
                    if proxyIP == ipWhithoutProxy:
                        break
                    success = True
                    break
            self.ajaxSleep = previousAjaxSleep
            self.driver.set_page_load_timeout(self.pageLoadTimeout)
            if success:
                log("Successfully init " + self.name + " with proxy " + proxyIP, self)
                return True
            else:
                logWarning(self.name + " failed to use proxy " + self.proxy["ip"], self)
                return False




if __name__ == "__main__":
    print("a")




