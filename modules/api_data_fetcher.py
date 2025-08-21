import requests
from datetime import datetime, timedelta


class CathayETFManager():
    def __init__(self, etf_code, base_url="https://cwapi.cathaysite.com.tw/api/"):
        self.base_url = base_url
        self.etf_code = etf_code
        self.fund_code = self.get_etf_code(etf_code)

    # 查詢 etf代號
    def get_etf_code(self, etf_code):
        url = f"{self.base_url}Fund/GetFundDetailNavList?tab=netWorth"
        params = {'Keyword': etf_code}
        response = self.make_request(url, params)
        if response:
            etf_data = response.json()
            if 'result' in etf_data and len(etf_data['result']) > 0:
                return etf_data['result'][0].get('fundCode')
        return None

    # 發送請求
    def make_request(self, url, params):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as err:
            print(f"Error fetching data: {err}")
            return None

    # etf 的單日規模查詢
    def get_etf_assets_for_date(self, query_date):
        url = f"{self.base_url}ETF/GetETFAssets"
        params = {'FundCode': self.fund_code,
                  'SearchDate': query_date.replace('/', '-')}
        response = self.make_request(url, params)
        if response:
            assets_data = response.json()
            if assets_data['success']:
                return assets_data['result']
        return None

    # etf 的日期範圍規模查詢
    def get_etf_assets(self, start_date_str, end_date_str):
        fund_dict = {'ok': True, '日期': [], '基金資產淨值': [],
                     '基金在外流通單位數': [], '基金每單位淨值': []}
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        current_date = start_date
        while current_date <= end_date:
            query_date = current_date.strftime("%Y/%m/%d")
            etf_assets = self.get_etf_assets_for_date(query_date)
            if etf_assets:
                fund_dict['日期'].append(etf_assets['preDate'])
                fund_dict['基金資產淨值'].append(etf_assets['fundNav'])
                fund_dict['基金在外流通單位數'].append(
                    etf_assets['fundOutstandingShares'])
                fund_dict['基金每單位淨值'].append(etf_assets['fundPerNav'])
            current_date += timedelta(days=1)
        return fund_dict

    # etf 的單日持股權重查詢
    def get_stock_weights_for_date(self, query_date):
        url = f"{self.base_url}ETF/GetETFDetailStockList"
        params = {'FundCode': self.fund_code,
                  'SearchDate': query_date.replace('/', '-')}
        response = self.make_request(url, params)
        if response:
            assets_data = response.json()
            if assets_data['success']:
                return assets_data['result']
        return None

    # etf 的日期範圍持股權重查詢
    def get_stock_weights(self, start_date_str, end_date_str):
        fund_dict = {'ok': True, '日期': []}
        etf_holding_list = []
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        current_date = start_date
        while current_date <= end_date:
            query_date = current_date.strftime("%Y/%m/%d")
            etf_weights = self.get_stock_weights_for_date(query_date)
            if etf_weights:
                fund_dict['日期'].append(current_date.strftime("%Y/%m/%d"))
                for record in etf_weights:
                    stock_code = record['stockCode'].strip()
                    stock_name = record['stockName'].strip()
                    holding_quantity = record['volumn'].replace(',', '')
                    percentage = record['weights'].replace(',', '')
                    if stock_code not in etf_holding_list:
                        fund_dict.setdefault(
                            f'{stock_code}-{stock_name}', {'持股數量': [], '佔淨值比例': []})
                        day_length = len(fund_dict['日期']) - 1
                        if day_length > 0:
                            fund_dict[f'{stock_code}-{stock_name}']['持股數量'] = [0] * day_length
                            fund_dict[f'{stock_code}-{stock_name}']['佔淨值比例'] = [0] * day_length
                        etf_holding_list.append(stock_code)
                    fund_dict[f'{stock_code}-{stock_name}']['持股數量'].append(
                        holding_quantity)
                    fund_dict[f'{stock_code}-{stock_name}']['佔淨值比例'].append(
                        percentage)
            current_date += timedelta(days=1)
        self.fill_missing_data(fund_dict, len(fund_dict['日期']))
        return fund_dict

    # 填補缺失數據
    def fill_missing_data(self, fund_dict, check_data_length):
        for category in ['持股數量', '佔淨值比例']:
            for stock_code, data in fund_dict.items():
                if stock_code != '日期' and stock_code != 'ok':
                    data_length = len(data[category])
                    if check_data_length != data_length:
                        fund_dict[stock_code][category] = data.get(
                            category, []) + ['0'] * (check_data_length - data_length)
