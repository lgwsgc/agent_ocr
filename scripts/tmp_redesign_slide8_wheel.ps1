$ErrorActionPreference = "Stop"
function Rgb([int]$r,[int]$g,[int]$b){ return $r + ($g*256) + ($b*65536) }
$ink=Rgb 45 50 59; $muted=Rgb 98 108 120; $light=Rgb 244 248 251; $line=Rgb 214 225 234; $blue=Rgb 15 94 142; $red=Rgb 190 57 42; $green=Rgb 69 176 94; $gold=Rgb 173 128 45; $white=Rgb 255 255 255
function AddText($slide,[string]$text,[double]$x,[double]$y,[double]$w,[double]$h,[double]$size=14,[bool]$bold=$false,[int]$color=0,[int]$align=1){ $shape=$slide.Shapes.AddTextbox(1,$x,$y,$w,$h); $shape.TextFrame2.WordWrap=-1; $shape.TextFrame2.MarginLeft=2; $shape.TextFrame2.MarginRight=2; $shape.TextFrame2.MarginTop=1; $shape.TextFrame2.MarginBottom=1; $r=$shape.TextFrame2.TextRange; $r.Text=$text; $r.Font.Name='Microsoft YaHei'; $r.Font.NameFarEast='Microsoft YaHei'; $r.Font.Size=$size; if($bold){$r.Font.Bold=-1}else{$r.Font.Bold=0}; $r.Font.Fill.ForeColor.RGB=$color; $r.ParagraphFormat.Alignment=$align; return $shape }
function AddCard($slide,[double]$x,[double]$y,[double]$w,[double]$h,[int]$fill,[int]$border){ $s=$slide.Shapes.AddShape(5,$x,$y,$w,$h); $s.Fill.Visible=-1; $s.Fill.ForeColor.RGB=$fill; $s.Line.Visible=-1; $s.Line.ForeColor.RGB=$border; $s.Line.Weight=0.9; return $s }
function AddRect($slide,[double]$x,[double]$y,[double]$w,[double]$h,[int]$fill){ $s=$slide.Shapes.AddShape(1,$x,$y,$w,$h); $s.Fill.Visible=-1; $s.Fill.ForeColor.RGB=$fill; $s.Line.Visible=0; return $s }
function AddFooter($slide,[int]$p){ AddText $slide '上海致宇信息技术有限公司' 760 515 145 12 6.8 $false $muted 3|Out-Null; AddText $slide '用技术简化知识工作' 78 515 110 12 6.8 $false $muted 1|Out-Null; AddText $slide ("{0:D2}" -f $p) 918 515 28 12 6.8 $false $muted 3|Out-Null }
function AddSampleBox($slide,[string]$title,[string]$hint,[double]$x,[double]$y,[int]$color){
  AddCard $slide $x $y 245 86 $light $line|Out-Null
  AddRect $slide $x $y 245 7 $color|Out-Null
  AddText $slide $title ($x+14) ($y+17) 120 16 11.5 $true $color 1|Out-Null
  AddText $slide $hint ($x+14) ($y+42) 200 24 8.8 $false $ink 1|Out-Null
  AddText $slide '放入对应错误样本截图' ($x+14) ($y+66) 190 12 7.6 $false $muted 1|Out-Null
}
$ppt='D:\OCR_Research\company_share\营业执照AgentOCR技术分享_套模板_v2.pptx'
$preview='D:\OCR_Research\company_share\ppt_preview_template_v2'
$wheel='D:\OCR_Research\company_share\ppt_preview_template_v2\ocr_error_wheel.png'
$pp=New-Object -ComObject PowerPoint.Application
$pres=$pp.Presentations.Open($ppt,$false,$false,$false)
$s=$pres.Slides.Item(8)
for($j=$s.Shapes.Count;$j -ge 1;$j--){$s.Shapes.Item($j).Delete()}
AddText $s 'OCR 难点：用「四象限样本图」讲，会比纯文字更直观' 78 42 790 42 24 $true $ink 1|Out-Null
AddText $s '中间四等分对应四类难点，四周放真实错误样本；后续你只需要替换样本截图。' 80 84 790 24 10.8 $false $muted 1|Out-Null
if(Test-Path $wheel){ $s.Shapes.AddPicture($wheel,$false,$true,365,190,220,220)|Out-Null }
AddSampleBox $s '字段错配' '把说明文字、旧版字段或其他区域内容误抽为目标字段。' 95 145 $red
AddSampleBox $s '语义错字' '字形相近但业务含义变了，如临颍/临颖、造价/浩价。' 620 145 $gold
AddSampleBox $s '长文本截断' '经营范围跨行、括号、许可项目导致内容被截断或粘连。' 95 355 $blue
AddSampleBox $s '版面噪声' '印章、二维码、国徽、水印、倾斜拍摄干扰版面定位。' 620 355 $green
$line1=$s.Shapes.AddLine(340,210,370,240); $line1.Line.ForeColor.RGB=$red; $line1.Line.Weight=1.2
$line2=$s.Shapes.AddLine(610,210,580,240); $line2.Line.ForeColor.RGB=$gold; $line2.Line.Weight=1.2
$line3=$s.Shapes.AddLine(340,400,370,365); $line3.Line.ForeColor.RGB=$blue; $line3.Line.Weight=1.2
$line4=$s.Shapes.AddLine(610,400,580,365); $line4.Line.ForeColor.RGB=$green; $line4.Line.Weight=1.2
AddText $s '讲法：每一类错误先用真实样本引出，再说明为什么需要 Agent 的抽取、校验、修复和复核流程。' 140 470 680 22 12.8 $true $red 2|Out-Null
AddFooter $s 8
$pres.Save()
if(Test-Path $preview){Remove-Item $preview -Recurse -Force}
New-Item -ItemType Directory -Force -Path $preview|Out-Null
$pres.Export($preview,'PNG',1280,720)
$pres.Close(); $pp.Quit(); [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres)|Out-Null; [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp)|Out-Null
Write-Output 'redesigned slide 8 wheel layout'

