# WebBrowser

This tool is a wrapper over `selenium` and `requests`. It allow an easy use of phantomjs and Chrome (headless or not) through Selenium. It handle selenium instability by killing dead process. You can set proxy and it will automatically applied it (through plugin with Chrome to handle user/password...). It use [DomainDuplicate](https://github.com/hayj/DomainDuplicate) lib to control web pages content. Each requests return normalized content over all drivers. It will randomly select a header (and seed it by proxy ip).

## Installation

	git clone git@github.com:hayj/WebBrowser.git
	pip install ./WebBrowser/wm-dist/*.tar.gz


## Browser

This class is a wrapper over phantmjs and Chrome (Selenium).

Features:

 * Randomly select a header (and seed it with the proxy if exists)
 * Handle proxies for Chrome, Chrome headless, phantomjs
 * Automaticaly re-init dead drivers
 * Fix problem of page_source which doesn't change automatically over several gets
 * Use [DomainDuplicate](https://github.com/hayj/DomainDuplicate) to prevent captcha pages or "refuse" page.
 * It retains proxy performance in b.durationHistory
 * Prevent infinite get using selenium
 * Considers an ajax sleep as not being a bottleneck, but the get itself
 * It can detect 404 errors with Selenium (which doesn't provide this information). [Coming soon].

You can set the driver and headless or not (don't forgot to install driver and set the PATH env):

	from webbrowser.browser import *
	b = Browser(driverType=DRIVER_TYPE.chrome) # or DRIVER_TYPE.phantomjs

You can then call `html` method to get data:

	data = b.html("http://...")

data is a dict:

	data = \
	{
	    "proxy": "xxx",
	    "url": "http...",
	    "domain": <The domain name using public suffix list>,
	    "browser": <the browser name (http, phantomjs, chrome)>,
	    "lastUrl": "http...", # The last url after redirections
	    "lastUrlDomain": <The domain name of the last url>,
	    "html": "<html>...",
	    "title": "The title",
	    "status": <a status from webbrowser.browser.REQUEST_STATUS>,
	}

You can see all status in `webbrowser.browser.REQUEST_STATUS`.

You can set a proxy:

	b = Browser(proxy={"ip": "xxx.xxx.xxx.xxx", "port": "22", "user": None, "password": None})

You can use Chrome as headless:

	b = Browser(headless=True, driverType=DRIVER_TYPE.chrome)

You can set a callback if you work with threads:

	b = Browser(htmlCallback=myHtmlCallbackFunct)

In this case you have to call the `get` method (see the class doc for more informations):

	isOk = b.get("http://...")

You can set a ajax sleep to wait a little bit when the page is loaded, and set a page load timeout and choose to load image or not:

	b = Browser(ajaxSleep=3.0, pageLoadTimeout=60, loadImages=False)

Set the maxDuplicatePerDomain from DomainDuplicate:

	b = Browser(maxDuplicatePerDomain=5)

Performance notes:

 * Chrome is slower than phantomjs when using a lot in parallel
 * Phantomjs is more often detected by servers, and now is deprecated in Selenium

## HTTPBrowser

This tool is not a wrapper over a real browser (Selenium) but over request. It works the same way but also return a `httpStatus`.

You can give retry counts : `maxRetryWithoutProxy`, `maxRetryIfTimeout`, `maxRetryIf407`.
You can set different port for you proxy through portSet.

Contrary to `Browser`, the `get` method return data. `html` is an alias. But you can give a `htmlCallback` too.

## Proxies

The proxy object must be a dict `{"ip": "xxx.xxx.xxx.xxx", "port": "22", "user": None, "password": None}`

## Error 404 detection for `Browser`

This feature is currently not functional. It will be updated soon. So consider error404 as a success status for now.

## Phantomjs deprecation

If phantomjs doesn't works, you can go back to `selenium==3.8.0` and `phantomjs==2.1.1`

