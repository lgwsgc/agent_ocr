$ErrorActionPreference = "Stop"
function Rgb([int]$r,[int]$g,[int]$b){ return $r + ($g*256) + ($b*65536) }
$ink=Rgb 45 50 59; $muted=Rgb 98 108 120; $light=Rgb 244 248 251; $line=Rgb 214 225 234; $blue=Rgb 15 94 142; $red=Rgb 190 57 42; $green=Rgb 69 176 94; $gold=Rgb 173 128 45; $white=Rgb 255 255 255
function AddText($slide,[string]$text,[double]$x,[double]$y,[double]$w,[double]$h,[double]$size=14,[bool]$bold=$false,[int]$color=0,[int]$align=1){ $shape=$slide.Shapes.AddTextbox(1,$x,$y,$w,$h); $shape.TextFrame2.WordWrap=-1; $shape.TextFrame2.MarginLeft=2; $shape.TextFrame2.MarginRight=2; $shape.TextFrame2.MarginTop=1; $shape.TextFrame2.MarginBottom=1; $r=$shape.TextFrame2.TextRange; $r.Text=$text; $r.Font.Name='Microsoft YaHei'; $r.Font.NameFarEast='Microsoft YaHei'; $r.Font.Size=$size; if($bold){$r.Font.Bold=-1}else{$r.Font.Bold=0}; $r.Font.Fill.ForeColor.RGB=$color; $r.ParagraphFormat.Alignment=$align; return $shape }
function AddCard($slide,[double]$x,[double]$y,[double]$w,[double]$h,[int]$fill,[int]$border){ $s=$slide.Shapes.AddShape(5,$x,$y,$w,$h); $s.Fill.Visible=-1; $s.Fill.ForeColor.RGB=$fill; $s.Line.Visible=-1; $s.Line.ForeColor.RGB=$border; $s.Line.Weight=0.8; return $s }
function AddRect($slide,[double]$x,[double]$y,[double]$w,[double]$h,[int]$fill){ $s=$slide.Shapes.AddShape(1,$x,$y,$w,$h); $s.Fill.Visible=-1; $s.Fill.ForeColor.RGB=$fill; $s.Line.Visible=0; return $s }
function AddFooter($slide,[int]$p){ AddText $slide '上海致宇信息技术有限公司' 760 515 145 12 6.8 $false $muted 3|Out-Null; AddText $slide '用技术简化知识工作' 78 515 110 12 6.8 $false $muted 1|Out-Null; AddText $slide ("{0:D2}" -f $p) 918 515 28 12 6.8 $false $muted 3|Out-Null }
$ppt='D:\OCR_Research\company_share\营业执照AgentOCR技术分享_套模板_v2.pptx'
$preview='D:\OCR_Research\company_share\ppt_preview_template_v2'
$pp=New-Object -ComObject PowerPoint.Application
$pres=$pp.Presentations.Open($ppt,$false,$false,$false)
$s=$pres.Slides.Item(8)
for($j=$s.Shapes.Count;$j -ge 1;$j--){$s.Shapes.Item($j).Delete()}
AddText $s '错误类型可以用「分布 + 样本」来讲，会比纯文字更直观' 78 42 790 42 24 $true $ink 1|Out-Null
AddText $s '左侧是建议的错误类型分布，右侧留给后续替换真实错误截图。' 80 84 790 24 10.8 $false $muted 1|Out-Null
$chartShape=$s.Shapes.AddChart2(251,5,105,150,340,260)
$chart=$chartShape.Chart
$chart.HasTitle=$false
$chart.HasLegend=$false
$chart.ChartData.Activate()
$wb=$chart.ChartData.Workbook
$ws=$wb.Worksheets.Item(1)
$ws.Cells.Item(1,1).Value2='错误类型'; $ws.Cells.Item(1,2).Value2='占比'
$labels=@('字段错配','语义错字','长文本截断','版面噪声')
$vals=@(35,25,20,20)
for($i=0;$i -lt 4;$i++){ $ws.Cells.Item($i+2,1).Value2=$labels[$i]; $ws.Cells.Item($i+2,2).Value2=$vals[$i] }
$chart.SetSourceData($ws.Range('A1:B5'))
$colors=@($red,$gold,$blue,$green)
for($i=1;$i -le 4;$i++){ $chart.FullSeriesCollection(1).Points($i).Format.Fill.ForeColor.RGB=$colors[$i-1]; $chart.FullSeriesCollection(1).Points($i).Format.Line.ForeColor.RGB=$white }
$wb.Close($true)
for($i=0;$i -lt 4;$i++){ AddRect $s 475 (155+$i*42) 14 14 $colors[$i]|Out-Null; AddText $s ($labels[$i]+'  '+$vals[$i]+'%') 500 (151+$i*42) 160 18 11.2 $true $ink 1|Out-Null }
$samples=@(@('字段错配','把执照说明文字中的内容当成目标字段'),@('语义错字','临颍/临颖、造价/浩价、记账/记帐'),@('长文本截断','经营范围换行、括号、许可项目被截断'))
for($i=0;$i -lt 3;$i++){ $y=155+$i*86; AddCard $s 670 $y 210 58 $light $line|Out-Null; AddText $s $samples[$i][0] 686 ($y+10) 80 14 10.3 $true $red 1|Out-Null; AddText $s $samples[$i][1] 686 ($y+31) 165 18 8.4 $false $ink 1|Out-Null }
AddText $s '这些比例先作为讲解框架，等你补充真实错误样本后，可以替换为真实统计。' 110 430 740 22 12.5 $false $muted 2|Out-Null
AddFooter $s 8
$pres.Save()
if(Test-Path $preview){Remove-Item $preview -Recurse -Force}
New-Item -ItemType Directory -Force -Path $preview|Out-Null
$pres.Export($preview,'PNG',1280,720)
$pres.Close(); $pp.Quit(); [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres)|Out-Null; [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp)|Out-Null
Write-Output 'fixed slide 8 chart'
