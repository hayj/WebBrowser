################### Tor test ################
# Warning: actually HTTPBrowser try to use Tor but on server which doesn't have tor installed, it will use the public ip of the server, the test proof:
# from domainduplicate import config as ddConf
# ddConf.useMongodb = False
# from systemtools.basics import *
# from hjwebbrowser.httpbrowser import *
# # from hjwebbrowser.tor import *
# # tor = Tor(portCount=3)
# # tor.stop()
# # p = tor.getRandomProxy()
# b = HTTPBrowser(proxy=getRandomProxy(), maxRetryWithTor=1)
# printLTS(b.html("https://api.ipify.org?format=json"))
# tor.stop()
##############################################





# from domainduplicate import config as ddConf
# ddConf.useMongodb = False
# from systemtools.basics import *
# from hjwebbrowser.httpbrowser import *
# from hjwebbrowser.tor import *
# tor = Tor(portCount=3, startPort=1100)
# p = tor.getRandomProxy()
# print(p.toScheme())
# b = HTTPBrowser(proxy=p)
# printLTS(b.html("https://api.ipify.org?format=json"))





# import requests
# import eventlet
# from systemtools.duration import *
# from systemtools.logger import *
# from hjwebbrowser.proxy import *
# # from hjwebbrowser.tor import *
# # print(getUsedPorts())
# # tor = Tor(portCount=3)
# # url = "https://api.ipify.org?format=json"
# # url = "http://go.wisc.edu/2xa717"
# # url = "https://go.wisc.edu/h825k9"
# url = "http://ipv4.download.thinkbroadband.com/1GB.zip"
# # url = "https://cimss.ssec.wisc.edu/goes/blog/wp-content/uploads/2018/01/180117_terra_modis_truecolor_falsecolor_Deep_South_snow_anim.gif"
# # url = "https://cimss.ssec.wisc.edu/goes/blog/wp-content/uploads/2018/02/180213_himawari8_himawari9_infrared_Gita_anim.mp4"
# p = getRandomProxy()
# # p = tor.getRandomProxy()
# proxies = {'http': p.toScheme(), 'https': p.toScheme()}
# tt = TicToc()
# tt.tic("Requesting...")



# def patchSocket():
# 	if not eventlet.patcher.is_monkey_patched("socket"):
# 		eventlet.monkey_patch(socket=True)

# try:
# 	# patchSocket()
# 	with eventlet.Timeout(2, Exception("Eventlet timeout")):
# 		r = requests.get(url, proxies=proxies, verify=False, timeout=2)
# except Exception as e:
# 	# logException(e)
# 	pass

# print("aaaaaaaaaaaaaaaaaaaaaaaa")


# try:
# 	print(r.content[:30])
# except Exception as e:
# 	print(str(e))
# tt.toc()


import requests
import eventlet
from systemtools.duration import *
from systemtools.logger import *
from hjwebbrowser.proxy import *
# from hjwebbrowser.tor import *
from threading import Thread
from datatools.url import *



urls = URLParser().strToUrls(fileToStr(getExecDir() + "/urls.txt"))


def patchSocket():
	if not eventlet.patcher.is_monkey_patched("socket"):
		eventlet.monkey_patch(socket=True)


def request(url, p, timeout=10):
	patchSocket()
	try:
		r = None
		proxies = {'http': p.toScheme(), 'https': p.toScheme()}
		with eventlet.Timeout(timeout, Exception("Eventlet timeout")):
			r = requests.get(url, proxies=proxies, verify=False, timeout=timeout)
		if r is not None:
			print(url + " --> " + str(r.content[:15]))
	except Exception as e:
		print(url + " --> " + str(e))




urls = urls[:10]
urls += ["http://ipv4.download.thinkbroadband.com/1GB.zip"]

tt = TicToc()
tt.tic()

threads = []
i = 0
allProxies = getAllProxies()

for url in urls:
	thread = Thread(target=request, args=(url, allProxies[i],))
	threads.append(thread)
	i += 1




for current in threads:
	current.start()
for current in threads:
	current.join()




tt.toc()






