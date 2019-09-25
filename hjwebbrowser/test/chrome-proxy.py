# pew in st-venv python ~/Workspace/Python/Crawling/WebBrowser/hjwebbrowser/test/chrome-proxy.py

from selenium import webdriver
from systemtools.location import *

proxy = "165.231.92.40:80" #test with any ip address which supports `http` as well because the link within the script are of `http`


chromeDriverPath = homeDir() + "/lib/browserdrivers/chromedriver"


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--proxy-server={}'.format(proxy))
# chrome_options.binary_location = "/usr/bin/google-chrome"
driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chromeDriverPath)

driver.get('https://api.ipify.org?format=json')
print(driver.page_source)
driver.quit()


# Chrome binary : https://stackoverflow.com/questions/46026987/selenium-gives-selenium-common-exceptions-webdriverexception-message-unknown

# installer chrome : https://askubuntu.com/questions/60133/where-can-i-find-chromium-binary-tarballs/64396 https://github.com/scheib/chromium-latest-linux


# installer chrome driver : https://chromedriver.chromium.org/downloads



# lien de dl (remplaceer revidion var) : https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F$REVISION%2Fchrome-linux.zip?alt=media
# https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F697136%2Fchrome-linux.zip?alt=media
# https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F389148%2Fchrome-linux.zip?alt=media