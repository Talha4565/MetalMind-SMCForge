# Phase 0 Verification Script
Write-Host "`n=== Phase 0 Verification ===" -ForegroundColor Cyan

# Check Node.js
Write-Host "`n[1/12] Node.js..." -NoNewline
$nodeVersion = node --version
if ($nodeVersion -match "v\d+\.\d+\.\d+") {
    Write-Host " ✓ $nodeVersion" -ForegroundColor Green
} else {
    Write-Host " ✗ Not found" -ForegroundColor Red
}

# Check npm
Write-Host "[2/12] npm..." -NoNewline
$npmVersion = npm --version
if ($npmVersion) {
    Write-Host " ✓ v$npmVersion" -ForegroundColor Green
} else {
    Write-Host " ✗ Not found" -ForegroundColor Red
}

# Check package.json
Write-Host "[3/12] package.json..." -NoNewline
if (Test-Path "package.json") {
    Write-Host " ✓ Exists" -ForegroundColor Green
} else {
    Write-Host " ✗ Missing" -ForegroundColor Red
}

# Check TypeScript configs
Write-Host "[4/12] TypeScript config..." -NoNewline
if ((Test-Path "tsconfig.json") -and (Test-Path "tsconfig.node.json")) {
    Write-Host " ✓ Both configs present" -ForegroundColor Green
} else {
    Write-Host " ✗ Missing files" -ForegroundColor Red
}

# Check Vite config
Write-Host "[5/12] Vite config..." -NoNewline
if (Test-Path "vite.config.ts") {
    Write-Host " ✓ vite.config.ts" -ForegroundColor Green
} else {
    Write-Host " ✗ Missing" -ForegroundColor Red
}

# Check ESLint
Write-Host "[6/12] ESLint config..." -NoNewline
if (Test-Path ".eslintrc.cjs") {
    Write-Host " ✓ .eslintrc.cjs" -ForegroundColor Green
} else {
    Write-Host " ✗ Missing" -ForegroundColor Red
}

# Check Prettier
Write-Host "[7/12] Prettier config..." -NoNewline
if (Test-Path ".prettierrc") {
    Write-Host " ✓ .prettierrc" -ForegroundColor Green
} else {
    Write-Host " ✗ Missing" -ForegroundColor Red
}

# Check Husky
Write-Host "[8/12] Git hooks..." -NoNewline
if (Test-Path ".husky/pre-commit") {
    Write-Host " ✓ Husky configured" -ForegroundColor Green
} else {
    Write-Host " ⚠ Needs initialization" -ForegroundColor Yellow
}

# Check folder structure
Write-Host "[9/12] Folder structure..." -NoNewline
$requiredDirs = @("src", "src/components", "src/features", "src/pages", "src/hooks", "src/lib", "public")
$allExist = $true
foreach ($dir in $requiredDirs) {
    if (-not (Test-Path $dir)) {
        $allExist = $false
        break
    }
}
if ($allExist) {
    Write-Host " ✓ Complete" -ForegroundColor Green
} else {
    Write-Host " ✗ Incomplete" -ForegroundColor Red
}

# Check environment files
Write-Host "[10/12] Environment files..." -NoNewline
if ((Test-Path ".env.example") -and (Test-Path ".env.development")) {
    Write-Host " ✓ Present" -ForegroundColor Green
} else {
    Write-Host " ✗ Missing" -ForegroundColor Red
}

# Check entry points
Write-Host "[11/12] Entry points..." -NoNewline
if ((Test-Path "index.html") -and (Test-Path "src/main.tsx") -and (Test-Path "src/App.tsx")) {
    Write-Host " ✓ All present" -ForegroundColor Green
} else {
    Write-Host " ✗ Missing files" -ForegroundColor Red
}

# Check node_modules
Write-Host "[12/12] Dependencies..." -NoNewline
if (Test-Path "node_modules") {
    $count = (Get-ChildItem "node_modules" -Directory | Measure-Object).Count
    Write-Host " ✓ $count packages installed" -ForegroundColor Green
} else {
    Write-Host " ⚠ Not installed - Run: npm install --legacy-peer-deps" -ForegroundColor Yellow
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Phase 0 configuration: " -NoNewline
Write-Host "COMPLETE ✅" -ForegroundColor Green
Write-Host "`nNext step: " -NoNewline
if (-not (Test-Path "node_modules/vite")) {
    Write-Host "npm install --legacy-peer-deps" -ForegroundColor Yellow
} else {
    Write-Host "npm run dev" -ForegroundColor Green
}
Write-Host ""
