
from systemtools.logger import *
from systemtools.basics import *
from hjwebbrowser.browser import *
from scroller.scroller import *
from nlptools.preprocessing import preprocess


def tryClick(driver, css, randomSleepAmount=None, logger=None, verbose=True):
    found = waitForElement(driver, css)
    if found:
        if randomSleepAmount is not None:
            randomSleep(randomSleepAmount)
        try:
            el = driver.find_element_by_css_selector(css)
            el.click()
            return True
        except Exception as e:
            logException(e, logger, verbose=verbose)
            return False
    else:
        return False

def elementExists(browser, cssSelector, logger=None, verbose=True):
    driver = browser
    try:
        driver = driver.driver
    except: pass
    el = None
    try:
        el = driver.find_element_by_css_selector(cssSelector)
    except:
        return False
    if el is not None and el.is_displayed():
        return True
    else:
        return False

def waitForElement(browser, cssSelector,
                   iterationCount=20, randomSleepAmount=0.5,
                   logger=None, verbose=True,
                   raiseException=False):
    for i in range(iterationCount):
        if elementExists(browser, cssSelector,
                         logger=logger, verbose=verbose):
            return True
        randomSleep(randomSleepAmount)
    if raiseException:
        raise Exception\
        (
            "The element " + cssSelector +
            " doesn't appear after " +
            secondsToHumanReadableDuration(randomSleepAmount * iterationCount)
        )
    return False


def waitAndScroll(browser, cssSelector,
                   waitForElementParams={},
                   logger=None, verbose=True):
    if waitForElement(browser, cssSelector, **waitForElementParams):
        el = browser.driver.find_element_by_css_selector(cssSelector)
        scrollTo(browser.driver, el)
        return True
    return False

def waitScrollAndClick(browser, cssSelector, *args, randomSleepAmount=0.2, **kwargs):
    if waitAndScroll(browser, cssSelector, *args, **kwargs):
        randomSleep(randomSleepAmount)
        el = browser.driver.find_element_by_css_selector(cssSelector)
        el.click()
        return True
    return False

def getElementByText(driver, text, doPreprocessing=True, tag="*", strongMatch=False,
                    logger=None, verbose=True):
    try:
        psElements = driver.find_elements_by_xpath("//" + tag + "[contains(text(), '" + text + "')]")
        def prepr(text):
            return preprocess(text, removeHtml=True, doReduceBlank=True, keepNewLines=False,
                              stripAccents=True, doRemoveUrls=True, doLower=True,
                              unescapeHtml=True, doBadlyEncoded=True)
        pText = text
        if doPreprocessing:
            pText = prepr(text)
        for current in psElements:
            currentText = current.text
            if currentText is not None and len(currentText) > 0:
                if doPreprocessing:
                    currentText = prepr(currentText)
                if pText == currentText:
                    return current
        if not strongMatch:
            for current in psElements:
                currentText = current.text
                if currentText is not None and len(currentText) > 0:
                    if doPreprocessing:
                        currentText = prepr(currentText)
                    if pText in currentText:
                        return current
    except Exception as e:
        logException(e, logger=logger, verbose=verbose)
    return None