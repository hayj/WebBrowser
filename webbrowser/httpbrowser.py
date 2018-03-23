# coding: utf-8

# pew in webcrawler-venv python ~/wm-dist-tmp/WebCrawler/webcrawler/httpbrowser.py

import requests
from datatools.url import *
from urllib.request import urlopen
from systemtools.basics import *
from systemtools.location import *
from systemtools.logger import *
import requests.auth
from datastructuretools.hashmap import *
from webbrowser.utils import *
from webbrowser.browser import *
try:
    from newstools.newsscraper import *
except: pass
from bs4 import BeautifulSoup

def proxyStrToProxyDict(proxyStr):
    theTuple = proxies[i].split(":")
    theDict = {}
    theDict["ip"] = theTuple[0]
    theDict["port"] = theTuple[1]
    if len(theTuple) > 2:
        theDict["user"] = theTuple[2]
    if len(theTuple) > 3:
        theDict["password"] = theTuple[3]
    theDict["type"] = "http"
    return theDict

def htmlTitle(html):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title
    if title is not None:
        title = strip(title.string)
    return title

class HTTPBrowser():
    duplicates = DomainDuplicate()
    urlParser = URLParser()
    def __init__ \
    (
        self,
        logger=None,
        verbose=True,
        proxy=None,
        maxRetryWithoutProxy=0,
        maxRetryIfTimeout=1,
        maxRetryIf407=1,
        portSet=["80", "55555"],
        retrySleep=1.0,
        defaultScore=None,
        pageLoadTimeout=25,
        htmlCallback=None,
        name=None,
        maxDuplicatePerDomain=20,
        durationHistoryCount=60,
        durationHistory=None,
    ):
        self.maxDuplicatePerDomain = maxDuplicatePerDomain
        HTTPBrowser.duplicates.setMaxDuplicates(self.maxDuplicatePerDomain)
        self.name = name
        self.driver = None
        if self.name is None:
            self.name = getRandomName()
        self.portSet = portSet
        self.retrySleep = retrySleep
        self.htmlCallback = htmlCallback
        self.setTimeout(pageLoadTimeout)
        self.defaultScore = defaultScore
        if self.defaultScore is None:
            self.defaultScore = self.pageLoadTimeout
        self.durationHistoryCount = durationHistoryCount
        self.durationHistory = durationHistory
        if self.durationHistory is None:
            self.durationHistory = getFixedLengthQueue(self.durationHistoryCount)
        # Retry max counts:
        self.maxRetryWithoutProxy = maxRetryWithoutProxy
        self.maxRetryIfTimeout = maxRetryIfTimeout
        self.maxRetryIf407 = maxRetryIf407
        self.logger = logger
        self.verbose = verbose
        self.setProxy(proxy)
        self.initHeader()

    def setTimeout(self, *args, **kwargs):
        self.setPageLoadTimeout(*args, **kwargs)
    def setPageLoadTimeout(self, timeout):
        self.pageLoadTimeout = timeout

    def meanDuration(self):
        return queueMean(self.durationHistory, defaultValue=self.defaultScore)

    def clone(self):
        return HTTPBrowser \
        (
            logger=self.logger,
            verbose=self.verbose,
            proxy=self.proxy,
            maxRetryWithoutProxy=self.maxRetryWithoutProxy,
            maxRetryIfTimeout=self.maxRetryIfTimeout,
            maxRetryIf407=self.maxRetryIf407,
            portSet=self.portSet,
            retrySleep=self.retrySleep,
            defaultScore=self.defaultScore,
            pageLoadTimeout=self.pageLoadTimeout,
            htmlCallback=self.htmlCallback,
            name=self.name,
            maxDuplicatePerDomain=self.maxDuplicatePerDomain,
            durationHistoryCount=self.durationHistoryCount,
            durationHistory=self.durationHistory,
        )

    def initHeader(self, seedWithProxy=True):
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
        self.header = header

    @staticmethod
    def isGoodStatus(status):
        if status.name in "success error404 timeoutWithContent".split(" "):
            return True
        else:
            return False

    def setProxy(self, proxy):
        self.proxy = proxy
        self.proxyStr = None
        self.proxyIpStr = None
        if self.proxy is not None and isinstance(proxy, str):
            self.proxy = proxyStrToProxyDict(self.proxy)
        # We add the current port to port set:
        if self.hasProxy():
            self.portSet.append(self.proxy["port"])
            self.portSet = list(set(self.portSet))

    def hasProxy(self):
        return self.proxy is not None

    def getCrawlerName(self):
        return "requests"

    def getProxy(self):
        return self.proxy

    def html(self, *args, **kwargs):
        return self.get(*args, **kwargs)
    def get(self, *args, **kwargs):
        self.countRetryWithoutProxy = 0
        self.countRetryIfTimeout = 0
        self.countRetryIf407 = 0
        return self.privateGet(*args, **kwargs)

    def privateGet(self, crawlingElement, forcedPort=None, noProxy=False, isARetry=False, **kwargs):
        """
            This function return data, it call htmlCallbcak if given at __init__
        """
        # This function return the result and call the htmlCallback too:
        def returner(result):
            if self.htmlCallback is not None:
                try:
                    self.htmlCallback(result, self)
                except Exception as e:
                    logException(e, self, location="returner(result)")
            if not isARetry:
                self.printStatusMessage(result)
            return result
        # We convert the url:
        crawlingElement = tryUrlToCrawlingElement(crawlingElement)
        url = crawlingElement.data
        # Now we set the right port:
        if forcedPort is None and self.hasProxy():
            forcedPort = self.proxy["port"]
        # We parse the url:
        url = HTTPBrowser.urlParser.normalize(url)
        domain = HTTPBrowser.urlParser.getDomain(url, urlLevel=URLLEVEL.SMART)
        # We set the proxy string:
        if self.hasProxy() and not noProxy:
            self.proxyIpStr = self.proxy["ip"]
            self.proxyStr = "http://" + self.proxy["ip"] + ":" + forcedPort
        else:
            self.proxyIpStr = None
            self.proxyStr = None
        # We prepare the result:
        result = \
        {
            "proxy": self.proxyIpStr,
            "lastUrl": None,
            "crawlingElement": crawlingElement,
            "url": url,
            "domain": domain,
            "browser": "http",
            "lastUrlDomain": None,
            "historyCount": None,
            "redirected": None,
            "status": None,
            "httpStatus": None,
            "message": None,
            "html": None,
            "title": None,
        }
        # We retain the time start:
        tt = TicToc()
        tt.tic(display=False)
        # And we launch the request:
        response = None
        try:
            if self.hasProxy():
                response = requests.get \
                (
                    url,
                    proxies= \
                    {
                        "http": self.proxyStr,
                        "https": self.proxyStr,
                    },
                    timeout=self.pageLoadTimeout,
                    headers=self.header,
#                     cookies={'preview': '1'},
                )
            else:
                response = requests.get(url, timeout=self.pageLoadTimeout, headers=self.header,)
            # Now we retain the diff time:
            diffTime = tt.tic(display=False)
        # Now if we got an error:
        except Exception as ex:
            # Here we have an exception, so the diff time is the max:
            diffTime = self.pageLoadTimeout
            # We get e as a lowered string:
            e = str(ex)
            if e is None:
                e = ""
            e = e.lower()
            e = e.replace('\n', ' ')
            # We check if it is a 407:
            is407 = False
            if "407" in e and "proxy" in e:
                is407 = True
            # We get a new port for retry:
            ports = list(self.portSet)
            if forcedPort in ports:
                ports.remove(forcedPort)
            if len(ports) > 0:
                forcedPort = random.choice(ports)
            # We check if it is a timeout:
            isTimeout = False
            if isinstance(ex, requests.exceptions.Timeout):
                isTimeout = True
            # We write the error message:
            if isTimeout:
                errorMessage = "Getting " + url + " timeout. " + e
            elif is407:
                errorMessage = "Enable to connect to the proxy for " + url + " " + e
            else:
                errorMessage = "Getting " + url + " error. " + e
            logError(errorMessage, self)
            # Now we check if we have to retry the request:
            hasToRetry = False
            noProxy = not self.hasProxy()
            # Now we retry if we have a timeout:
            if isTimeout:
                if self.countRetryIfTimeout < self.maxRetryIfTimeout:
                    self.countRetryIfTimeout += 1
                    hasToRetry = True
                    noProxy = False
                    logError("The request to " + url + " failed. We retry on an other proxy port.")
            # If we have a 407 we retry:
            elif is407:
                if self.countRetryIf407 < self.maxRetryIf407:
                    self.countRetryIf407 += 1
                    hasToRetry = True
                    noProxy = False
                    logError("The proxy connexion failed (" + self.proxyStr + "). We retry on an other proxy port.")
            # Else we retry:
            else:
                if self.countRetryWithoutProxy < self.maxRetryWithoutProxy:
                    self.countRetryIf407 += 1
                    hasToRetry = True
                    noProxy = True
            # And finally we retry:
            if hasToRetry:
                randomSleep(self.retrySleep)
                result = self.privateGet(url, forcedPort=forcedPort, noProxy=noProxy, isARetry=True)
                # We add the score to the history if this is not a retry:
                if not isARetry:
                    self.durationHistory.append(diffTime)
                return returner(result)
            else:
                # Here we didn't get the data, we return an error:
                result["message"] = errorMessage
                # We set the status:
                if isTimeout:
                    result["status"] = REQUEST_STATUS.timeout
                else:
                    result["status"] = REQUEST_STATUS.refused
                # We set the http status:
                if is407:
                    result["httpStatus"] = 407
                elif isTimeout:
                    result["httpStatus"] = 408
                elif isinstance(ex, requests.exceptions.RequestException):
                    result["httpStatus"] = 500
                elif isinstance(ex, requests.exceptions.ConnectionError):
                    result["httpStatus"] = 503
                elif isinstance(ex, requests.exceptions.HTTPError):
                    result["httpStatus"] = 500
                elif isinstance(ex, requests.exceptions.TooManyRedirects):
                    result["httpStatus"] = 310
                else:
                    result["httpStatus"] = 500
                # We add the score to the history if this is not a retry:
                if not isARetry:
                    self.durationHistory.append(diffTime)
                return returner(result)
        try:
            # We add the score to the history:
            self.durationHistory.append(diffTime)
            # Here we got a response, so we just get data:
            if response.history:
                historyCount = 0
                for _ in response.history:
                    historyCount += 1
                result["historyCount"] = historyCount
                result["redirected"] = True
            else:
                result["historyCount"] = 0
                result["redirected"] = False
            result["httpStatus"] = response.status_code
            result["lastUrl"] = response.url
            result["lastUrlDomain"] = HTTPBrowser.urlParser.getDomain(response.url, urlLevel=URLLEVEL.SMART)
            result["html"] = response.text
            result["title"] = htmlTitle(response.text)
            # Next we compute the status of the response
            if response.status_code == 404: # or response.status_code == 403
                result["status"] = REQUEST_STATUS.error404
            elif isRefused(response.text, response.url):
                result["status"] = REQUEST_STATUS.refused
            elif isInvalidHtml(response.text):
                result["status"] = REQUEST_STATUS.invalid
            elif not (response.status_code >= 200 and response.status_code <= 226):
                result["status"] = REQUEST_STATUS.refused
            elif HTTPBrowser.duplicates.isDuplicate(url=result["lastUrl"], html=result["html"]):
                result["status"] = REQUEST_STATUS.duplicate
            else:
                result["status"] = REQUEST_STATUS.success
            # And finally we return the result:
            return returner(result)
        except Exception as e:
            # If we can't acces to attribute, we just send the result with status exception:
            errorMessage = "Cannot access response attribute " + str(e)
            logError(errorMessage + " " + str(e), self)
            result["message"] = errorMessage
            result["status"] = REQUEST_STATUS.exception
            return returner(result)

    def printStatusMessage(self, result):
        message = ""
        message += str(result["status"].name) + " (" + str(result["httpStatus"]) + ")"
        message += " from " + self.name + " (" + self.proxy["ip"] + ")"
        message += " " + result["url"]
        log(message, self)

    def close(self):
        pass
    def quit(self):
        pass
    def checkProxy(self):
        logError("checkProxy not yet implemented!")
        return True

if __name__ == '__main__':
    urls = \
    [
        "http://bit.ly/2AGvbIz",
        "http://httpbin.org/redirect/3",
        "https://api.ipify.org/?format=json",
        "https://www.linkedin.com/?originalSubdomain=fr",
        "http://bit.ly/21vCb1P",
        "http://apprendre-python.com/page-apprendre-variables-debutant-python",
        "www.mon-ip.com/dsfdsgdrfg",
        "husdgfvsddsfsd.com",
    ]

#     (user, password, host) = getStudentMongoAuth()
#     collection = MongoCollection("crawling", "taonews",
#                                  user=user, password=password, host=host)
#     for current in collection.find():
#         url = current["last_url"]
#         if getRandomFloat() > 0.9:
#             urls.insert(0, url)
#         if len(urls) > 50:
#             break

    urls.insert(0, "https://lasvegassun.com/news/2017/jan/14/report-raiders-to-file-relocation-papers-to-move-f/")

    urls = [
"https://www.africa.upenn.edu/Articles_Gen/Letter_Birmingham.html", # 200 invalid
"https://www.washingtontimes.com/news/2017/jan/29/survivor-of-wwii-secret-escape-from-nazis-dies-in-/?utm_source=dlvr.it&utm_medium=twitter", # 200 invalid
"https://www.washingtontimes.com/news/2017/jan/29/attorney-generals-of-16-states-condemn-trumps-trav/?utm_source=dlvr.it&utm_medium=twitter", # 200 invalid
"https://www.huffingtonpost.com/entry/200-buses-have-applied-for-inauguration-parking-1200-for-the-womens-march_us_5878e7dfe4b09281d0ea697f?ncid=engmodushpmg00000004", # 500
"https://www.thedailybeast.com/terrorist-troll-pretended-to-be-isis-white-supremacist-and-jewish-lawyer", # 403
"http://dailycaller.com/2017/01/14/heads-are-finally-beginning-to-roll-at-the-clinton-foundation", # 403
"https://lasvegassun.com/news/2017/jan/14/report-raiders-to-file-relocation-papers-to-move-f", # 403
"https://www.thedailybeast.com/trump-could-address-these-legitimacy-questionsbut-he-wont", # 403
"https://viralbot360.wordpress.com/2017/01/30/here-are-some-of-the-most-powerful-images-from-airport-protests-across-the-us", # 410
"http://dailycaller.com/2017/01/29/donald-trump-defends-his-executive-order-this-is-not-a-muslim-ban", # 403
"http://www.billboard.com/articles/columns/pop/7670007/fifth-harmony-cancels-nhl-all-star-game-national-anthem", # 403
"http://www.hollywoodreporter.com/bookmark/trump-tweet-sends-john-lewis-book-sales-soaring-964415", # 403

"https://evesdaughter14.wordpress.com/2017/01/29/c-i-inmates-list-write-a-letter", # 410
]

    proxy = getRandomProxy()
    httpBrowser = HTTPBrowser(proxy=proxy)

    for url in urls:
#         proxy = getRandomProxy()
#         if isHostname("datas"):

        result = httpBrowser.get(url)
        reducedResult = reduceDictStr(result, max=500, replaceNewLine=True)
        del reducedResult["crawlingElement"]
        printLTS(reducedResult)
        html = result["html"]
        textNewsPaper = ""
        textBoilerpipe = ""
        if html is not None:
            textNewsPaper = NewsScraper().scrap(html, scrapLib=NewsScraper.SCRAPLIB.newspaper)["newspaper"]["text"]
            textBoilerpipe = NewsScraper().scrap(html, scrapLib=NewsScraper.SCRAPLIB.boilerpipe)["boilerpipe"]["text"]

        text = "RESULT\n\n\n"
        text += listToStr(reducedResult) + "\n\n\n"
        if textNewsPaper is not None:
            text += "NEWSPAPER\n\n\n"
            text += textNewsPaper + "\n\n\n"
        if textBoilerpipe is not None:
            text += "BOILERPIPE\n\n\n"
            text += textBoilerpipe + "\n\n\n"


        if text is not None:
            textFilePath = strToTmpFile(text, "text", "txt", addRandomStr=False, subDir="httpbrowser-test")
        if html is not None:
            htmlFilePath = strToTmpFile(html, "html", "html", addRandomStr=False, subDir="httpbrowser-test")

        input()

        removeFile(textFilePath)
        removeFile(htmlFilePath)




        # TODO test sur datas












