# Stock Valuation Router

本地股票分析网站第一版。输入 ticker 后，网站会展示：

- 财务质量：收入增长、毛利率、净利率、FCF margin、负债、ROE、现金转化
- 估值路由：Forward PE、PE、PEG、P/S、P/B、P/FCF、EV/EBITDA、DCF
- 市场热度：流动性、社媒热度框架、连接器状态
- 风险雷达：现金流、负债、估值、地缘、关税、转型风险
- 宏观政策：利率、财政/政策催化、关税/出口管制、地缘暴露

## 运行

```powershell
cd C:\Users\David\market_dashboard\stock_valuation_site
& C:\Users\David\python312\python.exe -X utf8 server.py
```

然后打开：

```text
http://127.0.0.1:8765
```

## 当前数据源

- Futu OpenD：如果本机 OpenD 可连接，会优先读取 `get_market_snapshot`
- SEC EDGAR：已写入 companyfacts 读取逻辑；网络不可用时自动降级
- FRED：设置 `FRED_API_KEY` 后会读取 2Y/10Y/Fed Funds
- Reddit/X/Google Trends/News：第一版先显示连接器状态，后续接入 API token

## 说明

当前估值结果是研究工具，不是投资建议。网络或 API 不可用时，页面会使用 deterministic fallback，让 UI 和模型逻辑保持可演示。

## Vercel 部署

项目已经包含 Vercel serverless 入口：

- `public/`：前端静态页面
- `api/analyze.py`：云端 `/api/analyze?ticker=...`
- `vercel.json`：静态资源和 Python API 路由

注意：部署到 Vercel 后，本机 Futu OpenD 无法在云端访问，行情会自动降级到 fallback 或其他公开数据源。`FRED_API_KEY`、`X_BEARER_TOKEN` 等需要在 Vercel 项目环境变量里单独设置。
