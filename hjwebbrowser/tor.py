import requests
from datatools.url import *
from datatools.bashscripts import BashScripts
from urllib.request import urlopen
from systemtools.basics import *
from systemtools.location import *
from systemtools.logger import *
import requests.auth
from datastructuretools.hashmap import *
import socks
import socket
import sh

def torSingletonExists():
    global torSingleton
    return torSingleton is not None

torSingleton = None
def getTorSingleton(*args, **kwargs):
    global torSingleton
    if torSingleton is None:
        torSingleton = Tor(*args, **kwargs)
    return torSingleton

class Tor:
    """
        This class init n tor services. You can define n using portCount parameter.
        It will only use available ports on your machine.
        You need to install tor:
            sudo apt-get install tor
        Then you can call methods to get local proxies.
        A proxie is a dict with "ip", "port", "type"
        Or you can call restart which will refresh ips.
    """
    def __init__(self, ports=None, portCount=100, startPort=1000,
                 logger=None, verbose=True, resetSleepTime=0.3,
                 initSleepTime=0.5, initSleepTimeFactor=0.3, autoPorts=True):
        self.initSleepTimeFactor = initSleepTimeFactor
        self.resetSleepTime = resetSleepTime
        self.initSleepTime = initSleepTime
        self.autoPorts = autoPorts
        self.logger = logger
        self.verbose = verbose
        self.bashScripts = BashScripts(logger=self.logger, verbose=self.verbose)
        self.killbillScript = self.bashScripts.get("killbill")
        self.nnScript = self.bashScripts.get("nn")
        self.ports = ports
        if self.ports is not None:
            self.autoPorts = False
        self.portCount = portCount
        self.startPort = startPort
        self.initPorts()
        self.confDir = tmpDir(subDir="tor/conf")
        self.scriptsDir = tmpDir("tor")
        if self.initSleepTime is None:
            self.initSleepTime = self.initSleepTimeFactor * len(self.ports)
        self.restart()

    def initPorts(self, erase=False):
        if erase or self.ports is None or len(self.ports) == 0:
            self.ports = []
            usedPorts = getUsedPorts()
            for i in range(0, self.portCount * 10, 2):
                if len(self.ports) >= self.portCount:
                    break
                currentPort = self.startPort + i
                controlPort = self.startPort + i + 1
                if currentPort not in usedPorts and controlPort not in usedPorts:
                    self.ports.append(currentPort)

    def execBashFile(self, path):
        try:
            sh.bash(path)
        except Exception as e:
            logException(e, self, location="execBashFile")

    def restart(self):
        """
            This method will refresh all ips, si can have new ips through tor.
        """
        self.stop()
        self.start()

    def stop(self):
        log("Reseting tor services...", self)
        killbillText = ""
        for port in self.ports:
            killbillText += "killbill torrc." + str(port) + '\n'
        script = \
        """
            cd """ + self.scriptsDir + """
            """ + self.killbillScript + """
            """ + killbillText + """
            rm -rf """ + self.confDir + """/*
        """
        script = stripAllLines(script)
        scriptPath = self.scriptsDir + "/stop.sh"
        strToFile(script, scriptPath)
        self.execBashFile(scriptPath)
        time.sleep(self.resetSleepTime)
        log("Tor services reseted.", self)

    def start(self, sleepTime=None, removeScripts=False):
        log("Initializing tor services...", self)
        if self.autoPorts:
            self.initPorts(erase=True)
        # We define a funct to init tor services on a specifi port:
        def initPort(port):
            controlPort = str(port + 1)
            port = str(port)
            logDir = self.confDir + "/logs-" + port
            mkdir(logDir)
            confFilePath = self.confDir + "/torrc." + port
            confFileText = \
            """
                SocksPort """ + port + """
                ControlPort """ + controlPort + """
                DataDirectory """ + logDir + """
            """
            confFileText = stripAllLines(confFileText)
            strToFile(confFileText, confFilePath)
            script = \
            """
                cd """ + self.confDir + """
                """ + self.nnScript + """
                nn -n 0 -o """ + logDir + """/nohup.out tor -f """ + confFilePath + """
            """
            script = stripAllLines(script)
            scriptPath = self.scriptsDir + "/start-" + port + ".sh"
            strToFile(script, scriptPath)
            self.execBashFile(scriptPath)
        # We init all in parallel:
        threads = []
        for port in self.ports:
            theThread = Thread(target=initPort, args=(port,))
            threads.append(theThread)
        for theThread in threads:
            theThread.start()
        for theThread in threads:
            theThread.join()
        # And we sleep:
        time.sleep(self.initSleepTime)
        if removeScripts:
            removeFiles(sortedGlob(self.scriptsDir + "/*.sh"))
        log("Tor services initialized.", self)

    def getProxies(self):
        """
            This method return all proxies of all class tor services
        """
        proxies = []
        for port in self.ports:
            proxy = {"ip": "127.0.0.1", "port": str(port), "user": None,
                     "password": None, "type": "socks5"}
            proxies.append(proxy)
        return proxies

    def getRandomProxy(self):
        """
            This method return a random proxies over all class tor services
        """
        return random.choice(self.getProxies())


if __name__ == '__main__':
    Tor(portCount=100).stop()

