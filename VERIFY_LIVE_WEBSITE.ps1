$ErrorActionPreference = 'Stop'
$baseUrl = 'https://insightflow-ai.up.railway.app'
$deadline = (Get-Date).AddMinutes(20)

function Get-JsonValue($url) {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 25
    if ($response.StatusCode -ne 200) { throw "HTTP $($response.StatusCode): $url" }
    return ($response.Content | ConvertFrom-Json)
}
function Get-TextValue($url) {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 25
    if ($response.StatusCode -ne 200) { throw "HTTP $($response.StatusCode): $url" }
    return $response.Content
}
function Test-LiveVersion {
    $issues = New-Object System.Collections.Generic.List[string]
    try { $health = Get-JsonValue "$baseUrl/api/health" } catch { $issues.Add("health request failed: $($_.Exception.Message)"); return $issues }
    try { $config = Get-JsonValue "$baseUrl/api/config" } catch { $issues.Add("config request failed: $($_.Exception.Message)"); return $issues }
    try { $homeHtml = Get-TextValue "$baseUrl/" } catch { $issues.Add("home request failed: $($_.Exception.Message)"); return $issues }
    try { $caseHtml = Get-TextValue "$baseUrl/case-study.html" } catch { $issues.Add("case-study request failed: $($_.Exception.Message)"); return $issues }
    try { $x6Html = Get-TextValue "$baseUrl/case-insta360-x6.html" } catch { $issues.Add("X6 request failed: $($_.Exception.Message)"); return $issues }
    try { $motionJs = Get-TextValue "$baseUrl/motion.js" } catch { $issues.Add("motion.js request failed: $($_.Exception.Message)"); return $issues }

    if ($health.version -ne '2.0.0') { $issues.Add("health.version=$($health.version), expected 2.0.0") }
    if (-not $health.portfolio_demo) { $issues.Add('portfolio_demo flag missing') }
    if (-not $health.bilingual_ui) { $issues.Add('bilingual_ui flag missing') }
    if (-not $health.community_discovery) { $issues.Add('community_discovery flag missing') }
    if (-not $health.evidence_thread) { $issues.Add('evidence_thread flag missing') }
    if (-not $config.public_deployment) { $issues.Add('public_deployment is false') }
    if ($config.serpapi -or $config.llm) { $issues.Add('connector status is exposed in public mode') }
    if ($config.allow_public_live_research) { $issues.Add('public live research is enabled') }

    $needles = @('hero-signal-stage','evidenceDrawer','Trend Radar','Consumer Voice','Competitors','Opportunities','data-lang-toggle','Insta360 X6','Reddit / Forums')
    foreach ($needle in $needles) { if ($homeHtml -notmatch [regex]::Escape($needle)) { $issues.Add("home missing: $needle") } }
    if ($motionJs -notmatch 'magnetic') { $issues.Add('motion system missing') }
    if ($caseHtml -notmatch 'Evidence') { $issues.Add('flagship case surface incomplete') }
    if ($x6Html -notmatch 'Insta360 X6') { $issues.Add('X6 case surface incomplete') }

    try {
        $demoRequest = Invoke-WebRequest -UseBasicParsing -Method POST -Uri "$baseUrl/api/demo/load" -ContentType 'application/json' -Body '{}' -TimeoutSec 30
        $demo = $demoRequest.Content | ConvertFrom-Json
        $researchId = if ($demo.current_id) { $demo.current_id } elseif ($demo.id) { $demo.id } else { $null }
        if (-not $researchId) { $issues.Add('demo research id missing') }
        else {
            $summary = Get-JsonValue "$baseUrl/api/research/$researchId/summary"
            if ($summary.review_count -lt 18) { $issues.Add("review_count=$($summary.review_count), expected >=18") }
            if ($summary.product_count -lt 8) { $issues.Add("product_count=$($summary.product_count), expected >=8") }
            if (-not $summary.historical_delta) { $issues.Add('historical_delta missing') }
            if ($summary.market_comparison.available) { $issues.Add('market guardrail unexpectedly allows comparison') }
            if (-not $summary.research_quality) { $issues.Add('research_quality missing') }
            $reviews = Get-JsonValue "$baseUrl/api/research/$researchId/reviews?limit=40"
            if ($reviews.total -lt 18) { $issues.Add('evidence API incomplete') }
            $enBody = '{"question":"Can US and AU consumer preferences be compared?","language":"en"}'
            $enAsk = Invoke-WebRequest -UseBasicParsing -Method POST -Uri "$baseUrl/api/research/$researchId/ask" -ContentType 'application/json' -Body $enBody -TimeoutSec 30
            if ($enAsk.StatusCode -ne 200 -or $enAsk.Content -notmatch 'does not support') { $issues.Add('English Ask InsightFlow check failed') }
        }
    } catch { $issues.Add("demo verification failed: $($_.Exception.Message)") }
    return $issues
}

Write-Host "Checking InsightFlow 2.0 live recruiter website..."
$attempt = 0
while ((Get-Date) -lt $deadline) {
    $attempt++
    $issues = Test-LiveVersion
    if ($issues.Count -eq 0) {
        Write-Host ""
        Write-Host "PASS: InsightFlow 2.0 is live and all critical surfaces passed verification." -ForegroundColor Green
        Write-Host "Landing:     $baseUrl/"
        Write-Host "Flagship:    $baseUrl/?demo=1"
        Write-Host "Case study:  $baseUrl/case-study.html"
        Write-Host "Insta360 X6: $baseUrl/case-insta360-x6.html"
        exit 0
    }
    Write-Host "Attempt $attempt - live verification is not ready:" -ForegroundColor Yellow
    $issues | Select-Object -First 8 | ForEach-Object { Write-Host "  - $_" }
    Write-Host "Retrying in 20 seconds..."
    Start-Sleep -Seconds 20
}
Write-Host ""
Write-Host "FAIL: InsightFlow 2.0 did not pass full verification within 20 minutes." -ForegroundColor Red
$issues | ForEach-Object { Write-Host "  - $_" }
exit 1
