# Respaldo diario de la base de datos (Postgres en Supabase).
#
# El plan free de Supabase no ofrece point-in-time recovery, así que los datos
# del box (pagos, membresías, asistencias) necesitan una copia que no dependa del
# proveedor. Este script corre en la PC de recepción — ya encendida 24/7 para el
# bridge — y deja el dump en OneDrive, que al sincronizar lo saca del sitio sin
# pagar almacenamiento extra.
#
# Uso manual:
#   .\backup-db.ps1
#   .\backup-db.ps1 -DestDir D:\Backups -Retener 30
#
# Agendarlo (Task Scheduler, diario 3 AM, "ejecutar aunque el usuario no haya
# iniciado sesión" + "ejecutar apenas sea posible si se perdió una ejecución"):
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<ruta>\backup-db.ps1"
#
# Requiere:
#   • pg_dump (client tools de PostgreSQL; no vienen con Windows).
#   • La variable de entorno de sistema JSB_BACKUP_URL con la URI de Supabase.
#     Nunca poner la URI acá adentro: este archivo va a git.
#
# Restaurar un dump:
#   pg_restore --no-owner --no-privileges -d "<URI destino>" jsb-YYYYMMDD.dump

param(
    [string]$Url = $env:JSB_BACKUP_URL,
    [string]$DestDir = (Join-Path $env:OneDrive "JainSportBox-Backups"),
    [int]$Retener = 14
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Mensaje, [string]$Color = "Gray")
    $linea = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Mensaje
    Write-Host $linea -ForegroundColor $Color
    if ($script:LogFile) { Add-Content -Path $script:LogFile -Value $linea -Encoding utf8 }
}

if (-not $Url) {
    Write-Host "[ERROR] Falta la URI de la base. Definí JSB_BACKUP_URL o pasá -Url." -ForegroundColor Red
    exit 1
}

# pg_dump puede no estar en PATH aunque esté instalado.
$pgDump = (Get-Command pg_dump -ErrorAction SilentlyContinue).Source
if (-not $pgDump) {
    $candidato = Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\pg_dump.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    if ($candidato) { $pgDump = $candidato.FullName }
}
if (-not $pgDump) {
    Write-Host "[ERROR] No se encontró pg_dump. Instalá las client tools de PostgreSQL." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $DestDir)) { New-Item -ItemType Directory -Path $DestDir -Force | Out-Null }
$script:LogFile = Join-Path $DestDir "backup-db.log"

$destino = Join-Path $DestDir ("jsb-{0}.dump" -f (Get-Date -Format "yyyyMMdd"))
Write-Log "Iniciando respaldo -> $destino" "Cyan"

# -Fc (formato custom): comprimido y restaurable por tabla. Solo el esquema
# public: los esquemas auth/storage son de Supabase y no se restauran.
& $pgDump --dbname=$Url --schema=public --no-owner --no-privileges -Fc --file=$destino
if ($LASTEXITCODE -ne 0) {
    Write-Log "pg_dump falló con código $LASTEXITCODE. NO se rotaron los backups viejos." "Red"
    exit 1
}

# Un dump de 0 bytes cuenta como fallo: mejor conservar los anteriores.
$tamano = (Get-Item $destino).Length
if ($tamano -lt 1024) {
    Write-Log "El dump quedó en $tamano bytes: se descarta y se conservan los previos." "Red"
    Remove-Item $destino -Force
    exit 1
}
Write-Log ("OK - {0:N2} MB" -f ($tamano / 1MB)) "Green"

# Rotación: conservar los N más recientes.
$viejos = Get-ChildItem (Join-Path $DestDir "jsb-*.dump") |
    Sort-Object LastWriteTime -Descending | Select-Object -Skip $Retener
foreach ($f in $viejos) {
    Remove-Item $f.FullName -Force
    Write-Log "Rotado (eliminado): $($f.Name)" "DarkGray"
}

Write-Log "Respaldo completado. Copias en disco: $((Get-ChildItem (Join-Path $DestDir 'jsb-*.dump')).Count)" "Cyan"
