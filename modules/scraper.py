from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime, timedelta
import re

class ETFScraper:
    def __init__(self):
        self.service = Service(executable_path=ChromeDriverManager().install())
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-notifications")
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')

        self.driver = webdriver.Chrome(service=self.service, options=self.options)

        print("Chrome version:", self.driver.capabilities['browserVersion'])
        print("ChromeDriver version:", self.driver.capabilities['chrome']['chromedriverVersion'])

    def __del__(self):
        if self.driver:
            self.driver.quit()

    # 復華 fhtrust
    def scrape_fhtrust_data(self, etf_code, start_date_str, end_date_str, data_type):

        url = 'https://www.fhtrust.com.tw/ETF/etf_list'
        self.driver.get(url=url)

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        try:
            time.sleep(5)

            # 定位 ETF 代號輸入框
            input_xpath = '//*[@id="app"]/main/section/div[1]/div/div[2]/div[2]/div/div/input'
            input_element = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, input_xpath)))

            # 輸入 ETF 代號並按 Enter 鍵
            input_element.send_keys(etf_code)
            input_element.send_keys(Keys.ENTER)

            # 點擊搜尋結果
            try:
                result_xpath = '//*[@id="app"]/main/section/div[1]/div/div[2]/div[2]/div/div/div[2]/ul/li'
                result_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, result_xpath)))
                result_element.click()
            except:
                return {'ok': False, 'message': '無此代號'}

            # 切換至分頁
            target_element_xpath = '//*[@id="tns1-item2"]'
            target_element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, target_element_xpath)))
            target_element.click()

            # 定位日期輸入框
            date_input_xpath = '//*[@id="etfPanel3"]/section[1]/div/div/div[1]/div/input'
            date_input_element = self.driver.find_element(By.XPATH, date_input_xpath)

            # 初始化基金資料字典
            if data_type == 'fund_asset':
                fund_dict = {
                    'ok': True,
                    '日期': [],
                    '基金資產淨值': [],
                    '基金在外流通單位數': [],
                    '基金每單位淨值': [],
                }
            elif data_type == 'holding_list':
                pass

            # 日期範圍資料蒐集
            current_date = start_date
            while current_date <= end_date:
                # 使用 JavaScript 設定日期值
                self.driver.execute_script("arguments[0].value = '{}';".format(current_date.strftime("%Y/%m/%d")), date_input_element)

                # 搜尋指定日期
                search_button_xpath = '//*[@id="etfPanel3"]/section[1]/div/div/div[2]/div/button'
                search_button_element = self.driver.find_element(By.XPATH, search_button_xpath)
                search_button_element.click()

                time.sleep(1)

                no_data_locator = (By.XPATH, '//*[@id="etfPanel3"]/div/section/div/p')
                try:
                    element = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(no_data_locator))
                    print(f'{current_date} 無資料,{element.text}')

                except:
                    print(f'{current_date} 有資料')

                    # 基金資產
                    if data_type == 'fund_asset':

                        # 基金資產淨值
                        asset_value_xpath = '//*[@id="etfPanel3"]/section[2]/div/div[2]/div/div[1]/div'
                        asset_value_element = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, asset_value_xpath)))
                        asset_value = re.sub(r'\s', '', asset_value_element.get_attribute('textContent').replace('NTD', ''))

                        # 基金在外流通單位數
                        unit_xpath = '//*[@id="etfPanel3"]/section[2]/div/div[2]/div/div[2]/div'
                        unit_element = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, unit_xpath)))
                        unit_value = re.sub(r'\s', '', unit_element.get_attribute('textContent').replace('NTD', ''))

                        # 基金每單位淨值
                        net_value_xpath = '//*[@id="etfPanel3"]/section[2]/div/div[2]/div/div[3]/div'
                        net_value_element = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, net_value_xpath)))
                        net_value = re.sub(r'\s', '', net_value_element.get_attribute('textContent').replace('NTD', ''))

                        # 將資料存入字典
                        fund_dict['日期'].append(current_date.strftime("%Y/%m/%d"))
                        fund_dict['基金資產淨值'].append(asset_value)
                        fund_dict['基金在外流通單位數'].append(unit_value)
                        fund_dict['基金每單位淨值'].append(net_value)

                    # 持股名單
                    if data_type == 'holding_list':
                        pass

                current_date += timedelta(days=1)

        except Exception as e:
            print(e)
            return {'ok': False, 'message': str(e)}
        finally:
            # # 關閉瀏覽器視窗
            # driver.quit()
            pass

        return fund_dict
