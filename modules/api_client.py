import requests
from datetime import datetime, timedelta


class YuantaETFManager():
    def __init__(self, etf_code):
        self.base_url = "https://cwapi.cathaysite.com.tw/api/"
        self.etf_code = etf_code
        self.fund_code = self.get_etf_code(etf_code)

    # 查詢 etf代號
    def get_etf_code(self, etf_code):
        url = f"{self.base_url}Fund/GetFundDetailNavList?tab=netWorth"
        params = {'Keyword': etf_code}

        response = requests.get(url, params=params)

        if response.status_code == 200:
            etf_data = response.json()

            if 'result' in etf_data and len(etf_data['result']) > 0:
                # 檢查 'result' 是否存在並且至少有一個元素
                return etf_data['result'][0].get('fundCode')
            else:
                print("ETF data not found in the response.")
                return None
        else:
            print(
                f"Failed to fetch ETF code. Status code: {response.status_code}")
            return None

    # etf 的單日規模查詢
    def get_etf_assets_for_date(self, query_date):
        url = f"{self.base_url}ETF/GetETFAssets"
        try:
            params = {'FundCode': self.fund_code,
                      'SearchDate': query_date.replace('/', '-')}
            response = requests.get(url, params=params)
            response.raise_for_status()

            assets_data = response.json()

            if assets_data['success']:
                return assets_data['result']
            else:
                return None
        except requests.exceptions.HTTPError as err:
            print(f"Error fetching ETF assets: {err}")
            return None

    # etf 的日期範圍規模查詢
    def get_etf_assets(self, start_date_str, end_date_str):
        fund_dict = {
            'ok': True,
            '日期': [],
            '基金資產淨值': [],
            '基金在外流通單位數': [],
            '基金每單位淨值': []
        }

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # 使用 while 迴圈處理日期範圍
        current_date = start_date
        while current_date <= end_date:
            query_date = current_date.strftime("%Y/%m/%d")

            etf_assets = self.get_etf_assets_for_date(query_date)
            if etf_assets:
                # 將數據存入字典
                fund_dict['日期'].append(etf_assets['preDate'])
                fund_dict['基金資產淨值'].append(etf_assets['fundNav'])
                fund_dict['基金在外流通單位數'].append(
                    etf_assets['fundOutstandingShares'])
                fund_dict['基金每單位淨值'].append(etf_assets['fundPerNav'])

            # 日期 +1 天
            current_date += timedelta(days=1)

        return fund_dict

    # etf 的單日持股權重查詢
    def get_stock_weights_for_date(self, query_date):

        url = f"{self.base_url}ETF/GetETFDetailStockList"

        try:
            params = {'FundCode': self.fund_code,
                      'SearchDate': query_date.replace('/', '-')}
            response = requests.get(url, params=params)
            response.raise_for_status()

            assets_data = response.json()

            if assets_data['success']:
                return assets_data['result']
            else:
                return None
        except requests.exceptions.HTTPError as err:
            print(f"Error fetching ETF assets: {err}")
            return None

    # etf 的日期範圍持股權重查詢
    def get_stock_weights(self, start_date_str, end_date_str):
        fund_dict = {
            'ok': True,
            '日期': [],
        }
        etf_holding_list = []

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # 使用 while 迴圈處理日期範圍
        current_date = start_date
        while current_date <= end_date:

            query_date = current_date.strftime("%Y/%m/%d")

            etf_weights = self.get_stock_weights_for_date(query_date)
            if etf_weights:

                fund_dict.setdefault('日期', []).append(
                    current_date.strftime("%Y/%m/%d"))

                for record in etf_weights:

                    stock_code = record['stockCode'].strip()
                    stock_name = record['stockName'].strip()
                    holding_quantity = record['volumn'].replace(',', '')
                    percentage = record['weights'].replace(',', '')

                    # 判斷是否有新增或替除
                    if stock_code not in etf_holding_list:

                        # 使用 setdefault 確認股票 key 是否存在，如果不存在則新增
                        fund_dict.setdefault(
                            f'{stock_code}-{stock_name}', {'持股數量': [], '佔淨值比例': []})

                        # 跑到第幾天, 而需要補的 0 次數
                        day_length = len(fund_dict['日期']) - 1
                        if day_length > 0:
                            fund_dict[f'{stock_code}-{stock_name}']['持股數量'] = [
                                0] * day_length

                            fund_dict[f'{stock_code}-{stock_name}']['佔淨值比例'] = [
                                0] * day_length

                        etf_holding_list.append(stock_code)

                    # 將數據存入字典
                    fund_dict[f'{stock_code}-{stock_name}']['持股數量'].append(
                        holding_quantity)

                    fund_dict[f'{stock_code}-{stock_name}']['佔淨值比例'].append(
                        percentage)

            # 日期 +1 天
            current_date += timedelta(days=1)

            check_data_length = len(fund_dict['日期'])
            for category in ['持股數量', '佔淨值比例']:
                # 遍歷每支股票
                for stock_code, data in fund_dict.items():
                    if stock_code != '日期' and stock_code != 'ok':
                        data_length = len(data[category])
                        if check_data_length != data_length:
                            fund_dict[stock_code][category] = data.get(
                                category, []) + ['0'] * (check_data_length - data_length)

        return fund_dict


if __name__ == "__main__":

    etf_code = "00878"
    etf_manager = YuantaETFManager(etf_code)
    if etf_manager.fund_code:
        #     # 輸入的日期範圍字串
        #     start_date_str = "2024-01-01"
        #     end_date_str = "2024-01-05"
        #     fund_dict = etf_manager.get_etf_assets(
        #         start_date_str, end_date_str)
        #     if fund_dict:
        #         print(
        #             f"ETF Assets for {etf_code} from {start_date_str} to {end_date_str}: {fund_dict}")
        # else:
        #     print('查無此etf')
        start_date_str = "2023-11-24"
        end_date_str = "2023-11-28"
        result = etf_manager.get_stock_weights(start_date_str, end_date_str)
        print(result)
