param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$OllamaArgs
)

$ErrorActionPreference = 'Stop'
$portableExe = Join-Path $PSScriptRoot '.runtime\ollama\ollama.exe'
if (Test-Path -LiteralPath $portableExe) {
    $exe = $portableExe
    $env:OLLAMA_MODELS = Join-Path $PSScriptRoot 'models'
} else {
    $installed = Get-Command ollama.exe -CommandType Application -ErrorAction SilentlyContinue
    if (-not $installed) {
        $standardExe = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
        if (Test-Path -LiteralPath $standardExe) { $installed = Get-Item -LiteralPath $standardExe }
    }
    if (-not $installed) {
        throw 'Ollama is not installed. Install it from https://ollama.com/download/windows and run: ollama pull qwen3:4b-instruct'
    }
    $exe = $installed.Source
    if (-not $exe) { $exe = $installed.FullName }
}

$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_CONTEXT_LENGTH = '4096'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot 'logs') | Out-Null
if (Test-Path -LiteralPath $portableExe) {
    New-Item -ItemType Directory -Force -Path $env:OLLAMA_MODELS | Out-Null
}

function Test-Ollama {
    try {
        $null = Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 2
        return $true
    } catch { return $false }
}

if (-not (Test-Ollama)) {
    $server = Start-Process -FilePath $exe -ArgumentList 'serve' -WindowStyle Hidden -PassThru `
        -WorkingDirectory $PSScriptRoot `
        -RedirectStandardOutput (Join-Path $PSScriptRoot 'logs\ollama.stdout.log') `
        -RedirectStandardError (Join-Path $PSScriptRoot 'logs\ollama.stderr.log')
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if (Test-Ollama) { $ready = $true; break }
        if ($server.HasExited) { throw 'Ollama exited. See logs\ollama.stderr.log.' }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { throw 'Ollama did not start. See logs\ollama.stderr.log.' }
}

if (-not $OllamaArgs -or $OllamaArgs.Count -eq 0) {
    $OllamaArgs = @('run', 'qwen3:4b-instruct')
}
& $exe @OllamaArgs
exit $LASTEXITCODE
