
from hjwebbrowser.browser import *
from hjwebbrowser.tor import *
from hjwebbrowser.utils import *



if __name__ == '__main__':
    driversPath = dict()
    driversPath["chromeDriverPath"] = "/home/hayj/Programs/browserdrivers/chromedriver"
    proxies = getProxies("*")
    printLTS(proxies)

    for i in range(2*6):
        b = Browser(proxy=proxies[i], driverType=DRIVER_TYPE.chrome, **driversPath)
        printLTS(b.html("https://api.ipify.org/?format=json"))
    while True: time.sleep(100)
