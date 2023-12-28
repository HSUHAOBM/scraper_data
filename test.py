import pandas as pd

def process_holding_list(data_type):
    # 模擬 holding_list_dict 的格式
    holding_list_dict = {
        '日期': ['2023/12/25', '2023/12/26'],
        '2454-聯發科技': {'持股數量': ['6,156,000', '6,156,000'], '市值': ['6,094,440,000', '6,094,440,000'], '佔淨值比例': ['5.324%', '5.324%']},
        '2385-群光電子': {'持股數量': ['30,486,000', '30,486,000'], '市值': ['5,319,807,000', '5,319,807,000'], '佔淨值比例': ['4.647%', '4.647%']}
        # 其他股票以此類推
    }

    # 創建一個字典，用於存放每個分頁的 DataFrame
    dataframes = {}

    # 遍歷每個分頁
    for category in ['持股數量', '市值', '佔淨值比例']:
        # 創建 DataFrame
        df = pd.DataFrame(holding_list_dict['日期'], columns=['Date'])

        # 遍歷每支股票
        for stock_code, data in holding_list_dict.items():
            if stock_code != '日期':
                stock_data = data[category]
                df[stock_code] = stock_data

        # 將 DataFrame 寫入 Excel 文件，分頁名稱為分類名稱
        excel_sheet_name = category
        dataframes[category] = df

    # 對應 3 個分頁資料寫入
    with pd.ExcelWriter('holding_list.xlsx', engine='xlsxwriter') as writer:
        for sheet_name, data in dataframes.items():
            data.to_excel(writer, sheet_name=sheet_name, index=False)
            # df.to_excel(writer, sheet_name=excel_sheet_name, index=False)

    return dataframes

# 呼叫函數
process_holding_list('holding_list')