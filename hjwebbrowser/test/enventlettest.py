

import requests
import eventlet
eventlet.monkey_patch(socket=True)
from systemtools.duration import *
from systemtools.logger import *
from hjwebbrowser.proxy import *
from hjwebbrowser.httpbrowser import *
# from hjwebbrowser.tor import *
from threading import Thread
from datatools.url import *



urls = URLParser().strToUrls(fileToStr(getExecDir() + "/urls.txt"))


# def patchSocket():
# 	if not eventlet.patcher.is_monkey_patched("socket"):
# 		eventlet.monkey_patch(socket=True)


def request(url, p, timeout=2):
	try:
		r = None
		proxies = {'http': p.toScheme(), 'https': p.toScheme()}
		with eventlet.Timeout(timeout, Exception("Eventlet timeout")):
			r = requests.get(url, proxies=proxies, verify=False, timeout=timeout)
		if r is not None:
			print(url + " --> " + str(r.content[:15]))
	except Exception as e:
		print(url + " --> " + str(e))

def request2(url, p, timeout=10):
	p["ip"] = "120.120.120.1"
	result = HTTPBrowser(proxy=p, useTimeoutGet=True, pageLoadTimeout=timeout, maxRetryWithTor=0,).html(url)
	print(url + " --> " + str(result["html"])[:30])




urls = urls[:10]
urls += ["http://ipv4.download.thinkbroadband.com/1GB.zip"]
# urls = ["http://ipv4.download.thinkbroadband.com/1GB.zip"]
# urls = ["https://api.ipify.org?format=json"]

tt = TicToc()
tt.tic()

threads = []
i = 0
allProxies = getAllProxies()

for url in urls:
	thread = Thread(target=request2, args=(url, allProxies[i],))
	threads.append(thread)
	i += 1




for current in threads:
	current.start()
for current in threads:
	current.join()




tt.toc()
