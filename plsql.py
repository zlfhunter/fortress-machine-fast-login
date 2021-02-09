import os
import sys
base_path = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(base_path)
# lib_path = os.path.join(base_path, 'lib')
# sys.path.append(lib_path)
import template_file
import tempfile
import Util
import subprocess
import time
from socket import *
import json

# 日志对象
logger = Util.getLogger('login')
# 操作超时时间
# wait_timeout = int(Util.getConfig('wait_timeout'))
# 自动登录watcher端口
watcher_port = int(Util.getConfig('watcher_port'))
# 堡垒机登录名
# login_name = Util.getConfig('login_name')
# 登录的ip
target_ip = crt.Arguments.GetArg(0)

logger.info('login plsql script start, target ip: ' + target_ip)

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
			# 启动watcher
			watcher_path = os.path.join(base_path, 'sockerServer.py')
			sp = subprocess.Popen(['python', watcher_path])
			time.sleep(2)
			retry = retry + 1

	sendData = ('{"command":"getLoginToken","target_ip":"' + target_ip + '"}')

	tcpClientSocket.send(sendData)
	recvData = tcpClientSocket.recv(1024)
	logger.info ('get message:' + recvData)

	recvData = json.loads(recvData.encode())
	if recvData['rspCode'] == 'success':
		recvData = recvData['rspMsg']
		recvData = recvData.replace('\'','"')
		logger.info('get token succeed for ' + target_ip +', token: ' + recvData)
	tcpClientSocket.close()

	token = json.loads(recvData)

	# screen_mode_id = 'i:1'
	# bpp = 'i:16'
	# enable_cred_ssp_support = 'i:0'
	# maximize = 1
	# width = 'i:1680'
	# height = 'i:978'
	drive_redirection_mode = 0
	redirect_folder = '/Users'

	context = {
	    "DesktopSize": template_file.fullscreen_desktopsize,
	    "DriveRedirectionMode": drive_redirection_mode,
	    "RedirectFolder": redirect_folder,
	    "ApplicationPath": token['alternate shell'].replace('s:',''),
	    "ConnectionString": token['full address'].replace('s:',''),
	    "AudioRedirectionMode": token['audiomode']
	}

	template_str = template_file.rdc_cfg_tmpl.format(**context)

	suffix = ".rdp"
	cfg_file_path = os.path.join(base_path, 'rdp')
	cfg_file = os.path.join(cfg_file_path, str(Util.getUUID()) + '.rdp')

	with open(cfg_file, 'w+') as f:
		f.write(template_str)

	cmdline_args = [Util.getConfig('rdc_path')]
	cmdline_args.append(cfg_file)
	cmdline = [unicode(x).encode(sys.getfilesystemencoding())for x in cmdline_args]

	subprocess.Popen(cmdline)

except Exception as e:
	logger.exception('login plsql error :')
	tab.Screen.Send('login plsql error, please check the log file')
finally:
	crt.Session.Disconnect()




