# AI 出海岗位爬取与简历匹配工具

这个项目用于每天抓取国内 AI 公司、国内 AI 出海公司、云服务与开发者工具公司的公开招聘页，按你的简历定位进行规则匹配，生成 `jobs.csv` 和 `jobs.md`，并可推送到飞书群。

当前版本不使用 OpenAI API key，只做规则匹配。

## 适合匹配的方向

- AI海外增长 / AI出海增长
- 开发者生态 / 开发者社区 / 技术社区运营
- AI产品运营 / API产品运营 / 模型API运营
- 海外SEM / Google Ads / Affiliate / GTM
- B2B SaaS 增长 / 海外市场 / 产品市场

## 本地运行

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Windows PowerShell：

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

运行后会生成：

- `jobs.csv`
- `jobs.md`

## 飞书推送配置

在飞书群中添加自定义机器人，复制 Webhook。如果开启签名校验，还需要保存密钥。

本地测试：

```bash
export FEISHU_WEBHOOK_URL="你的飞书Webhook"
export FEISHU_SECRET="你的飞书签名密钥"
python main.py
```

Windows PowerShell：

```powershell
$env:FEISHU_WEBHOOK_URL="你的飞书Webhook"
$env:FEISHU_SECRET="你的飞书签名密钥"
python main.py
```

如果没有配置 `FEISHU_WEBHOOK_URL`，程序会跳过飞书推送，只生成文件。

## GitHub Actions

工作流文件在 `.github/workflows/daily.yml`。

- 每天北京时间早上 9 点运行，即 UTC 01:00
- 支持 `workflow_dispatch` 手动触发
- 运行结果会上传为 artifact：`job-results`

在 GitHub 仓库里添加 Secrets：

- `FEISHU_WEBHOOK_URL`
- `FEISHU_SECRET`

路径：

`Settings -> Secrets and variables -> Actions -> New repository secret`

## 修改公司列表

编辑 `config.yaml` 的 `company_urls`：

```yaml
company_urls:
  - name: MiniMax
    url: https://www.minimax.io/careers
```

如果某家公司官网是动态加载页面，通用爬虫可能抓不到。建议改为该公司的校招页、社招页、第三方招聘系统页，或后续为它单独写 crawler。

## 修改地点偏好

编辑 `target_locations`：

```yaml
target_locations:
  - Beijing
  - Shanghai
  - Hangzhou
  - Shenzhen
  - Chengdu
```

## 注意

第一版是轻量规则匹配，不保证抓全所有岗位。更适合作为每日岗位雷达：先帮你发现可能适合的岗位，再由你人工复核 JD 后投递。
