$ErrorActionPreference = "Stop"

function Rgb([int]$r, [int]$g, [int]$b) {
    return $r + ($g * 256) + ($b * 65536)
}

function Find-Ppt([string]$pattern) {
    $file = Get-ChildItem "D:\OCR_Research\company_share" -Filter "*.pptx" |
        Where-Object { -not $_.Name.StartsWith("~$") -and $_.Name -like $pattern } |
        Select-Object -First 1
    if (-not $file) { throw "找不到模板：$pattern" }
    return $file.FullName
}

function Add-Text($slide, [string]$text, [double]$x, [double]$y, [double]$w, [double]$h, [double]$size = 16, [bool]$bold = $false, [int]$color = 0, [int]$align = 1) {
    $shape = $slide.Shapes.AddTextbox(1, $x, $y, $w, $h)
    $shape.TextFrame2.WordWrap = -1
    $shape.TextFrame2.MarginLeft = 2
    $shape.TextFrame2.MarginRight = 2
    $shape.TextFrame2.MarginTop = 1
    $shape.TextFrame2.MarginBottom = 1
    $range = $shape.TextFrame2.TextRange
    $range.Text = $text
    $range.Font.Name = "Microsoft YaHei"
    $range.Font.NameFarEast = "Microsoft YaHei"
    $range.Font.Size = $size
    if ($bold) { $range.Font.Bold = -1 } else { $range.Font.Bold = 0 }
    $range.Font.Fill.ForeColor.RGB = $color
    $range.ParagraphFormat.Alignment = $align
    return $shape
}

function Add-Card($slide, [double]$x, [double]$y, [double]$w, [double]$h, [int]$fill, [int]$line) {
    $shape = $slide.Shapes.AddShape(5, $x, $y, $w, $h)
    $shape.Fill.Visible = -1
    $shape.Fill.ForeColor.RGB = $fill
    $shape.Line.Visible = -1
    $shape.Line.ForeColor.RGB = $line
    $shape.Line.Weight = 0.8
    return $shape
}

function Add-Title($slide, [string]$title, [string]$subtitle) {
    Add-Text $slide $title 78 42 780 42 25 $true $ink 1 | Out-Null
    if ($subtitle) {
        Add-Text $slide $subtitle 80 84 780 24 10.8 $false $muted 1 | Out-Null
    }
}

function Add-Footer($slide, [int]$page) {
    Add-Text $slide "上海致宇信息技术有限公司" 760 515 145 12 6.8 $false $muted 3 | Out-Null
    Add-Text $slide "用技术简化知识工作" 78 515 110 12 6.8 $false $muted 1 | Out-Null
    Add-Text $slide ("{0:D2}" -f $page) 918 515 28 12 6.8 $false $muted 3 | Out-Null
}

function Add-Section($slide, [string]$num, [string]$title, [string]$subtitle) {
    Add-Text $slide $num 420 160 70 30 22 $true $red 2 | Out-Null
    Add-Text $slide $title 180 235 600 50 30 $true $ink 2 | Out-Null
    Add-Text $slide $subtitle 225 292 510 24 12.5 $false $muted 2 | Out-Null
}

function Add-GridFlow($slide, [array]$items, [double]$x, [double]$y, [double]$w, [double]$h, [int]$cols = 3) {
    $gapX = 14
    $gapY = 16
    $rows = [Math]::Ceiling($items.Count / $cols)
    $boxW = ($w - $gapX * ($cols - 1)) / $cols
    $boxH = ($h - $gapY * ($rows - 1)) / $rows
    for ($i = 0; $i -lt $items.Count; $i++) {
        $row = [Math]::Floor($i / $cols)
        $col = $i % $cols
        $bx = $x + $col * ($boxW + $gapX)
        $by = $y + $row * ($boxH + $gapY)
        Add-Card $slide $bx $by $boxW $boxH $light $line | Out-Null
        Add-Text $slide ([string]($i + 1)) ($bx + 8) ($by + 10) 18 12 7.8 $true $red 1 | Out-Null
        Add-Text $slide $items[$i][0] ($bx + 34) ($by + 9) ($boxW - 44) 18 10.8 $true $ink 1 | Out-Null
        Add-Text $slide $items[$i][1] ($bx + 14) ($by + 38) ($boxW - 28) ($boxH - 45) 8.5 $false $muted 2 | Out-Null
    }
}

$template = Find-Ppt "*AgenticADE*20260604.pptx"
$output = "D:\OCR_Research\company_share\营业执照AgentOCR技术分享_套模板_v1.pptx"
$preview = "D:\OCR_Research\company_share\ppt_preview_template_v1"
$image = "D:\OCR_Research\agent\data\188.jpg"

$ink = Rgb 45 50 59
$muted = Rgb 98 108 120
$light = Rgb 244 248 251
$line = Rgb 214 225 234
$blue = Rgb 15 94 142
$red = Rgb 190 57 42
$green = Rgb 69 176 94
$gold = Rgb 173 128 45
$white = Rgb 255 255 255

Copy-Item $template $output -Force

$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open($output, $false, $false, $false)

while ($pres.Slides.Count -gt 18) {
    $pres.Slides.Item($pres.Slides.Count).Delete()
}

for ($i = 1; $i -le $pres.Slides.Count; $i++) {
    $slide = $pres.Slides.Item($i)
    for ($j = $slide.Shapes.Count; $j -ge 1; $j--) {
        $slide.Shapes.Item($j).Delete()
    }
}

# 1 封面
$s = $pres.Slides.Item(1)
Add-Text $s "营业执照 Agent OCR 实践" 165 140 640 48 32 $true $ink 2 | Out-Null
Add-Text $s "从 PaddleOCR-VL 识别到可信字段 JSON" 210 202 550 32 20 $true $red 2 | Out-Null
Add-Text $s "工具调用 / LangChain / 大模型语义后处理 / Skill 沉淀" 245 255 470 22 12.5 $false $muted 2 | Out-Null
Add-Text $s "分享人：李岗威`n时间：2026-06-10" 680 405 160 44 11.5 $false $ink 1 | Out-Null
Add-Footer $s 1

# 2 目录
$s = $pres.Slides.Item(2)
Add-Text $s "目录" 80 70 120 34 28 $true $ink 1 | Out-Null
Add-Text $s "CONTENTS" 82 105 110 16 9.5 $false $gold 1 | Out-Null
$contents = @(
    @("01", "营业执照常识：制度、版面与字段变化", "为什么它适合作为 Agent OCR 的业务对象"),
    @("02", "OCR 难点：从看见文字到可信字段", "长文本、地址、字段错配和语义型错误"),
    @("03", "理论主线：工具使用与 LangChain", "用函数调用把 OCR、校验、修复组织成流程"),
    @("04", "Demo 实践：从图片到可信 JSON", "PaddleOCR-VL-1.6 + 大模型语义后处理"),
    @("05", "沉淀与复盘：可复用流程和 Skill", "环境、代理、模型下载、默认参数和故障恢复")
)
for ($i = 0; $i -lt $contents.Count; $i++) {
    $y = 145 + $i * 66
    Add-Text $s $contents[$i][0] 95 $y 36 24 16 $true $red 1 | Out-Null
    Add-Text $s $contents[$i][1] 145 ($y - 2) 520 24 15.5 $true $ink 1 | Out-Null
    Add-Text $s $contents[$i][2] 146 ($y + 25) 560 18 9.8 $false $muted 1 | Out-Null
}
Add-Footer $s 2

# 3 章节
$s = $pres.Slides.Item(3)
Add-Section $s "01" "营业执照常识" "先理解证照制度和字段变化，再谈识别难点"
Add-Footer $s 3

# 4 制度变化
$s = $pres.Slides.Item(4)
Add-Title $s "营业执照的发展：从「证件图片」到「企业身份入口」 " "营业执照承载主体资格、经营边界和监管入口，因此识别结果天然需要可信。"
$timeline = @(
    @("传统注册号", "各地工商登记规则不统一，证照字段和编号规则差异较大。"),
    @("三证合一 / 一照一码", "统一社会信用代码成为企业身份主键。"),
    @("新版横版执照", "版面更稳定，二维码、公示系统入口和字段布局更标准。"),
    @("字段持续调整", "法定代表人、经营者、出资额、经营场所等随主体类型变化。")
)
for ($i = 0; $i -lt $timeline.Count; $i++) {
    $x = 92 + $i * 190
    Add-Card $s $x 165 160 162 $light $line | Out-Null
    Add-Text $s ("0" + ($i + 1)) ($x + 10) 178 28 14 9.5 $true $red 1 | Out-Null
    Add-Text $s $timeline[$i][0] ($x + 12) 215 136 20 13.5 $true $ink 2 | Out-Null
    Add-Text $s $timeline[$i][1] ($x + 16) 252 128 45 9.5 $false $muted 2 | Out-Null
}
Add-Text $s "分享视角：营业执照不是「随便 OCR 一下」的图片，而是有制度约束、字段语义和校验规则的业务对象。" 120 400 730 30 17 $true $red 2 | Out-Null
Add-Footer $s 4

# 5 字段变化
$s = $pres.Slides.Item(5)
Add-Title $s "版面和字段会变：同一位置不一定代表同一业务含义" "营业执照识别难点不止是字准，还包括主体类型驱动的字段解释。"
$headers = @("主体类型", "负责人字段", "资本字段", "地址字段", "经营边界")
$rows = @(
    @("公司", "法定代表人", "注册资本", "住所", "经营范围"),
    @("合伙企业", "执行事务合伙人", "出资额", "主要经营场所", "经营范围"),
    @("个体工商户", "经营者", "资金数额/无", "经营场所", "经营范围"),
    @("分支机构", "负责人", "无注册资本", "营业场所", "经营范围")
)
$xs = @(86, 206, 376, 496, 676)
$ws = @(120, 170, 120, 180, 170)
for ($c = 0; $c -lt $headers.Count; $c++) {
    Add-Card $s $xs[$c] 150 $ws[$c] 30 $blue $blue | Out-Null
    Add-Text $s $headers[$c] ($xs[$c] + 4) 158 ($ws[$c] - 8) 12 8.8 $true $white 2 | Out-Null
}
for ($r = 0; $r -lt $rows.Count; $r++) {
    for ($c = 0; $c -lt $headers.Count; $c++) {
        $y = 180 + $r * 42
        Add-Card $s $xs[$c] $y $ws[$c] 42 $light $line | Out-Null
        Add-Text $s $rows[$r][$c] ($xs[$c] + 4) ($y + 14) ($ws[$c] - 8) 12 8.8 $false $ink 2 | Out-Null
    }
}
Add-Text $s "这也是为什么 demo 不能只做普通 OCR：同一张图中可能有正文、说明、二维码旁注、印章和脚注。Agent 的价值在于把字段抽取、规则校验、上下文修复、输出解释拆成可观测工具链。" 95 395 760 40 13.8 $false $ink 1 | Out-Null
Add-Footer $s 5

# 6 章节
$s = $pres.Slides.Item(6)
Add-Section $s "02" "OCR 难点" "营业执照真正难的，是把识别结果变成可信字段"
Add-Footer $s 6

# 7 难点
$s = $pres.Slides.Item(7)
Add-Title $s "从图片到字段，中间有四类典型错误" "这些错误正好可以作为 Agent OCR 的实战样本。"
$cards = @(
    @("版面噪声", "国徽、印章、二维码、边框、水印会干扰版面块定位。", $green),
    @("字段错配", "把旧执照或说明文字中的内容误认为目标字段。", $red),
    @("长文本截断", "经营范围很长，换行和括号会影响完整性。", $blue),
    @("语义型错字", "如「临颍/临颖」「造价/浩价」「记账/记帐」，单靠格式校验不够。", $gold)
)
for ($i = 0; $i -lt $cards.Count; $i++) {
    $x = 95 + ($i % 2) * 380
    $y = 160 + [Math]::Floor($i / 2) * 115
    Add-Card $s $x $y 335 82 $light $line | Out-Null
    Add-Text $s $cards[$i][0] ($x + 15) ($y + 14) 115 18 12.5 $true $cards[$i][2] 1 | Out-Null
    Add-Text $s $cards[$i][1] ($x + 15) ($y + 43) 300 24 11.5 $false $ink 1 | Out-Null
}
Add-Text $s "结论：OCR 模型负责「看见」，但业务系统还需要「理解、校验、修复、解释」。" 140 425 700 26 18 $true $red 2 | Out-Null
Add-Footer $s 7

# 8 章节
$s = $pres.Slides.Item(8)
Add-Section $s "03" "工具使用与 LangChain" "把知识点落到 demo 的架构里"
Add-Footer $s 8

# 9 工具调用
$s = $pres.Slides.Item(9)
Add-Title $s "工具使用：让模型调用外部能力，而不是只生成文本" "对应 PDF 中《工具使用（函数调用）》章节：定义工具、调用工具、观察结果、决定下一步。"
Add-GridFlow $s @(
    @("工具定义", "OCR、字段抽取、校验、规则修复、语义修复"),
    @("调用决策", "根据当前任务状态选择下一步工具"),
    @("执行工具", "本地模型、Python 函数或远程大模型"),
    @("观察结果", "文本、JSON、校验失败原因、耗时"),
    @("继续处理", "再次校验、修复或输出报告")
) 95 160 760 150 5
Add-Card $s 120 365 720 74 $white $line | Out-Null
Add-Text $s "映射到本次 demo" 145 382 125 16 12 $true $blue 1 | Out-Null
Add-Text $s "LangChain StructuredTool 把每个动作封装成工具；Agent 记录 tool_trace，最后输出字段 JSON、修复动作和运行摘要。" 270 382 530 26 13.2 $false $ink 1 | Out-Null
Add-Footer $s 9

# 10 LangChain 架构
$s = $pres.Slides.Item(10)
Add-Title $s "LangChain 在 demo 中承担「工具编排层」" "它不是为了炫框架，而是让每个步骤可替换、可追踪、可复用。"
Add-GridFlow $s @(
    @("输入工具", "读取图片或 OCR 文本"),
    @("OCR 工具", "PaddleOCR-VL-1.6"),
    @("抽取工具", "中文字段结构化"),
    @("校验工具", "信用代码 / 日期 / 金额"),
    @("修复工具", "规则修复 + LLM 语义修复"),
    @("输出工具", "JSON + 摘要 + 路径")
) 95 160 760 175 3
Add-Text $s "设计原则：可确定的错误先用规则修；需要上下文和语义的错误再交给大模型。这样能避免把所有问题都丢给 LLM，也方便后续替换 OCR 模型或大模型供应商。" 110 405 740 42 14.5 $false $ink 1 | Out-Null
Add-Footer $s 10

# 11 章节
$s = $pres.Slides.Item(11)
Add-Section $s "04" "Demo 实践" "从营业执照图片到可信字段 JSON"
Add-Footer $s 11

# 12 Demo 流程
$s = $pres.Slides.Item(12)
Add-Title $s "Demo 流程：图片进入，可信 JSON 出来" "当前默认参数已经指向样例营业执照图片，运行 app.py 即可走完整链路。"
if (Test-Path $image) {
    $s.Shapes.AddPicture($image, $false, $true, 80, 135, 340, 240) | Out-Null
}
Add-GridFlow $s @(
    @("图片输入", "data/188.jpg"),
    @("OCR", "PaddleOCR-VL-1.6"),
    @("字段抽取", "中文字段"),
    @("校验", "格式和规则"),
    @("LLM 修复", "语义后处理"),
    @("结果保存", "outputs/*.json")
) 460 148 360 166 3
Add-Text $s "演示命令" 470 385 80 16 11.5 $true $blue 1 | Out-Null
Add-Card $s 460 412 360 46 $light $line | Out-Null
Add-Text $s "python app.py" 485 428 315 16 14 $true $ink 1 | Out-Null
Add-Footer $s 12

# 13 运行摘要
$s = $pres.Slides.Item(13)
Add-Title $s "这次运行确实经过了大模型后处理" "摘要中能看到 OCR 模型、LLM 模型、耗时和结果保存路径。"
$metrics = @(
    @("OCR 模型", "PaddleOCR-VL-1.6", $blue),
    @("大模型", "claude-sonnet-4-6", $red),
    @("大模型耗时", "14.256 秒", $green),
    @("自动修复字段", "7 个", $gold)
)
for ($i = 0; $i -lt $metrics.Count; $i++) {
    $x = 95 + $i * 185
    Add-Card $s $x 155 160 65 $light $line | Out-Null
    Add-Text $s $metrics[$i][1] ($x + 10) 168 140 18 13 $true $metrics[$i][2] 2 | Out-Null
    Add-Text $s $metrics[$i][0] ($x + 10) 195 140 12 8.5 $false $muted 2 | Out-Null
}
Add-Card $s 95 280 760 90 $light $line | Out-Null
Add-Text $s "输出路径" 120 300 70 16 11.5 $true $blue 1 | Out-Null
Add-Text $s "D:\OCR_Research\agent\outputs\license_image_agent_result.json" 205 300 600 16 12.5 $true $ink 1 | Out-Null
Add-Text $s "完整图片链路在 CPU 上耗时较长，主要时间花在本地 PaddleOCR-VL 推理；LLM 后处理只占十几秒。" 120 332 650 18 11 $false $muted 1 | Out-Null
Add-Footer $s 13

# 14 字段结果
$s = $pres.Slides.Item(14)
Add-Title $s "最终输出字段：用中文字段名，方便业务同学直接理解" "字段不用英文包装，demo 直接输出营业执照语义字段。"
$fieldRows = @(
    @("统一社会信用代码", "91110108306767909G"),
    @("名称", "北京索伯尼国际科技有限公司"),
    @("类型", "有限责任公司（自然人独资）"),
    @("法定代表人", "刘福喜"),
    @("注册资本", "2000万元"),
    @("成立日期", "2014年08月25日"),
    @("营业期限", "2014年08月25日至2034年08月24日"),
    @("住所", "北京市海淀区中关村大街49号9号楼B座四层405室"),
    @("核准日期", "2019年11月04日")
)
for ($i = 0; $i -lt $fieldRows.Count; $i++) {
    $y = 135 + $i * 30
    Add-Card $s 95 $y 160 28 $light $line | Out-Null
    Add-Card $s 255 $y 585 28 $white $line | Out-Null
    Add-Text $s $fieldRows[$i][0] 105 ($y + 8) 140 10 8.3 $true $blue 2 | Out-Null
    Add-Text $s $fieldRows[$i][1] 270 ($y + 8) 550 10 8.3 $false $ink 1 | Out-Null
}
Add-Text $s "经营范围字段较长，在 JSON 中完整保留；PPT 中只展示关键短字段。" 100 420 670 18 11 $false $muted 1 | Out-Null
Add-Footer $s 14

# 15 修复动作
$s = $pres.Slides.Item(15)
Add-Title $s "大模型后处理负责「语义修复」，但必须保留证据链" "本次图片识别中，LLM 根据上下文修复了 7 个字段。"
$repairs = @(
    @("统一社会信用代码", "92440300MA5FPG0XXH", "91110108306767909G"),
    @("类型", "个体工商户", "有限责任公司（自然人独资）"),
    @("法定代表人", "薛丁川", "刘福喜"),
    @("成立日期", "2019年07月12日", "2014年08月25日"),
    @("住所", "深圳市宝安区...佛商大厦027", "北京市海淀区中关村大街...405室")
)
$headers = @("字段", "修复前", "修复后")
$xs = @(95, 260, 530)
$ws = @(165, 270, 310)
for ($c = 0; $c -lt 3; $c++) {
    Add-Card $s $xs[$c] 145 $ws[$c] 30 $blue $blue | Out-Null
    Add-Text $s $headers[$c] ($xs[$c] + 4) 153 ($ws[$c] - 8) 12 8.8 $true $white 2 | Out-Null
}
for ($r = 0; $r -lt $repairs.Count; $r++) {
    $y = 175 + $r * 42
    for ($c = 0; $c -lt 3; $c++) {
        Add-Card $s $xs[$c] $y $ws[$c] 42 $light $line | Out-Null
        Add-Text $s $repairs[$r][$c] ($xs[$c] + 5) ($y + 14) ($ws[$c] - 10) 12 8.3 $false $ink 2 | Out-Null
    }
}
Add-Text $s "注意：大模型不能替代权威库。地址、省市区、主体名称等字段，后续最好接入行政区划库和企业信用公示数据做二次校验。" 110 420 730 26 13.2 $true $red 2 | Out-Null
Add-Footer $s 15

# 16 模型边界
$s = $pres.Slides.Item(16)
Add-Title $s "PaddleOCR-VL 是视觉文档理解模型，大模型承担语义后处理" "这页专门回答分享时最容易被问到的边界问题。"
$boundary = @(
    @("PaddleOCR-VL-1.6", "多模态文档解析/视觉 OCR 模型，擅长版面、文本、表格和图片区域解析。它可以理解文档结构，但不是通用对话大模型。", $blue),
    @("LLM 后处理", "利用上下文、字段语义和常识修复 OCR 错字、字段错配、经营范围截断等问题。", $red),
    @("规则与权威库", "信用代码、日期、金额可规则校验；省市区地址建议接入行政区划库，避免只靠大模型猜。", $green)
)
for ($i = 0; $i -lt $boundary.Count; $i++) {
    $y = 150 + $i * 82
    Add-Card $s 95 $y 760 58 $light $line | Out-Null
    Add-Text $s $boundary[$i][0] 120 ($y + 18) 150 16 11.2 $true $boundary[$i][2] 1 | Out-Null
    Add-Text $s $boundary[$i][1] 280 ($y + 16) 530 22 11.3 $false $ink 1 | Out-Null
}
Add-Text $s "我的判断：让 OCR/VL 负责感知，让规则负责确定性，让 LLM 负责语义候选，再用业务库兜底。" 120 420 720 26 17 $true $red 2 | Out-Null
Add-Footer $s 16

# 17 章节
$s = $pres.Slides.Item(17)
Add-Section $s "05" "沉淀与复盘" "把一次 demo 变成可复用的方法"
Add-Footer $s 17

# 18 总结
$s = $pres.Slides.Item(18)
Add-Title $s "沉淀下来的是一套 Agent OCR 方法，而不只是一段脚本" "可复用的东西，才是这次分享真正有价值的部分。"
$takeaways = @(
    @("默认参数", "app.py 默认走图片链路，输出路径固定，现场不需要临时拼命输参数。", $blue),
    @("运行摘要", "只打印模型、耗时、是否调用 LLM、保存位置，避免现场被大段 JSON 淹没。", $red),
    @("环境 Skill", "记录 conda、代理、SSL_CERT_FILE、模型缓存和常见问题恢复。", $green),
    @("业务 Skill", "记录营业执照字段、别名、校验规则、修复策略和讲解口径。", $gold)
)
for ($i = 0; $i -lt $takeaways.Count; $i++) {
    $x = 95 + ($i % 2) * 380
    $y = 165 + [Math]::Floor($i / 2) * 98
    Add-Card $s $x $y 335 68 $light $line | Out-Null
    Add-Text $s $takeaways[$i][0] ($x + 16) ($y + 16) 95 16 11.8 $true $takeaways[$i][2] 1 | Out-Null
    Add-Text $s $takeaways[$i][1] ($x + 112) ($y + 14) 200 28 10.4 $false $ink 1 | Out-Null
}
Add-Text $s "Q&A" 420 420 120 30 24 $true $ink 2 | Out-Null
Add-Footer $s 18

$pres.Save()

if (Test-Path $preview) {
    Remove-Item $preview -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $preview | Out-Null
$pres.Export($preview, "PNG", 1280, 720)

$slideCount = $pres.Slides.Count
$pres.Close()
$pp.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp) | Out-Null

Write-Output "output=$output"
Write-Output "slides=$slideCount"
Write-Output "preview=$preview"

