# GitHub 部署脚本
# 使用方法：在 PowerShell 中运行 .\deploy_to_github.ps1

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PDF 文档问答助手 - GitHub 部署脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Git 是否安装
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git 未安装，请先安装 Git: https://git-scm.com/" -ForegroundColor Red
    exit 1
}

# 检查 Git 用户配置
$gitUser = git config --global user.name
$gitEmail = git config --global user.email

if (-not $gitUser -or -not $gitEmail) {
    Write-Host "⚠️  请先配置 Git 用户信息：" -ForegroundColor Yellow
    Write-Host "   git config --global user.name `"Your Name`"" -ForegroundColor Yellow
    Write-Host "   git config --global user.email `"your.email@example.com`"" -ForegroundColor Yellow
    Write-Host ""
    $configure = Read-Host "是否现在配置？ (y/n)"
    if ($configure -eq 'y') {
        $name = Read-Host "请输入你的名字"
        $email = Read-Host "请输入你的邮箱"
        git config --global user.name $name
        git config --global user.email $email
    }
}

# 获取仓库信息
$repoUrl = Read-Host "请输入你的 GitHub 仓库 URL（例如 https://github.com/username/pdf-qa-app.git）"
if (-not $repoUrl) {
    Write-Host "❌ 仓库 URL 不能为空"
    exit 1
}

# 切换到项目目录
$projectDir = $PSScriptRoot
Set-Location $projectDir
Write-Host "📁 当前目录: $projectDir" -ForegroundColor Green

# 初始化 Git（如果还没有）
if (-not (Test-Path ".git")) {
    Write-Host "`n🔧 初始化 Git 仓库..." -ForegroundColor Cyan
    git init
    git branch -M main
}

# 添加远程仓库
$remoteExists = git remote get-url origin 2>$null
if (-not $remoteExists) {
    Write-Host "`n🔗 添加远程仓库..." -ForegroundColor Cyan
    git remote add origin $repoUrl
} else {
    Write-Host "`n🔗 远程仓库已存在: $remoteExists" -ForegroundColor Yellow
    Write-Host "   更新为新的 URL..." -ForegroundColor Yellow
    git remote set-url origin $repoUrl
}

# 添加文件
Write-Host "`n📦 添加文件到 Git..." -ForegroundColor Cyan
git add .

# 检查是否有变更
$status = git status --porcelain
if (-not $status) {
    Write-Host "✅ 没有新的变更需要提交" -ForegroundColor Yellow
} else {
    # 提交
    Write-Host "`n💾 提交变更..." -ForegroundColor Cyan
    $commitMsg = Read-Host "请输入提交信息（直接回车使用默认）"
    if (-not $commitMsg) {
        $commitMsg = "Update: deploy to GitHub (Groq support)"
    }
    git commit -m $commitMsg
}

# 推送
Write-Host "`n🚀 推送到 GitHub..." -ForegroundColor Cyan
Write-Host "   如果是首次推送，可能需要输入 GitHub 凭据" -ForegroundColor Yellow

try {
    git push -u origin main
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "  ✅ 部署成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📌 下一步：访问 Streamlit Cloud 部署应用" -ForegroundColor Cyan
    Write-Host "   1. 打开 https://share.streamlit.io/" -ForegroundColor White
    Write-Host "   2. 点击 'New app'" -ForegroundColor White
    Write-Host "   3. 选择你的仓库: $repoUrl" -ForegroundColor White
    Write-Host "   4. Main file path: app.py" -ForegroundColor White
    Write-Host "   5. 配置 Secrets (高级设置):" -ForegroundColor White
    Write-Host "      LLM_MODE = `"groq`"" -ForegroundColor Yellow
    Write-Host "      GROQ_API_KEY = `"gsk_...`"" -ForegroundColor White
    Write-Host "      GROQ_MODEL = `"llama-3.1-8b-instant`"" -ForegroundColor White
    Write-Host "   6. 点击 Deploy" -ForegroundColor White
    Write-Host ""
    Write-Host "📚 更多说明见 README.md 和 GROQ_SETUP.md" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host "`n❌ 推送失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因：" -ForegroundColor Yellow
    Write-Host "1. 仓库 URL 不正确" -ForegroundColor White
    Write-Host "2. 没有推送权限（检查 GitHub 凭据）" -ForegroundColor White
    Write-Host "3. 仓库不存在（请先在 GitHub 创建仓库）" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 提示：可以先在 GitHub 网站上创建空仓库，然后重试此脚本" -ForegroundColor Yellow
}