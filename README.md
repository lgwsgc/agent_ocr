# 营业执照 OCR Agent 演示项目

面向分享演示的轻量项目：以营业执照为识别对象，展示 OCR + Agent 的字段抽取、规则校验、自动修复和可解释输出。

## 演示目标

传统 OCR 输出全文文本；本项目展示 Agent OCR 如何把全文文本变成可信结构化结果：

```text
读取 -> 抽取 -> 校验 -> 修复 -> 解释
```

## 识别字段

- 统一社会信用代码
- 名称
- 类型
- 法定代表人
- 注册资本
- 成立日期
- 营业期限
- 住所
- 经营范围
- 登记机关
- 核准日期

## 快速运行

当前版本已经内置默认样本和默认输出路径，演示时可以尽量少输参数。

运行默认营业执照图片，演示 PaddleOCR-VL 图片识别和 Agent 后处理：

```powershell
python app.py
```

运行默认文本样本，演示字段抽取、规则校验和自动修复：

```powershell
python app.py --mode text
```

传入自定义 OCR 文本文件：

```powershell
python app.py --text samples/license_ocr_with_errors.txt
```

可视化分享 Demo：

```powershell
python demo_gui.py
```

左侧展示营业执照图片，右侧展示 Agent 运行结果。建议现场先点击“运行文本兜底 Demo”，快速展示 LangChain 工具调用和自动修复；再点击“加载真实图片 OCR 结果”，展示 PaddleOCR-VL 已识别文本如何进入同一套 Agent 工具链。

## Agent 工具链

当前 demo 使用 LangChain Core 的 `StructuredTool` 封装四个工具。工具名保留英文是为了符合 LangChain 调用习惯，业务字段输出使用中文。

- `extract_business_license_fields`：从 OCR 全文中抽取营业执照字段
- `validate_business_license_fields`：校验统一社会信用代码、日期、出资额/注册资本等字段
- `repair_business_license_fields`：根据校验失败原因修复 O/0、I/1、日期等 OCR 常见错误
- `llm_semantic_repair_business_license_fields`：使用大模型修复经营范围、住所、名称等语义型 OCR 错误

这对应分享中的“工具使用（函数调用）”章节：Agent 不直接相信 OCR 文本，而是通过工具调用把识别结果转成可校验、可修复、可解释的结构化 JSON。

## 中文字段输出

最终 JSON 中的营业执照字段使用中文键名，便于业务人员阅读和现场讲解：

```json
{
  "统一社会信用代码": "91110102082841146L",
  "名称": "中兴华会计师事务所（特殊普通合伙）",
  "类型": "特殊普通合伙企业",
  "法定代表人": "李尊农、乔久华",
  "注册资本": "8916万元",
  "成立日期": "2013年11月04日",
  "营业期限": "",
  "住所": "北京市丰台区丽泽路20号院1号楼南楼20层",
  "经营范围": "一般项目：工程造价咨询业务；工程管理服务；资产评估。",
  "登记机关": "北京市市场监督管理局",
  "核准日期": "2025年02月27日"
}
```

## 大模型语义后处理

规则工具适合修复统一社会信用代码、日期这类可校验字段；大模型适合修复经营范围中的语义型 OCR 错误。例如：

```text
工程浩价咨洵业务 -> 工程造价咨询业务
代理记帐 -> 代理记账
```

运行示例：

```powershell
$env:ANTHROPIC_API_KEY='你的 key'
$env:ANTHROPIC_BASE_URL='https://crs.hexai.cn/api'
$env:SSL_CERT_FILE='D:\conda_envs\company_tool\lib\site-packages\certifi\cacert.pem'
python app.py --text samples/license_ocr_semantic_errors.txt
```

默认策略：如果当前环境中存在 `ANTHROPIC_API_KEY`，程序会自动启用大模型语义后处理；如果没有 key，则只运行规则抽取、校验和修复。需要强制关闭时使用：

```powershell
python app.py --text samples/license_ocr_semantic_errors.txt --no-llm-postprocess
```

## 使用本地 PaddleOCR-VL-1.6

本机已经在 `company_tool` conda 环境中配置好 PaddleOCR-VL-1.6。建议直接使用该环境的 Python：

```powershell
& 'D:\conda_envs\company_tool\python.exe' app.py
```

CPU 推理营业执照图片：

```powershell
$env:HTTP_PROXY='http://127.0.0.1:7890'
$env:HTTPS_PROXY='http://127.0.0.1:7890'
$env:ALL_PROXY='http://127.0.0.1:7890'
& 'D:\conda_envs\company_tool\python.exe' app.py --image
```

也可以传入其他营业执照图片：

```powershell
& 'D:\conda_envs\company_tool\python.exe' app.py --image --image-path .\你的营业执照图片.jpg
```

默认输出路径：

- 图片样本：`outputs/license_image_agent_result.json`
- 文本样本：`outputs/license_agent_result.json`
- 启用大模型语义后处理的文本样本：`outputs/license_llm_semantic_result.json`

需要覆盖默认路径时再传入 `--out` 和 `--ocr-out`。

需要注意：项目可以处理新的营业执照图片，但效果取决于图片清晰度、倾斜程度、印章遮挡、版式差异和 PaddleOCR-VL 的识别质量。Agent 后处理能修复一部分可校验错误和语义错字，但不会保证所有字段都 100% 正确；低置信或缺失字段仍应进入人工复核。

当前 Windows CPU 路径使用 PaddleOCR-VL 的 `transformers` 引擎，避免 Paddle 原生动态引擎在本机 CPU 上崩溃。第一次运行会下载模型，CPU 会慢一些，适合提前跑一遍做缓存。

已缓存模型位置：

```text
C:\Users\EDY\.paddlex\official_models\PaddleOCR-VL-1.6
C:\Users\EDY\.paddlex\official_models\PP-DocLayoutV3
C:\Users\EDY\.paddlex\official_models\PP-DocLayoutV3_safetensors
```

## 分享重点

分享重点不是底层 OCR 训练，而是 Agent 如何组织 OCR、字段抽取、规则校验、错误修复、大模型语义后处理和可解释输出。
