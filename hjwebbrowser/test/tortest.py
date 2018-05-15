
from hjwebbrowser.browser import *
from hjwebbrowser.tor import *
from hjwebbrowser.utils import *


def testSelenium():
    tor = Tor(portCount=1)
    proxies = tor.getProxies()

#     print("WITH A TOR PROXY")
#     b = Browser(proxy=tor.getProxies()[0], driverType=DRIVER_TYPE.phantomjs, **driversPath)
#     printLTS(b.html("https://api.ipify.org/?format=json"))
# 
#     print("NO PROXY")
#     b = Browser(driverType=DRIVER_TYPE.phantomjs, **driversPath)
#     printLTS(b.html("https://api.ipify.org/?format=json"))

    print("NO A OCTOPEEK PROXY")
    b = Browser(proxy=getProxiesLinkedin()[10], driverType=DRIVER_TYPE.phantomjs, **driversPath)
    printLTS(b.html("https://api.ipify.org/?format=json"))



if __name__ == '__main__':
    driversPath = dict()
    driversPath["chromeDriverPath"] = "/home/hayj/Programs/browserdrivers/chromedriver"
    driversPath["phantomjsPath"] = "/home/hayj/Programs/headlessbrowsers/phantomjs-2.1.1-linux-x86_64/bin/phantomjs"
    testSelenium()
