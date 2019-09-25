# pew in st-venv python ~/Workspace/Python/Crawling/WebBrowser/hjwebbrowser/test/firefox-proxy2.py


from selenium import webdriver
from systemtools.location import *
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

proxyString = "165.231.92.40:80"

binary = FirefoxBinary(homeDir() + '/lib/firefox/firefox')




desired_capability = webdriver.DesiredCapabilities.FIREFOX
desired_capability['proxy'] = {
    "proxyType": "manual",
    "httpProxy": proxyString,
    "ftpProxy": proxyString,
    "sslProxy": proxyString
}

base_url = "https://api.ipify.org?format=json"


options = Options()
options.headless = True

firefox_profile = webdriver.FirefoxProfile()
firefox_profile.set_preference("browser.privatebrowsing.autostart", True)
driver = webdriver.Firefox\
(
    options=options,
    executable_path=homeDir() + "/lib/browserdrivers/geckodriver",
    firefox_profile=firefox_profile,
    capabilities=desired_capability,
    firefox_binary=binary,
    ) 
print("aaaaaaa")
print(driver.get(base_url))
print(driver.page_source)
print("bbbbb")