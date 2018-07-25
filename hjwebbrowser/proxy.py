
from systemtools.basics import *
from systemtools.file import *
from systemtools.logger import *
from systemtools.location import *
from systemtools.system import *
import requests
import requests.auth


PROXY_DESC = Enum("PROXY_DESC", "ip port user password type")

class Proxy:
    """
        See the unit test Python script to have more information
        A str proxy is formated like these examples:
         * 107.150.77.161
         * 107.150.77.161:80
         * 107.150.77.161:80:user:password
         * 107.150.77.161:80:::
         * 107.150.77.161:80:::http
         * 107.150.77.161:80:::socks
    """
    def __init__\
    (
        self,
        proxyStr,
        defaults={"type": "http", "port": "80"},
        logger=None,
        verbose=True,
        equalityExclude=["user", "password"],
    ):
        if isinstance(proxyStr, Proxy):
            proxyStr = repr(proxyStr)
        self.equalityExclude = equalityExclude
        self.proxyStr = proxyStr
        self.logger = logger
        self.verbose = verbose
        self.defaults = defaults
        self.data = None
        self.initData()

    def initData(self):
        # We check if the proxy str is well formated:
        if (not isinstance(self.proxyStr, str)) or len(self.proxyStr) == 0:
            logError("Wrong proxyStr given.", self)
            return
        # We init the data:
        self.data = dict()
        self.proxyStr = self.proxyStr.strip()
        # We iterate over self.proxyStr:
        theTuple = self.proxyStr.split(":")
        enumIndex = 1
        for current in theTuple:
            if enumIndex > len(PROXY_DESC):
                break
            if current == "":
                current = None
            self.data[PROXY_DESC(enumIndex).name] = current
            enumIndex += 1
        # We terminate the data dict by filling None values:
        for i in range(enumIndex, len(PROXY_DESC) + 1):
            self.data[PROXY_DESC(i).name] = None
        # We check the validity of the proxy:
        if not dictContains(self.data, "ip"):
            raise Exception("Proxy description not valid.")

    def __contains__(self, key):
        return dictContains(self.data, key)

    def __getattr__(self, attr):
        try:
            enumItem = enumCast(attr, PROXY_DESC)
            if enumItem is not None:
                if self.data[enumItem.name] is None and enumItem.name in self.defaults:
                    return self.defaults[enumItem.name]
                else:
                    return self.data[enumItem.name]
            super(Proxy, self).__getattr__(attr, value)
        except KeyError:
            raise AttributeError(attr)

    def __setattr__(self, attr, value):
        if isinstance(value, str):
            enumItem = enumCast(attr, PROXY_DESC)
            if enumItem is not None:
                self.data[enumItem.name] = value
                return
        super(Proxy, self).__setattr__(attr, value)

    def __eq__(self, o):
        for current in PROXY_DESC:
            if self.equalityExclude is None or current.name not in self.equalityExclude:
                if self[current.name] != o[current.name]:
                    return False
        return True

    def __getitem__(self, attr):
        enumItem = enumCast(attr, PROXY_DESC)
        if enumItem is not None:
            if self.data[enumItem.name] is None and enumItem.name in self.defaults:
                return self.defaults[enumItem.name]
            else:
                return self.data[enumItem.name]
        raise AttributeError(attr)


    def __setitem__(self, attr, value):
        if isinstance(value, str):
            enumItem = enumCast(attr, PROXY_DESC)
            if enumItem is not None:
                self.data[enumItem.name] = value
                return
        super(Proxy, self).__setitem__(attr, value)

    def toString(self):
        """
            This method returns the representation of the proxy
        """
        return repr(self)

    def __repr__(self):
        """
            This method returns the string representation of the proxy
            with user and password
        """
        def hasNext(current):
            for watch in PROXY_DESC:
                if watch.value > current.value:
                    if dictContains(self.data, watch.name):
                        return True
            return False
        result = ""
        for current in PROXY_DESC:
            if dictContains(self.data, current.name):
                result += self.data[current.name] + ":"
            elif hasNext(current):
                result += ":"
            else:
                break
        result = result[:-1]
        return result

    def __str__(self):
        """
            This method returns the pretty string representation
            without user, password and type
        """
        return self.ip + ":" + self.port

    def toScheme(self, hideUser=False):
        result = ""
        result += self.type + "://"
        if not hideUser and "user" in self:
            result += self.user + ":" + self.password + "@"
        result += self.ip + ":" + self.port
        return result

def getProxies\
(
    proxiesPatterns,
    removeFailingProxies=True,
    limit=0,
    logger=None,
    verbose=True,
    proxyArgs={},
    proxiesDataDir=None,
    failPatterns=["*failing*"],
    excludePatterns=[], # excludePatterns="*55555*"
):
    # We convert all patterns:
    if proxiesPatterns is None:
        proxiesPatterns = []
    if failPatterns is None:
        failPatterns = []
    if excludePatterns is None:
        excludePatterns = []
    if not isinstance(proxiesPatterns, list):
        proxiesPatterns = [proxiesPatterns]
    if not isinstance(excludePatterns, list):
        excludePatterns = [excludePatterns]
    if not isinstance(failPatterns, list):
        failPatterns = [failPatterns]
    # We find the proxies dir:
    if proxiesDataDir is None:
        proxiesDataDir = dataDir() + "/Misc/crawling/proxies"
    # We find all files to exclude:
    excludesPath = []
    for excludePattern in excludePatterns:
        excludesPath += sortedGlob(proxiesDataDir + "/" + excludePattern)
    # We find all files for proxies:
    proxiesPath = []
    for proxiesPattern in proxiesPatterns:
        proxiesPath += sortedGlob(proxiesDataDir + "/" + proxiesPattern)
    # We find all files for proxies:
    failingsPath = []
    for failPattern in failPatterns:
        failingsPath += sortedGlob(proxiesDataDir + "/" + failPattern)
    # We init all proxies:
    proxies = []
    for filePath in proxiesPath:
        if filePath not in excludesPath and isFile(filePath) and filePath not in failingsPath:
            for line in fileToStrList(filePath):
                try:
                    proxy = Proxy(line, logger=logger, verbose=verbose, **proxyArgs)
                    proxies.append(proxy)
                except Exception as e:
                    logException(e, location="getProxies", logger=logger, verbose=verbose)
    # We delete all failing proxies:
    if removeFailingProxies:
        newProxies = []
        failingProxies = getProxies(failPatterns, logger=logger,
                                    removeFailingProxies=False, proxyArgs=proxyArgs,
                                    failPatterns=None, verbose=False)
        for current in proxies:
            if current not in failingProxies:
                newProxies.append(current)
        proxies = newProxies
    # We set the limit:
    if limit > 0:
        i = 0
        newProxies = []
        for current in proxies:
            newProxies.append(current)
            if i >= limit:
                break
            i += 1
        proxies = newProxies
    # We return all:
    if proxies is None or len(proxies) == 0:
        logError("No proxies found...", logger=logger, verbose=verbose)
    return proxies


def proxyToStr(obj):
    if isinstance(obj, str):
        return obj
    else:
        return repr(obj)


def getProxiesProd(*args, **kwargs):
    return getAllProxies(*args, **kwargs)
def getProxiesTest(*args, **kwargs):
    return getProxiesProd(*args, **kwargs)[:20]
# def getProxiesRenew():
#     return getProxies("*", *args, excludePatterns=["*55555*", "*linkedin*"], **kwargs)
# def getProxiesLinkedin():
#     return getProxies("*linkedin*", *args, excludePatterns="*55555*", **kwargs)
def getRandomProxy(*args, **kwargs):
    return random.choice(getAllProxies(*args, **kwargs))
def getAllProxies(*args, **kwargs):
    return getProxies("*", *args, excludePatterns="*55555*", **kwargs)


if __name__ == '__main__':
#     testIsHtmlOK()
#     proxies = getProxies(dataDir() + proxiesDataSubDir + "/proxies-renew.txt")
#     proxies = getProxiesRenew()
#     print(len(proxies))


    for current in getAllProxies():
        print(repr(current))
    print(len(getAllProxies()))


