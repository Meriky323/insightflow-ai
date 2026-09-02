$ErrorActionPreference = 'Stop'
$base = 'https://insightflow-ai.up.railway.app'
$deadline = (Get-Date).AddMinutes(20)

function Get-Json($url) {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 25
    if ($r.StatusCode -ne 200) { throw "HTTP $($r.StatusCode): $url" }
    return ($r.Content | ConvertFrom-Json)
}
function Get-Text($url) {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 25
    if ($r.StatusCode -ne 200) { throw "HTTP $($r.StatusCode): $url" }
    return $r.Content
}
function Test-LiveVersion {
    $issues = New-Object System.Collections.Generic.List[string]
    try { $health = Get-Json "$base/api/health" } catch { $issues.Add("health request failed: $($_.Exception.Message)"); return $issues }
    try { $config = Get-Json "$base/api/config" } catch { $issues.Add("config request failed: $($_.Exception.Message)"); return $issues }
    try { $home = Get-Text "$base/" } catch { $issues.Add("home request failed: $($_.Exception.Message)"); return $issues }
    try { $case = Get-Text "$base/case-study.html" } catch { $issues.Add("flagship case request failed: $($_.Exception.Message)"); return $issues }
    try { $x6 = Get-Text "$base/case-insta360-x6.html" } catch { $issues.Add("X6 case request failed: $($_.Exception.Message)"); return $issues }

    if ($health.version -ne '1.6.0') { $issues.Add("health.version=$($health.version), expected 1.6.0") }
    if (-not $health.portfolio_demo) { $issues.Add('portfolio_demo flag missing') }
    if (-not $health.bilingual_ui) { $issues.Add('bilingual_ui flag missing') }
    if (-not $config.public_deployment) { $issues.Add('public_deployment is false') }
    if ($config.serpapi -or $config.llm) { $issues.Add('connector status is exposed in public mode') }
    if ($config.allow_public_live_research) { $issues.Add('public live research is enabled') }

    $requiredHome = @('evidence-backed','Trend Radar','Consumer Voice','Competitor Benchmark','Opportunity Board','data-lang-toggle','Insta360 X6')
    foreach ($needle in $requiredHome) { if ($home -notmatch [regex]::Escape($needle)) { $issues.Add("home missing: $needle") } }
    if ($case -notmatch 'localStorage.getItem') { $issues.Add('flagship case language switch missing') }
    if ($x6 -notmatch 'localStorage.getItem') { $issues.Add('X6 case language switch missing') }

    try {
        $demoReq = Invoke-WebRequest -UseBasicParsing -Method POST -Uri "$base/api/demo/load" -ContentType 'application/json' -Body '{}' -TimeoutSec 30
        if ($demoReq.StatusCode -ne 200) { $issues.Add("demo load HTTP $($demoReq.StatusCode)") }
        else {
            $demo = $demoReq.Content | ConvertFrom-Json
            $rid = if ($demo.current_id) { $demo.current_id } elseif ($demo.id) { $demo.id } else { $null }
            if (-not $rid) { $issues.Add('demo research id missing') }
            else {
                $summary = Get-Json "$base/api/research/$rid/summary"
                if ($summary.review_count -lt 18) { $issues.Add("review_count=$($summary.review_count), expected >=18") }
                if ($summary.product_count -lt 8) { $issues.Add("product_count=$($summary.product_count), expected >=8") }
                if (-not $summary.historical_delta) { $issues.Add('historical_delta missing') }
                if ($summary.market_comparison.available) { $issues.Add('market guardrail unexpectedly allows comparison') }
                $zhAsk = Invoke-WebRequest -UseBasicParsing -Method POST -Uri "$base/api/research/$rid/ask" -ContentType 'application/json' -Body '{"question":"现在可以比较美国和澳洲的消费者偏好吗？","language":"zh"}' -TimeoutSec 30
                if ($zhAsk.StatusCode -ne 200 -or $zhAsk.Content -notmatch '不支持') { $issues.Add('Chinese Ask InsightFlow check failed') }
                $enAsk = Invoke-WebRequest -UseBasicParsing -Method POST -Uri "$base/api/research/$rid/ask" -ContentType 'application/json' -Body '{"question":"Can US and AU consumer preferences be compared?","language":"en"}' -TimeoutSec 30
                if ($enAsk.StatusCode -ne 200 -or $enAsk.Content -notmatch 'does not support') { $issues.Add('English Ask InsightFlow check failed') }
            }
        }
    } catch { $issues.Add("demo verification failed: $($_.Exception.Message)") }
    return $issues
}

Write-Host "Checking InsightFlow v1.6 live recruiter website..."
$attempt = 0
while ((Get-Date) -lt $deadline) {
    $attempt++
    $issues = Test-LiveVersion
    if ($issues.Count -eq 0) {
        Write-Host ""
        Write-Host "PASS: InsightFlow v1.6 is live and all critical surfaces passed verification." -ForegroundColor Green
        Write-Host "Landing:     $base/"
        Write-Host "Flagship:    $base/?demo=1"
        Write-Host "Case study:  $base/case-study.html"
        Write-Host "Insta360 X6: $base/case-insta360-x6.html"
        exit 0
    }
    Write-Host "Attempt $attempt - Railway is not ready yet:" -ForegroundColor Yellow
    $issues | Select-Object -First 6 | ForEach-Object { Write-Host "  - $_" }
    Write-Host "Retrying in 20 seconds..."
    Start-Sleep -Seconds 20
}
Write-Host ""
Write-Host "FAIL: v1.6 did not pass full verification within 20 minutes." -ForegroundColor Red
Write-Host "The last verification issues are:"
$issues | ForEach-Object { Write-Host "  - $_" }
exit 1
