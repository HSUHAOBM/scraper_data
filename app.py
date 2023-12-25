from flask import Flask, request, jsonify, render_template, render_template, send_file, flash, redirect, make_response
import pandas as pd
import os
from datetime import datetime
from modules.scraper import ETFScraper

app = Flask(__name__)

app.secret_key = 'your_secret_key'  # 設置一個密鑰，用於啟用 flash 消息

@app.route('/')
def home():
    return render_template('index.html', message='Hello from Docker and Flask!')

@app.route('/scraper')
def scraper_index():
    return render_template('scraper.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    etf_code = request.form.get('etf_code')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    data_type = request.form.get('data_type')
    company = request.form.get('company')

    print(start_date, end_date, etf_code, data_type, company)

    scraper = ETFScraper()
    if company == 'fhtrust':
        etf_data = scraper.scrape_fhtrust_data(etf_code, start_date, end_date, data_type)

        if etf_data['ok'] and data_type == 'fund_asset':
            # 如果爬取成功，顯示結果
            return render_template('fund_asset_result.html', etf_data=etf_data, etf_code=etf_code)
        elif etf_data['ok'] and data_type == 'holding_list':
            pass

        else:
            # 如果爬取失敗，顯示錯誤消息並重新導向到爬蟲頁面
            flash(etf_data['message'], 'error')
            return redirect('/scraper')

@app.route('/download_excel', methods=['POST'])
def download_excel():
    try:
        # 從前端獲取 etf_data
        etf_data = request.json.get('etf_data')
        df = pd.DataFrame({
            '日期': etf_data['日期'],
            '基金資產淨值': etf_data['基金資產淨值'],
            '基金在外流通單位數': etf_data['基金在外流通單位數'],
            '基金每單位淨值': etf_data['基金每單位淨值'],
        })

        # print(df)
        # '''
        #  日期           基金資產淨值      基金在外流通單位數 基金每單位淨值
        # 0  2023/12/01  106,994,957,274  5,802,639,000   18.44
        # 1  2023/12/04  107,799,380,136  5,803,639,000   18.57
        # '''

        excel_file_path = 'sample_data.xlsx'
        df.to_excel(excel_file_path, index=False)

        # 發送檔案到客戶端
        response = send_file(excel_file_path, as_attachment=True)

        # 刪除伺服器本地的檔案
        os.remove(excel_file_path)

        return response

    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)})


# @app.route('/download_excel')
# def download_excel():
#     # 創建一個簡單的 DataFrame，這裡只是示範，實際上你需要根據你的資料生成 DataFrame
#     start_date_str = request.args.get('start_date')
#     end_date_str = request.args.get('end_date')
#     etf_code = request.args.get('etf_code')
#     print(start_date_str,end_date_str,etf_code)

#     # 呼叫 scrape_data 函數並傳遞參數
#     data = scrape_data(etf_code, start_date_str, end_date_str)

#     df = pd.DataFrame(data)

#     # 將 DataFrame 寫入 Excel 檔案
#     excel_file_path = 'sample_data.xlsx'
#     df.to_excel(excel_file_path, index=False)

#     # 提供下載連結
#     return send_file(excel_file_path, as_attachment=True)

# @app.route('/download_excel')
# def download_excel():
#     # 創建一個簡單的 DataFrame，這裡只是示範，實際上你需要根據你的資料生成 DataFrame
#     data = {'Name': ['Alice', 'Bob', 'Charlie'],
#             'Age': [25, 30, 35]}
#     df = pd.DataFrame(data)

#     # 將 DataFrame 寫入 Excel 檔案
#     excel_file_path = 'sample_data.xlsx'
#     df.to_excel(excel_file_path, index=False)

#     # 提供下載連結
#     return send_file(excel_file_path, as_attachment=True)

@app.route('/download_specific_excel')
def download_specific_excel():
    # 取得起始、結束日期和 ETF 代號參數
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    etf_code = request.args.get('etf_code')

    try:
        # 將字串轉換為日期，使用 pd.to_datetime，並指定格式
        start_date = pd.to_datetime(start_date_str, format='%Y-%m-%d')
        end_date = pd.to_datetime(end_date_str, format='%Y-%m-%d')

        # 在這裡根據你的邏輯生成特定日期範圍和 ETF 代號的 DataFrame
        date_range = pd.date_range(start=start_date, end=end_date)
        data = {
            'AAPL': [100] * len(date_range),  # 這裡可以換成對應 ETF 的實際資料
            'GOOGL': [1200] * len(date_range),
            'MSFT': [200] * len(date_range)
        }

        # 日期格式設定
        df = pd.DataFrame(data, index=date_range)

        # 將 DataFrame 轉置，讓 ETF 代號成為列標籤
        df.index = df.index.strftime('%Y-%m-%d')

        df_transposed = df.transpose()

        # 將 DataFrame 寫入 Excel 檔案，檔案名稱包含起始和結束日期以及 ETF 代號
        excel_file_path = f'{etf_code}_{start_date_str}_to_{end_date_str}_{etf_code}.xlsx'

        # 使用 ExcelWriter 並指定日期格式
        with pd.ExcelWriter(excel_file_path, engine='openpyxl', date_format='yyyy-mm-dd', datetime_format='yyyy-mm-dd') as writer:
            df_transposed.to_excel(writer, index_label='stock')

            # 取得 workbook 對象
            workbook = writer.book

            # 查看 sheets
            sheets = workbook.sheetnames
            print("Sheets:", sheets)

            # 選擇第一個 sheet
            worksheet = workbook[sheets[0]]

            # 從第一列開始檢查每一行的第一欄是否有值
            sheet_rowx = 1
            while worksheet.cell(row=sheet_rowx, column=1).value is not None:
                sheet_rowx += 1

            # 在找到的第一個空行中寫入特定的文字
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            worksheet.cell(row=sheet_rowx, column=1, value=f'輸出時間{current_time}')

            # 合併指定的儲存格
            worksheet.merge_cells(start_row=sheet_rowx, start_column=1, end_row=sheet_rowx, end_column=10)

        # 發送檔案到客戶端
        response = send_file(excel_file_path, as_attachment=True)

        # 刪除伺服器本地的檔案
        os.remove(excel_file_path)

        return response

    except ValueError:
        return "Invalid date format. Please enter dates in the format YYYY-MM-DD."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)