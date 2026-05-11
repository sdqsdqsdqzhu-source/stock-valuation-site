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
- Reddit：优先使用官方 OAuth API；需要在 Vercel 设置 `REDDIT_CLIENT_ID`、`REDDIT_CLIENT_SECRET`、`REDDIT_USER_AGENT`
- X/Google Trends/News：显示连接器状态；X 需要 `X_BEARER_TOKEN` 且账户有 credits

## 说明

当前估值结果是研究工具，不是投资建议。网络或 API 不可用时，页面会明确显示“无法获得 / unavailable”，不会用模拟数据冒充真实数据。

## Vercel 部署

项目已经包含 Vercel serverless 入口：

- `public/`：前端静态页面
- `api/analyze.py`：云端 `/api/analyze?ticker=...`
- `vercel.json`：静态资源和 Python API 路由

注意：部署到 Vercel 后，本机 Futu OpenD 无法在云端访问，行情会尝试 Yahoo/Nasdaq/SEC 等公开数据源；仍拿不到时会显示不可用。`FRED_API_KEY`、`X_BEARER_TOKEN`、Reddit OAuth 等需要在 Vercel 项目环境变量里单独设置。

### 从 GitHub 导入

1. 打开 <https://vercel.com/new>
2. 选择 GitHub 仓库 `sdqsdqsdqzhu-source/stock-valuation-site`
3. Framework Preset 选择 `Other`
4. 保持 Build Command / Output Directory 默认即可，项目使用 `vercel.json`
5. 点击 Deploy

推荐环境变量：

- `FRED_API_KEY`：宏观利率数据
- `REDDIT_CLIENT_ID`：Reddit App 的 client id
- `REDDIT_CLIENT_SECRET`：Reddit App 的 secret
- `REDDIT_USER_AGENT`：例如 `windows:stock-valuation-site:v1.0 (by u_yourname)`
- `X_BEARER_TOKEN`：X recent search（如果账户有 credits）
- `SEC_USER_AGENT`：SEC 请求标识，例如 `David stock dashboard your-email@example.com`
