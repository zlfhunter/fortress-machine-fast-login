#coding=utf-8
import os
import sys
base_path = os.path.split(os.path.realpath(__file__))[0]
lib_path = os.path.join(base_path, 'lib')
sys.path.append(lib_path)
sys.path.append(base_path)
from socket import *
import threading
import time
import Util
import sys
import json
import urllib3
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

baseDir = os.path.split(os.path.realpath(__file__))[0]
driver_path = os.path.join(baseDir, 'driver')

class nonono:
    def quit(slef):
        print(1)

logger = Util.getLogger('watcher.py')

# watcher状态 init：初始化中/error：初始化异常/success：可用
watcherStatus = 'init'
# 浏览器对象
browser = nonono()
# ip参数映射
ip_list = None
# socket对象
serverSocket = None
wait_timeout = int(Util.getConfig('wait_timeout'))

def main():
    global logger
    logger.info(str(os.getpid())+'starting watcher service')
    global ip_list
    global watcherStatus
    ip_list = Util.getIpList()

    # 初始化socket服务,不进行异常处理，失败直接结束程序
    initSocket()
    
    # 异步初始化watcher,如果异常则将watcherStatus变为error
    threading.Thread(target=initWatcher, name="initWatcher", args=()).start()

    logger.info(str(os.getpid())+'start service')
    
    # 异步初始化watcher,如果异常则将watcherStatus变为error
    threading.Thread(target=onService, name="onService", args=()).start()

    threading.Thread(target=checkNetState, name="checkNetState", args=()).start()

    while watcherStatus != 'error':
        time.sleep(1)
        
'''
    检查vpn网络状态
'''
def checkNetState():
    global browser
    global logger
    global wait_timeout
    baoleiji_ip = Util.getConfig('baoleiji_ip')

    time.sleep(10)
    try:
        while True:
            logger.info('ping start ')
            req = requests.get(baoleiji_ip,verify=False,timeout=wait_timeout)
            if req.status_code == 200:
                logger.info('get ping')
                time.sleep(10)
            else:
                logger.info('enable to request ' + baoleiji_ip + ', watcher exit now !')
                browser.quit()
                os._exit(0)
    except Exception as e:
        logger.info('enable to request ' + baoleiji_ip + ', watcher exit now !')
        browser.quit()
        os._exit(0)

'''
    监听socket请求
'''
def onService():
    try:
        while True:
            # print('-----主进程，，等待新客户端的到来------')
            newSocket,destAddr = serverSocket.accept()

            # print('-----主进程，，接下来创建一个新的进程负责数据处理[%s]-----'%str(destAddr))
            client = threading.Thread(target=clientHandler, args=(newSocket,destAddr))
            client.start()
    finally:
        if serverSocket != None:
            serverSocket.close()

'''
    初始化watcher,如果异常则将watcherStatus变为error
'''
def initWatcher():
    global watcherStatus
    global browser
    global logger
    global wait_timeout
    try:
        logger.info(str(os.getpid())+'start init watcher')

        # 变量设置
        login_name = Util.getConfig('login_name')
        login_pwd = Util.getConfig('login_pwd')
        baoleiji_ip = Util.getConfig('baoleiji_ip')

        # rootDir = os.path.split(os.path.realpath(__file__))[0]
        logFile = os.path.join(baseDir, 'autoLogin.log')
        # 初始化浏览器
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36")
        browser = webdriver.PhantomJS(executable_path=os.path.join(driver_path, 'phantomjs'), desired_capabilities=dcap, service_args=['--ignore-ssl-errors=true'], service_log_path=logFile)

        # 设置浏览器参数
        browser.set_window_size(1120, 550)
        browser.implicitly_wait(wait_timeout)

        # 打开堡垒机页面
        browser.get(baoleiji_ip)

        # 用户名
        user = browser.find_element_by_id("userName")
        user.send_keys(login_name)
        logger.info('send login name')
        # 密码
        password = browser.find_element_by_id("password")
        password.send_keys(login_pwd)
        password.send_keys(Keys.RETURN)
        logger.info('send login pwd')
        # 一次性口令
        OptPassword = browser.find_element_by_name("dyncode")
        myoptKey = Util.getOtpPwd()
        OptPassword.send_keys(myoptKey)
        OptPassword.send_keys(Keys.RETURN)
        logger.info('send otp pwd')

        watcherStatus = 'success'
    except Exception as e:
        watcherStatus = 'error'
        logger.exception(str(os.getpid())+'start init watcher error!')
        # exit()

'''
    初始化socket服务
'''
def initSocket():
    global logger

    global serverSocket

    watcher_port = int(Util.getConfig('watcher_port'))
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR  , 1)
    localAddr = ('localhost', watcher_port)
    serverSocket.bind(localAddr)
    serverSocket.listen(5)

    logger.info(str(os.getpid())+'socket server init succeed on port: ' + str(watcher_port))

'''
    socket请求处理
'''
def clientHandler(newSocket,destAddr):
    global watcherStatus
    global logger
    global wait_timeout
    while True:
        recvData = newSocket.recv(1024)
        if len(recvData)>0:
            print('recv[%s]:%s'%(str(destAddr), recvData))
            logger.info(str(os.getpid())+'recv request: ' + recvData)

            recvData = json.loads(recvData)
            if recvData['command'] == 'getLoginToken':
                # 等待watcher初始化完成
                while watcherStatus != 'success':
                    if watcherStatus == 'error':
                        newSocket.close()
                        return
                    time.sleep(1)

                target_ip = recvData['target_ip']
                server = ip_list.get(section=target_ip, option='server')
                service = ip_list.get(section=target_ip, option='service')
                account = ip_list.get(section=target_ip, option='account')
                this_id = str(Util.getUUID())
                js = ''
                if target_ip.startswith('1'):
                    js = '$.post("https://172.16.211.11/client/tui_client.php",  \
                        {\
                            server:' + server + ', \
                            account:' + account + ', \
                            service:' + service + ', \
                            worksheet:0, \
                            sess_remark:"",\
                            dual_auth:0,\
                            dual_auth_login:"",\
                            dual_auth_password:"",\
                            resolution:"80x24",\
                            bg_color:"white",\
                            proto:"ssh",\
                            authorize:0,\
                            authorize_login:"",\
                            authorize_password:""\
                        },  \
                        function(data){\
                            $("body").append("<zlf id=\\"'+this_id+'\\" rsp="+data.replace(new RegExp("\\"","gm"),"\'").replace(new RegExp(" ","gm"),"kongge")+"></zlf>")\
                        }\
                    );'
                else:
                    js = '$.post("https://172.16.211.11/client/gui_client.php",  \
                        {\
                            server:' + server + ', \
                            account:' + account + ', \
                            service:' + service + ', \
                            worksheet:0, \
                            sess_remark:"",\
                            dual_auth:0,\
                            dual_auth_login:"",\
                            dual_auth_password:"",\
                            resolution:"80x24",\
                            rdp_console:0,\
                            mstsc:1,\
                            maximize:1,\
                            disk:"c,d",\
                            authorize:0,\
                            authorize_login:"",\
                            authorize_password:"",\
                            mode:"mac"\
                        },  \
                        function(data){\
                            $("body").append("<zlf id=\\"'+this_id+'\\" rsp="+data.replace(new RegExp("\\"","gm"),"\'").replace(new RegExp(" ","gm"),"kongge")+"></zlf>")\
                        }\
                    );'
                
                try:
                    browser.execute_script(js)
                    rsp = WebDriverWait(browser,wait_timeout,0.5).until(EC.presence_of_element_located((By.ID,this_id)))
                    rsp = rsp.get_attribute('rsp')
                    # rsp = rsp.replace('\'','"').replace('kongge',' ')
                    rsp = rsp.replace('kongge',' ')
                    # rsp = json.loads(rsp)
                    newSocket.send('{"rspCode":"success","rspMsg":"' + rsp + '"}')
                    # newSocket.send('{"rspCode":"success","rspMsg":"' + rsp['pw'] + '"}')
                    logger.info(str(os.getpid())+'get token for request:' + str(recvData) + ',token: ' + rsp)
                except Exception as e:
                    watcherStatus = 'error'
                    logger.exception(str(os.getpid())+'get login token error .')
                    break
        else:
            print('[%s]客户端已经关闭'%str(destAddr))
            break
    newSocket.close()

if __name__ == '__main__':
    try:
        main()
        logger.info('exit')
    except:
        logger.exception(str(os.getpid())+'watcher exception: ')
    finally:
        if browser != None:
            browser.quit()

        os._exit(0)
        
    