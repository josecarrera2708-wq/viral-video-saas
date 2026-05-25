#!/usr/bin/env pwsh
# Script para configurar el backend automáticamente

param(
    [string]$StripeKey = "",
    [string]$KlingKey = "",
    [string]$RDSPassword = ""
)

$env:PATH = "C:\Program Files\Amazon\AWSCLIV2;$env:PATH"

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  CONFIGURACIÓN AUTOMÁTICA - BACKEND" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

# Si no se proporcionan credenciales, pedir al usuario
if ([string]::IsNullOrEmpty($StripeKey)) {
    $StripeKey = Read-Host "Ingresa Stripe Secret Key (sk_test_...)"
}

if ([string]::IsNullOrEmpty($KlingKey)) {
    $KlingKey = Read-Host "Ingresa Kling API Key"
}

if ([string]::IsNullOrEmpty($RDSPassword)) {
    Write-Host "Para obtener contraseña RDS, vamos a Secrets Manager..." -ForegroundColor Yellow

    $secretValue = aws secretsmanager get-secret-value --secret-id rds-password --region us-east-1 --output json 2>&1

    if ($LASTEXITCODE -eq 0) {
        $secret = $secretValue | ConvertFrom-Json
        $RDSPassword = $secret.SecretString
        Write-Host "✓ Contraseña RDS obtenida de Secrets Manager" -ForegroundColor Green
    } else {
        Write-Host "⚠ No se encontró en Secrets Manager" -ForegroundColor Yellow
        $RDSPassword = Read-Host "Ingresa manualmente la contraseña RDS"
    }
}

Write-Host "Obteniendo detalles de infraestructura..." -ForegroundColor Cyan

# Detalles
$rdsEndpoint = "viral-video-saas-db.cil62c4ow8ky.us-east-1.rds.amazonaws.com"
$s3Uploads = "viral-uploads-9794"
$s3Processed = "viral-processed-8902"
$secretKey = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Random -InputObject (65..90 + 97..122 + 48..57) -Count 32 | % { [char]$_ }) -join ''))

Write-Host ""
Write-Host "Configurando Docker con variables de entorno..." -ForegroundColor Yellow

# Comando Docker
$dockerCmd = @"
docker run -d `
  --name backend `
  --restart unless-stopped `
  -p 8000:8000 `
  -e DATABASE_URL="postgresql://postgres:$RDSPassword@$rdsEndpoint:5432/viral_db" `
  -e AWS_REGION=us-east-1 `
  -e AWS_BUCKET_UPLOADS=$s3Uploads `
  -e AWS_BUCKET_PROCESSED=$s3Processed `
  -e STRIPE_SECRET_KEY=$StripeKey `
  -e KLING_API_KEY=$KlingKey `
  -e SECRET_KEY=$secretKey `
  -e DEBUG=False `
  -e ALLOWED_HOSTS=18.209.92.177,localhost `
  971023775322.dkr.ecr.us-east-1.amazonaws.com/viral-backend:latest
"@

Write-Host "Deteniendo contenedor anterior..." -ForegroundColor Yellow
docker stop backend 2>&1 | Out-Null
docker rm backend 2>&1 | Out-Null

Write-Host "Iniciando nuevo contenedor con configuración..." -ForegroundColor Yellow
Invoke-Expression $dockerCmd

Write-Host ""
Write-Host "Esperando que el contenedor inicie..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "Verificando estado..." -ForegroundColor Cyan

$logs = docker logs backend 2>&1 | Select-Object -Last 5
Write-Host $logs

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "✅ BACKEND CONFIGURADO" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Backend disponible en: http://18.209.92.177:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://18.209.92.177:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Próximo paso: Desplegar frontend" -ForegroundColor Yellow
