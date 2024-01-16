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
        # url = f"{self.base_url}/ETF/GetETFAssets?FundCode={etf_code}&SearchDate={query_date}"
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
                # print("Invalid response format. 'success' is False.")
                return None
        except requests.exceptions.HTTPError as err:
            print(f"Error fetching ETF assets: {err}")
            return None

    # etf 的日期範圍規模查詢
    def get_etf_assets(self, start_date_str, end_date_str):
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # 初始化共用的字典
        fund_dict = {
            'ok': True,
            '日期': [],
            '基金資產淨值': [],
            '基金在外流通單位數': [],
            '基金每單位淨值': []
        }

        # 使用 while 迴圈處理日期範圍
        current_date = start_date
        while current_date <= end_date:
            query_date = current_date.strftime("%Y/%m/%d")

            # 獲取 ETF 資產
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

    # 持股權重查詢
    def get_stock_weights(self, etf_code, query_date):

        url = f"{self.base_url}/stock-weights"
        params = {'etf_code': etf_code, 'query_date': query_date}

        response = requests.get(url, params=params)

        if response.status_code == 200:
            weights_data = response.json()
            stock_weights = weights_data.get('stock_weights')
            return stock_weights
        else:
            print(
                f"Failed to fetch stock weights. Status code: {response.status_code}")
            return None


if __name__ == "__main__":

    etf_code = "00878"
    etf_manager = YuantaETFManager(etf_code)
    if etf_manager.fund_code:
        # 輸入的日期範圍字串
        start_date_str = "2023/12/01"
        end_date_str = "2024/01/05"
        fund_dict = etf_manager.get_etf_assets(
            start_date_str, end_date_str)
        if fund_dict:
            print(
                f"ETF Assets for {etf_code} from {start_date_str} to {end_date_str}: {fund_dict}")
    else:
        print('查無此etf')
