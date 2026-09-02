$ErrorActionPreference = 'Stop'
$base = 'https://insightflow-ai.up.railway.app'
$deadline = (Get-Date).AddMinutes(10)

function Get-Json($url) {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 20
    if ($r.StatusCode -ne 200) { throw "HTTP $($r.StatusCode): $url" }
    return ($r.Content | ConvertFrom-Json)
}

function Get-Text($url) {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 20
    if ($r.StatusCode -ne 200) { throw "HTTP $($r.StatusCode): $url" }
    return $r.Content
}

function Test-LiveVersion {
    try {
        $health = Get-Json "$base/api/health"
        $config = Get-Json "$base/api/config"
        $home = Get-Text "$base/"
        $case = Get-Text "$base/case-study.html"
        $x6 = Get-Text "$base/case-insta360-x6.html"

        $requiredHome = @(
            'evidence-backed',
            'Executive Snapshot',
            'Trend Radar',
            'Consumer Voice',
            'Competitive Benchmark',
            'Market Comparison',
            'Opportunity Board',
            'Insta360 X6'
        )
        foreach ($needle in $requiredHome) {
            if ($home -notmatch [regex]::Escape($needle)) { return $false }
        }
        if ($case -notmatch 'Evidence') { return $false }
        if ($x6 -notmatch 'Insta360 X6') { return $false }
        if ($health.version -ne '1.5.0') { return $false }
        if (-not $health.portfolio_demo) { return $false }
        if (-not $config.public_deployment) { return $false }
        if ($config.serpapi -or $config.llm) { return $false }
        if ($config.allow_public_live_research) { return $false }

        # Load the saved recruiter snapshot. This consumes no external API quota.
        $demoReq = Invoke-WebRequest -UseBasicParsing -Method POST -Uri "$base/api/demo/load" -ContentType 'application/json' -Body '{}' -TimeoutSec 25
        if ($demoReq.StatusCode -ne 200) { return $false }
        $demo = $demoReq.Content | ConvertFrom-Json
        $rid = if ($demo.current_id) { $demo.current_id } elseif ($demo.id) { $demo.id } else { $null }
        if (-not $rid) { return $false }

        $summary = Get-Json "$base/api/research/$rid/summary"
        if ($summary.review_count -lt 18) { return $false }
        if ($summary.product_count -lt 8) { return $false }
        if (-not $summary.historical_delta) { return $false }
        if ($summary.market_comparison.available) { return $false }

        return $true
    } catch {
        return $false
    }
}

Write-Host "Checking InsightFlow live recruiter website..."
while ((Get-Date) -lt $deadline) {
    if (Test-LiveVersion) {
        Write-Host "PASS: v1.5 recruiter website is live and all critical surfaces passed verification."
        Write-Host "Landing:     $base/"
        Write-Host "Flagship:    $base/?demo=1"
        Write-Host "Case study:  $base/case-study.html"
        Write-Host "Insta360 X6: $base/case-insta360-x6.html"
        exit 0
    }
    Write-Host "Railway is not serving the complete v1.5 build yet. Retrying in 15 seconds..."
    Start-Sleep -Seconds 15
}
Write-Host "FAIL: verification timed out before the complete v1.5 build was visible."
exit 1
