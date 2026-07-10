# Yan Coin 股票模拟

根据 Bitcoin 历史成交量驱动回购，模拟 Yan Coin 的股价与成交量，并生成 K 线图网页。

## 参数

| 参数 | 值 |
|------|-----|
| 初始发行量 | 10,000,000 股 |
| 初始发行价 | 1.1 HKD |
| 回购价 | 1.0 HKD |

## 使用

```bash
python Yan_coin.py
```

生成文件：
- `Yan_stock.csv` — 股价、成交量、流通股本
- `docs/Yan_stock.csv` — 同上，供网页读取
- `docs/index.html` — 交互式 K 线图（从 CSV 动态加载）

本地预览（需 HTTP 服务，直接打开 HTML 文件无法 fetch CSV）：

```bash
python Yan_coin.py
cd docs && python -m http.server 8080
# 浏览器访问 http://localhost:8080
```

## 新发行逻辑

在 `Yan_coin.py` 的 `new_issuance()` 函数中实现你的发行策略（当前为占位，默认重置至 10M）。

## 部署 GitHub Pages（GitHub Actions 自动部署）

### 一次性设置

1. 推送代码到 GitHub：

```bash
git add .
git commit -m "Add GitHub Actions Pages deployment"
git push origin main
```

2. 打开仓库 [Yueliangxi/Yan](https://github.com/Yueliangxi/Yan) → **Settings → Pages**
3. **Build and deployment → Source** 选择 **GitHub Actions**（不是 "Deploy from a branch"）
4. 保存即可

### 自动部署流程

每次 push 到 `main` 分支，`.github/workflows/pages.yml` 会：

1. 运行 `python Yan_coin.py` 生成最新数据
2. 将 `docs/` 目录（`index.html` + `Yan_stock.csv`）部署到 Pages

部署完成后访问：**https://yueliangxi.github.io/Yan/**

也可在 **Actions** 标签页手动点击 **Run workflow** 触发部署。
