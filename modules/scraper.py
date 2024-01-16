from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

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

        self.driver = webdriver.Chrome(
            service=self.service, options=self.options)

        print("Chrome version:", self.driver.capabilities['browserVersion'])
        print("ChromeDriver version:",
              self.driver.capabilities['chrome']['chromedriverVersion'])

    def __del__(self):
        if self.driver:
            self.driver.quit()


class Fhtrust(ETFScraper):
    # 復華 fhtrust
    def scrape_data(self, etf_code, start_date_str, end_date_str, data_type):

        url = 'https://www.fhtrust.com.tw/ETF/etf_list'
        self.driver.get(url=url)

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        try:
            time.sleep(5)

            # 定位 ETF 代號輸入框
            input_xpath = '//*[@id="app"]/main/section/div[1]/div/div[2]/div[2]/div/div/input'
            input_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, input_xpath)))

            # 輸入 ETF 代號並按 Enter 鍵
            input_element.send_keys(etf_code)
            input_element.send_keys(Keys.ENTER)

            # 點擊搜尋結果
            try:
                result_xpath = '//*[@id="app"]/main/section/div[1]/div/div[2]/div[2]/div/div/div[2]/ul/li'
                result_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, result_xpath)))
                result_element.click()
            except:
                return {'ok': False, 'message': '無此代號'}

            actions = ActionChains(self.driver)

            # 切換至分頁
            target_element_xpath = '//*[@id="tns1-item2"]'
            target_element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, target_element_xpath)))

            actions.move_to_element(
                target_element).click().perform()

            print('切換分頁成功')

            # 等待日期輸入框可見
            date_input_xpath = '//*[@id="etfPanel3"]/section[1]/div/div/div[1]/div/input'
            date_input_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, date_input_xpath))
            )

            time.sleep(1)
            fund_dict = {
                'ok': True,
                '日期': [],
            }
            # 初始化基金資料字典

            if data_type == 'holding_list':
                # 持股清單全部顯示
                holding_more_btn_xpath = '//*[@id="etfPanel3"]/div/section[1]/div/div[3]/div/button'
                holding_more_element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, holding_more_btn_xpath))
                )

                # 使用 ActionChains 執行點擊操作
                actions.move_to_element(holding_more_element).click().perform()
                # 紀錄 ETF 持股
                etf_holding_list = []

            # 日期範圍資料蒐集
            current_date = start_date
            while current_date <= end_date:
                # 使用 JavaScript 設定日期值
                self.driver.execute_script("arguments[0].value = '{}';".format(
                    current_date.strftime("%Y/%m/%d")), date_input_element)

                # 搜尋指定日期
                search_button_xpath = '//*[@id="etfPanel3"]/section[1]/div/div/div[2]/div/button'
                search_button_element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, search_button_xpath))
                )
                actions.move_to_element(
                    search_button_element).click().perform()

                no_data_locator = (
                    By.XPATH, '//*[@id="etfPanel3"]/div/section/div/p')
                try:
                    element = WebDriverWait(self.driver, 12).until(
                        EC.presence_of_element_located(no_data_locator))
                    print(f'{current_date} 無資料,{element.text}')

                except:
                    print(f'{current_date} 有資料')

                    # 基金資產
                    if data_type == 'fund_asset':

                        # 基金資產淨值
                        asset_value_xpath = '//*[@id="etfPanel3"]/section[2]/div/div[2]/div/div[1]/div'
                        asset_value_element = WebDriverWait(self.driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, asset_value_xpath)))
                        asset_value = re.sub(r'\s', '', asset_value_element.get_attribute(
                            'textContent').replace('NTD', ''))

                        # 基金在外流通單位數
                        unit_xpath = '//*[@id="etfPanel3"]/section[2]/div/div[2]/div/div[2]/div'
                        unit_element = WebDriverWait(self.driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, unit_xpath)))
                        unit_value = re.sub(r'\s', '', unit_element.get_attribute(
                            'textContent').replace('NTD', ''))

                        # 基金每單位淨值
                        net_value_xpath = '//*[@id="etfPanel3"]/section[2]/div/div[2]/div/div[3]/div'
                        net_value_element = WebDriverWait(self.driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, net_value_xpath)))
                        net_value = re.sub(r'\s', '', net_value_element.get_attribute(
                            'textContent').replace('NTD', ''))

                        # 將資料存入字典
                        fund_dict['日期'].append(
                            current_date.strftime("%Y/%m/%d"))
                        fund_dict.setdefault('基金資產淨值', []).append(asset_value)
                        fund_dict.setdefault(
                            '基金在外流通單位數', []).append(unit_value)
                        fund_dict.setdefault('基金每單位淨值', []).append(net_value)

                    # 持股名單
                    # '''
                    # holding_list_dict = {
                    # '日期': ['2023/12/25', '2023/12/26'],
                    # '2454-聯發科技': {'持股數量': ['6,156,000', '6,156,000'], '市值': ['6,094,440,000', '6,094,440,000'], '佔淨值比例': ['5.324%', '5.324%']},
                    # '2385-群光電子': {'持股數量': ['30,486,000', '30,486,000'], '市值': ['5,319,807,000', '5,319,807,000'], '佔淨值比例': ['4.647%', '4.647%']}
                    # # 其他股票以此類推
                    # }
                    # '''
                    if data_type == 'holding_list':
                        # 定位表格
                        holding_rows_xpath = '//*[@id="etfPanel3"]/div/section[1]/div/div[3]/div/div/table/tbody/tr'
                        holding_rows = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, holding_rows_xpath))
                        )
                        # 使用 setdefault 確認日期 key 是否存在，如果不存在則新增
                        fund_dict.setdefault('日期', []).append(
                            current_date.strftime("%Y/%m/%d"))

                        # 表格數據解析
                        for row in holding_rows:
                            # 股票代號
                            stock_code_xpath = './/td[1]/span'
                            stock_code_element = row.find_element(
                                By.XPATH, stock_code_xpath)
                            stock_code = stock_code_element.text.strip()

                            # 股票名稱
                            stock_name_xpath = './/td[2]/span'
                            stock_name_element = row.find_element(
                                By.XPATH, stock_name_xpath)
                            stock_name = stock_name_element.text.strip()

                            # 持股數量
                            holding_quantity_xpath = './/td[3]/span'
                            holding_quantity_element = row.find_element(
                                By.XPATH, holding_quantity_xpath)
                            holding_quantity = holding_quantity_element.text.strip().replace(',', '')

                            # 市值
                            market_value_xpath = './/td[4]/span'
                            market_value_element = row.find_element(
                                By.XPATH, market_value_xpath)
                            market_value = market_value_element.text.strip().replace(',', '')

                            # 淨值比例
                            percentage_xpath = './/td[5]/span'
                            percentage_element = row.find_element(
                                By.XPATH, percentage_xpath)
                            percentage = percentage_element.text.strip().replace(',', '')

                            # 判斷是否有新增或替除
                            if stock_code not in etf_holding_list:

                                # 使用 setdefault 確認股票 key 是否存在，如果不存在則新增
                                fund_dict.setdefault(
                                    f'{stock_code}-{stock_name}', {'持股數量': [], '市值': [], '佔淨值比例': []})

                                # 跑到第幾天, 而需要補的 None 次數
                                day_length = len(fund_dict['日期']) - 1
                                if day_length > 0:
                                    fund_dict[f'{stock_code}-{stock_name}']['持股數量'] = [
                                        None] * day_length
                                    fund_dict[f'{stock_code}-{stock_name}']['市值'] = [
                                        None] * day_length
                                    fund_dict[f'{stock_code}-{stock_name}']['佔淨值比例'] = [
                                        None] * day_length

                                etf_holding_list.append(stock_code)

                            # 將數據存入字典
                            fund_dict[f'{stock_code}-{stock_name}']['持股數量'].append(
                                holding_quantity)
                            fund_dict[f'{stock_code}-{stock_name}']['市值'].append(
                                market_value)
                            fund_dict[f'{stock_code}-{stock_name}']['佔淨值比例'].append(
                                percentage)

                current_date += timedelta(days=1)

            # 持股名單 檢查處理 替除補 None
            if data_type == 'holding_list':
                check_data_length = len(fund_dict['日期'])
                for category in ['持股數量', '市值', '佔淨值比例']:
                    # 遍歷每支股票
                    for stock_code, data in fund_dict.items():
                        if stock_code != '日期' and stock_code != 'ok':
                            data_length = len(data[category])
                            if check_data_length != data_length:
                                fund_dict[stock_code][category] = data.get(
                                    category, []) + ['0'] * (check_data_length - data_length)

        except Exception as e:
            print(e)
            return {'ok': False, 'message': str(e)}
        finally:
            # # 關閉瀏覽器視窗
            self.driver.quit()
            pass

        return fund_dict


