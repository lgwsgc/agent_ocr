# Business License OCR Agent Demo

面向分享演示的轻量项目：以营业执照为识别对象，展示 OCR + Agent 的字段抽取、规则校验、自动修复和可解释输出。

## Demo 目标

传统 OCR 输出全文文本；本项目展示 Agentic OCR 如何把全文文本变成可信结构化结果：

```text
Read -> Extract -> Validate -> Repair -> Explain
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

当前版本内置一段带 OCR 错误的营业执照示例文本，用于演示自动修复能力：

```powershell
python app.py
```

也可以输入 OCR 文本文件：

```powershell
python app.py --text samples/license_ocr_with_errors.txt
```

可视化分享 Demo：

```powershell
python demo_gui.py
```

左侧展示营业执照图片，右侧展示 Agent 运行结果。建议现场先点击“运行文本兜底 Demo”，快速展示 LangChain 工具调用和自动修复；再点击“加载真实图片 OCR 结果”，展示 PaddleOCR-VL 已识别文本如何进入同一套 Agent 工具链。

## Agent 工具链

当前 demo 使用 LangChain Core 的 `StructuredTool` 封装三个工具：

- `extract_business_license_fields`：从 OCR 全文中抽取营业执照字段
- `validate_business_license_fields`：校验统一社会信用代码、日期、出资额/注册资本等字段
- `repair_business_license_fields`：根据校验失败原因修复 O/0、I/1、日期等 OCR 常见错误

这对应分享中的“工具使用（函数调用）”章节：Agent 不直接相信 OCR 文本，而是通过工具调用把识别结果转成可校验、可修复、可解释的结构化 JSON。

## 使用本地 PaddleOCR-VL-1.6

本机已经在 `company_tool` conda 环境中配置好 PaddleOCR-VL-1.6。建议直接使用该环境的 Python：

```powershell
& 'D:\conda_envs\company_tool\python.exe' app.py --text samples/license_ocr_with_errors.txt --out outputs/company_tool_text_test.json
```

CPU 推理营业执照图片：

```powershell
$env:HTTP_PROXY='http://127.0.0.1:7890'
$env:HTTPS_PROXY='http://127.0.0.1:7890'
$env:ALL_PROXY='http://127.0.0.1:7890'
& 'D:\conda_envs\company_tool\python.exe' app.py --image .\Snipaste_2026-06-04_15-12-26.jpg --out outputs/company_tool_image_result.json --ocr-out outputs/paddleocr_vl_company_tool_app
```

当前 Windows CPU 路径使用 PaddleOCR-VL 的 `transformers` 引擎，避免 Paddle 原生动态引擎在本机 CPU 上崩溃。第一次运行会下载模型，CPU 会慢一些，适合提前跑一遍做缓存。

已缓存模型位置：

```text
C:\Users\EDY\.paddlex\official_models\PaddleOCR-VL-1.6
C:\Users\EDY\.paddlex\official_models\PP-DocLayoutV3
C:\Users\EDY\.paddlex\official_models\PP-DocLayoutV3_safetensors
```

## 后续接入真实 OCR

建议将真实图片放入：

```text
samples/license.png
```

然后在 `tools/ocr_tool.py` 中接入 PaddleOCR、PP-OCR 或 VLM OCR。分享重点不是底层 OCR 训练，而是 Agent 如何组织 OCR、字段抽取、规则校验和错误修复。
