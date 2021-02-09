
import sys
import os
base_path = os.path.split(os.path.realpath(__file__))[0]
lib_path = os.path.join(base_path, 'lib')
sys.path.append(lib_path)
sys.path.append(base_path)
import Util
from socket import *
import subprocess
import json
import time

# 日志对象
logger = Util.getLogger('login')
# 操作超时时间
wait_timeout = int(Util.getConfig('wait_timeout'))
# 自动登录watcher端口
watcher_port = int(Util.getConfig('watcher_port'))
# 堡垒机登录名
login_name = Util.getConfig('login_name')
# 登录的ip
target_ip = crt.Arguments.GetArg(0)
# target_ip = '172.16.73.58'

logger.info('login script start, target :' + target_ip)

tab = crt.GetScriptTab()
tab.Screen.Synchronous = True

try:
	connected = False
	retry = 0
	while connected != True and retry < 3:
		try:
			serAddr = ('localhost', watcher_port)
			logger.info('prot ' + str(watcher_port))
			tcpClientSocket = socket(AF_INET, SOCK_STREAM)
			tcpClientSocket.connect(serAddr)
			connected = True
		except Exception as e:
			logger.exception('not connectd')
			logger.warn('auto connect environment is disabled , init environment ...' + str(watcher_port))
			print('auto connect environment is disabled , init environment ...')
			# 启动watcher
			watcher_path = os.path.join(base_path, 'sockerServer.py')
			sp = subprocess.Popen(['python', watcher_path])
			time.sleep(2)
			retry = retry + 1

	sendData = ('{"command":"getLoginToken","target_ip":"' + target_ip + '"}')
	tcpClientSocket.send(sendData)
	recvData = tcpClientSocket.recv(1024)
	recvData = recvData.encode()
	logger.info ('get message:' + recvData)
	recvData = json.loads(recvData)
	if recvData['rspCode'] == 'success':
		recvData = recvData['rspMsg']
		recvData = recvData.replace('\'','"')
		logger.info('get token succeed for ' + target_ip +', token: ' + recvData)
	tcpClientSocket.close()

	token = json.loads(recvData)
	token = token["pw"]
	target_user = 'user'
	target_pwd = 'user'
	if target_ip.startswith('192.168.'):
	    target_user = 'user'
	    target_pwd = 'user'
	elif target_ip.startswith('172.16.72'):
	    target_user = 'user'
	    target_pwd = 'user'
	elif target_ip.startswith('172.16.73'):
	    target_user = 'user'
	    target_pwd = 'user'
	elif target_ip.startswith('172.16.74'):
	    target_user = 'user'
	    target_pwd = 'user'
	elif target_ip.startswith('172.18.72'):
	    target_user = 'user'
	    target_pwd = 'user'
	elif target_ip.startswith('172.18.73'):
	    target_user = 'user'
	    target_pwd = 'user'
	elif target_ip.startswith('172.18.74'):
	    target_user = 'user'
	    target_pwd = 'user'
	elif target_ip.startswith('172.18.172'):
	    target_user = 'deployer'
	    target_pwd = 'user'

	tab.Screen.WaitForString("Username:", wait_timeout)
	tab.Screen.Send(login_name + "\r")
	tab.Screen.WaitForString("Password:", wait_timeout)
	tab.Screen.Send(token + "\r")
	tab.Screen.WaitForString("Input account:", wait_timeout)
	tab.Screen.Send(target_user + "\r")
	tab.Screen.WaitForString("'s password", wait_timeout)
	tab.Screen.Send(target_pwd + "\r")
	tab.Screen.Clear()
except Exception as e:
	logger.exception('auto login error :')
	tab.Screen.Send('auto login error, please check the log file')
	crt.Session.Disconnect()


