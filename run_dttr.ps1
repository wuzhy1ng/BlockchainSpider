# DTTR 爬虫快速启动脚本
# 注意 请一定要配置  DTTR 参数配置 [string]$dttPath = "C:\Users\user\Desktop\DynamicTTR-0B66"
# 用法一（使用默认的）: .\run_dttr.ps1 -start 23925773 -end 23925773
# 用法二（自定义参数）：
# scrapy crawl trans.block.evm `
#     -a providers="https://mainnet.chainnodes.org/b23ab29c-345e-44fa-9964-1104b5646941" `
#     -a start_blk=23937589 `
#     -a end_blk=23937589 `
#     -a enable="BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware,BlockchainSpider.middlewares.trans.TokenTransferMiddleware" `
#     -s LOG_LEVEL="INFO" `
#     -s DTT_PATH="C:\Users\user\Desktop\DynamicTTR-0B66" `
#     -s DTT_SOURCE="['0x7a250d5630b4cf539739df2c5dacb4c659f2488d']" `
#     -s DTT_BATCH_SIZE=50 `
#     -s DTT_REVERSE_EDGE=True `
#     -s DTT_ALPHA=0.15 `
#     -s DTT_EPSILON="0.001" `
#     -s DTT_IS_IN_USD=False `
#     -s DTT_IS_REDUCE_SWAP=True `
#     -s DTT_IS_LOG_VALUE=True `
#     -s DTT_RESULT_FILE="C:\Users\user\Desktop\githubspider\BlockchainSpider\results\DTTR_result.csv"
# 用法三（修改下述参数）
#--------------------也可以更改以下示例，下述是默认值--------------------
param(
    [Parameter(Mandatory=$true)]
    [int]$start,
    
    [Parameter(Mandatory=$false)]
    [int]$end = $start,
    
    [Parameter(Mandatory=$false)]
    [string]$provider = "",
    
    # DTTR 参数配置
    [Parameter(Mandatory=$false)]
    [string]$dttPath = "C:\Users\user\Desktop\DynamicTTR-0B66",
    
    [Parameter(Mandatory=$false)]
    [string]$dttSource = "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
    
    [Parameter(Mandatory=$false)]
    [int]$dttBatchSize = 50,
    
    [Parameter(Mandatory=$false)]
    [bool]$dttReverseEdge = $true,
    
    [Parameter(Mandatory=$false)]
    [float]$dttAlpha = 0.15,
    
    [Parameter(Mandatory=$false)]
    [string]$dttEpsilon = "0.001",
    
    [Parameter(Mandatory=$false)]
    [bool]$dttIsInUsd = $false,
    
    [Parameter(Mandatory=$false)]
    [bool]$dttIsReduceSwap = $true,
    
    [Parameter(Mandatory=$false)]
    [bool]$dttIsLogValue = $true,
    
    [Parameter(Mandatory=$false)]
    [string]$dttResultFile = ""
)
#--------------------------------------------------------------------

# 如果没有指定结果文件，使用默认路径
if ($dttResultFile -eq "") {
    $dttResultFile = Join-Path $PSScriptRoot "results\DTTR_result.csv"
}

# 多 RPC 提供商池 (按优先级排列)
$providers = @(
    "https://mainnet.chainnodes.org/b23ab29c-345e-44fa-9964-1104b5646941",
    "https://lb.drpc.org/ethereum/AqImLXrstEC1mHVBB4R2nce8VVorjIAR8IsnqhnKxixj"
)

# 使用用户指定的 provider，否则使用第一个（最稳定的）
if ($provider -eq "") {
    $provider = $providers[0]
    Write-Host "Using default RPC: $($provider.Substring(0, 40))..."
}

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Write-Host ""
Write-Host "DTTR Pipeline - Block $start" -NoNewline
if ($end -ne $start) {
    Write-Host " ~ $end"
} else {
    Write-Host ""
}
Write-Host ""

Push-Location $PSScriptRoot
conda activate blockchain

# 设置 PYTHONPATH 以便能找到 algos 模块
$env:PYTHONPATH = "$dttPath;$env:PYTHONPATH"

scrapy crawl trans.block.evm `
    -a providers="$provider" `
    -a start_blk=$start `
    -a end_blk=$end `
    -a enable="BlockchainSpider.middlewares.trans.TransactionReceiptMiddleware,BlockchainSpider.middlewares.trans.TokenTransferMiddleware" `
    -s LOG_LEVEL="INFO" `
    -s DTT_PATH="$dttPath" `
    -s DTT_SOURCE="['$dttSource']" `
    -s DTT_BATCH_SIZE=$dttBatchSize `
    -s DTT_REVERSE_EDGE=$dttReverseEdge `
    -s DTT_ALPHA=$dttAlpha `
    -s DTT_EPSILON=$dttEpsilon `
    -s DTT_IS_IN_USD=$dttIsInUsd `
    -s DTT_IS_REDUCE_SWAP=$dttIsReduceSwap `
    -s DTT_IS_LOG_VALUE=$dttIsLogValue `
    -s DTT_RESULT_FILE="$dttResultFile"

Pop-Location

Write-Host ""
Write-Host "=== Analysis Result ==="
Get-Content "$PSScriptRoot\results\DTTR_result.csv" -Encoding UTF8
Write-Host ""
