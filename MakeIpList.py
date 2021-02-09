#!/usr/bin/env python
#coding=utf-8
import os
import sys
base_path = os.path.split(os.path.realpath(__file__))[0]
lib_path = os.path.join(base_path, 'lib')
util_path = os.path.join(base_path, 'util')
sys.path.append(lib_path)
sys.path.append(util_path)
import Util
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json

driver_path = os.path.join(base_path, 'driver')
log_path = os.path.join(base_path, 'log')

logger = Util.getLogger('MakeIpList.py')
logger.info("start make ip list")
print('start make ip list')

login_name = Util.getConfig('login_name')
login_pwd = Util.getConfig('login_pwd')
baoleiji_ip = Util.getConfig('baoleiji_ip')
wait_timeout = int(Util.getConfig('wait_timeout'))

dcap = dict(DesiredCapabilities.PHANTOMJS)
dcap["phantomjs.page.settings.userAgent"] = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36")
browser = webdriver.PhantomJS(executable_path=os.path.join(driver_path, 'phantomjs'), desired_capabilities=dcap, service_args=['--ignore-ssl-errors=true'], service_log_path=os.path.join(log_path, 'autoLogin.log'))
browser.set_window_size(1120, 550)
browser.implicitly_wait(wait_timeout)

try:
	browser.get(baoleiji_ip)

	user = browser.find_element_by_id("userName")
	user.send_keys(login_name)

	password = browser.find_element_by_id("password")
	password.send_keys(login_pwd)
	password.send_keys(Keys.RETURN)

	OptPassword = browser.find_element_by_name("dyncode")
	myoptKey = Util.getOtpPwd()
	OptPassword.send_keys(myoptKey)
	OptPassword.send_keys(Keys.RETURN)

	this_id = str(Util.getUUID())
	get_ip_list_js = '$.post( \
						"https://0.0.0.0/client/get_server_grid_bypage.php",  \
						 { \
							name_ipaddr: "", \
							proto: "", \
							systype: 0, \
							domain: "", \
							server_grid_filter: "all", \
							group: "all", \
							worksheet: 0, \
							pageindex: 1, \
							pagesize: 3000, \
							order: "server_name", \
							sort: "asc" \
						},\
						function(data){$("body").append("<zlf id=\\"'+this_id+'\\" rsp=\'"+data+"\'></zlf>")});'
	# print(get_ip_list_js)
	browser.execute_script(get_ip_list_js)

	rsp = WebDriverWait(browser,wait_timeout,0.5).until(EC.presence_of_element_located((By.ID,this_id)))
	rsp = rsp.get_attribute('rsp')
	rsp = json.loads(rsp)
	# print(rsp)
	Util.makeIpListConf(rsp)
	logger.info("success")
	print('success')
except Exception as e:
	print(e)
	logger.error(e)
finally:
	browser.quit()
