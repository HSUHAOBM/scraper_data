from flask import Blueprint, request, jsonify, render_template, flash, redirect, send_file
from modules.web_scraper import Fhtrust
from modules.api_data_fetcher import CathayETFManager
import os
import pandas as pd
import json

main = Blueprint('main', __name__)


@main.route('/scraper')
def scraper_index():
    return render_template('scraper.html')


@main.route('/crawl', methods=['POST'])
def crawl():
    try:
        etf_code = request.form['etf_code']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        data_type = request.form['data_type']
        company = request.form['company']
        password = request.form['password']

        if password != os.getenv('SCRAPER_PASSWORD'):
            flash('Invalid password')
            return redirect('/scraper')

        print(start_date, end_date, etf_code, data_type, company)

        # 國泰
        if company == 'cathay':
            etf_manager = CathayETFManager(etf_code)
            if etf_manager.fund_code:
                if data_type == 'fund_asset':
                    etf_data = etf_manager.get_etf_assets(start_date, end_date)
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

        return jsonify({'message': 'Data crawled successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})


@main.route('/download_excel/<string:report_type>', methods=['POST'])
def download_excel(report_type):
    try:
        etf_data = request.json.get('etf_data')
        excel_file_path = f"{report_type}.xlsx"

        if report_type == '持股清單':
            has_content = json.loads(request.json.get('has_content'))
            dataframes = {}

            for category in has_content:
                df = pd.DataFrame(etf_data['日期'], columns=['Date'])
                for stock_code, data in etf_data.items():
                    if stock_code != '日期':
                        stock_data = data[category]
                        df[stock_code] = stock_data
                dataframes[category] = df.set_index('Date').transpose()

            with pd.ExcelWriter(excel_file_path, engine='xlsxwriter') as writer:
                for sheet_name, data in dataframes.items():
                    data.to_excel(writer, sheet_name=sheet_name, index=True)

        elif report_type == '基金總淨值':
            df = pd.DataFrame({
                '日期': etf_data['日期'],
                '基金資產淨值': etf_data['基金資產淨值'],
                '基金在外流通單位數': etf_data['基金在外流通單位數'],
                '基金每單位淨值': etf_data['基金每單位淨值'],
            })
            df.to_excel(excel_file_path, index=False)

        else:
            return 'Invalid report type'

        response = send_file(excel_file_path, as_attachment=True)
        os.remove(excel_file_path)
        return response

    except Exception as e:
        return jsonify({'error': str(e)})
