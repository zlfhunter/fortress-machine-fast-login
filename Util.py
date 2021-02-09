#coding:utf-8
import os
import sys
base_path = os.path.split(os.path.realpath(__file__))[0]
lib_path = os.path.join(base_path, 'lib')
sys.path.append(lib_path)
sys.path.append(base_path)
import ConfigParser
import logging
import onetimepass as otp
import uuid

conf_path = os.path.join(base_path, 'conf')
log_path = os.path.join(base_path, 'log')

# 读取配置
def getConfig(confName):
	configFilePath = os.path.join(conf_path, 'config.conf')
	config = ConfigParser.ConfigParser()
	config.read(configFilePath)
	return config.get(section='default', option=confName)

# 获取日志对象
def getLogger(name):
	logger = logging.getLogger(name)
	
	if not logger.handlers:
		logger.setLevel(level = logging.INFO)
		logFile = os.path.join(log_path, 'autoLogin.log')
		handler = logging.FileHandler(logFile)
		handler.setLevel(logging.INFO)
		formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		handler.setFormatter(formatter)
		logger.addHandler(handler)
	
	return logger

# 获取一次性登录口令
def getOtpPwd():
	return otp.get_totp(getConfig('otp_key'))

# 获取UUID
def getUUID():
	return uuid.uuid1()

# 生成与serviceid、server的映射集合文件
def makeIpListConf(json):
	conf_file = os.path.join(conf_path, 'ipList.conf')
	if os.path.exists(conf_file):
		os.remove(conf_file)

	config = ConfigParser.ConfigParser()
	server_list = json['server_list']
	for item in server_list:
		if item['ipaddr'] == '':
			config.add_section(item['server_name'])
			config.set(item['server_name'],'server',item['server_id'])
			config.set(item['server_name'],'account',item['account'])
			for node in item['services']:
				if node['name'] == 'ssh':
					config.set(item['server_name'],'service',node['id'])
				elif node['name'] == 'rdpapp':
					config.set(item['server_name'],'service',node['id'])
		else:
			config.add_section(item['ipaddr'])
			config.set(item['ipaddr'],'server',item['server_id'])
			config.set(item['ipaddr'],'account',item['account'])
			for node in item['services']:
				if node['name'] == 'ssh':
					config.set(item['ipaddr'],'service',node['id'])
				elif node['name'] == 'rdpapp':
					config.set(item['ipaddr'],'service',node['id'])

		# print(item)

	with open(conf_file, 'w+') as f:
		config.write(f)

# 读取文件，获取ip与serviceid、server的映射集合
def getIpList():
	configFilePath = os.path.join(conf_path, 'ipList.conf')
	config = ConfigParser.ConfigParser()
	config.read(configFilePath)
	return config