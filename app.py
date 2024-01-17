from flask import Flask, request, jsonify, render_template, render_template, send_file, flash, redirect
import pandas as pd
import os
from modules.scraper import Fhtrust
from modules.api_client import YuantaETFManager
import json

app = Flask(__name__)

app.secret_key = '05fb22e618796839264428ecd52995eecd451d2a9ac26b6e'


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
    password = request.form.get('password')

    if password != '6h6EEWXt7GU8':
        flash('無權限操作', 'error')
        return redirect('/scraper')

    print(start_date, end_date, etf_code, data_type, company)

    # 元大
    if company == 'yuanta':
        etf_manager = YuantaETFManager(etf_code)
        if etf_manager.fund_code:
            if data_type == 'fund_asset':
                etf_data = etf_manager.get_etf_assets(
                    start_date, end_date)
                if etf_data['ok']:
                    return render_template('fund_asset_result.html', etf_data=etf_data, etf_code=etf_code, company=company)
            if data_type == 'holding_list':
                etf_data = etf_manager.get_stock_weights(
                    start_date, end_date)
                if etf_data['ok']:
                    return render_template('fund_holding_list.html', etf_data=etf_data, etf_code=etf_code, company=company, has_content=['持股數量', '佔淨值比例'])
        else:
            flash('無此代號', 'error')
            return redirect('/scraper')

    # 復華
    if company == 'fhtrust':
        scraper = Fhtrust()
        etf_data = scraper.scrape_data(
            etf_code, start_date, end_date, data_type)

        if etf_data['ok'] and data_type == 'fund_asset':
            return render_template('fund_asset_result.html', etf_data=etf_data, etf_code=etf_code, company=company)
        elif etf_data['ok'] and data_type == 'holding_list':
            return render_template('fund_holding_list.html', etf_data=etf_data, etf_code=etf_code, company=company, has_content=['持股數量', '市值', '佔淨值比例'])
        else:
            flash(etf_data['message'], 'error')
            return redirect('/scraper')


# excel 下載
@app.route('/download_excel/<string:report_type>', methods=['POST'])
def download_excel(report_type):
    try:
        etf_data = request.json.get('etf_data')
        has_content = json.loads(request.json.get('has_content'))
        excel_file_path = f"{report_type}.xlsx"

        if report_type == '持股清單':
            # 創建一個字典，用於存放每個分頁的 DataFrame
            dataframes = {}

            # 遍歷每個分頁
            for category in has_content:
                # 創建 DataFrame
                df = pd.DataFrame(etf_data['日期'], columns=['Date'])

                # 遍歷每支股票
                for stock_code, data in etf_data.items():
                    if stock_code != '日期':
                        stock_data = data[category]
                        df[stock_code] = stock_data

                # 將 DataFrame 寫入 Excel 文件，分頁名稱為分類名稱
                excel_sheet_name = category
                dataframes[category] = df.set_index('Date').transpose()
            # 對應 分頁資料寫入
            with pd.ExcelWriter(excel_file_path, engine='xlsxwriter') as writer:
                for sheet_name, data in dataframes.items():
                    data.to_excel(writer, sheet_name=sheet_name, index=True)

        elif report_type == '基金總淨值':
            # 如果要下載基金總淨值
            df = pd.DataFrame({
                '日期': etf_data['日期'],
                '基金資產淨值': etf_data['基金資產淨值'],
                '基金在外流通單位數': etf_data['基金在外流通單位數'],
                '基金每單位淨值': etf_data['基金每單位淨值'],
            })
            df.to_excel(excel_file_path, index=False)

        else:
            return 'Invalid report type'

        # 發送檔案到客戶端
        response = send_file(excel_file_path, as_attachment=True)

        # 刪除伺服器本地的檔案
        os.remove(excel_file_path)
        return response

    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
