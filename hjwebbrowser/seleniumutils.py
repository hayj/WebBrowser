
from systemtools.logger import *
from systemtools.basics import *
from hjwebbrowser.browser import *
from scroller.scroller import *


def elementExists(browser, cssSelector, logger=None, verbose=True):
    driver = browser.driver
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