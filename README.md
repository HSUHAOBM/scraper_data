# Scraper Data

## Purpose

使用 Flask 開發的網頁應用，練習網頁爬蟲技術。檢索和呈現不同公司相應ETF的持股權重和市值規模的變化。

## test url

1. **爬蟲**
   - [連結](https://scraper.haogooday.site/scraper)

## how use

1. 點擊上述連結進入相應的功能頁面。
2. 根據提示進行操作，輸入對應ETF代號、起始和結束日期、公司以及持股或規模選項。
3. 輸入測試密碼：6h6EEWXt7GU8。

## 事項

- **國泰 ETF**: 用 API 取得資料，處理速度較快
- **復華投信 ETF**: 用 Selenium 逐日爬取網頁資料，處理時間較長，會超過 Cloudflare 超時限制（524 錯誤）


# to do
* 擴大支援的ETF公司列表。
* 檢核使用者
* 優化處理速度

# Technologies

* **Flask**
* **Requests**
* **Jinja2**
* **Docker**
* **Selenium** (僅用於復華投信爬蟲)
* **WebDriver Manager**
