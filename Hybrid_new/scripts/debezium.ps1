# =============================================================================
# debezium.ps1 - Registra connettore CDC Debezium (PostgreSQL -> Neo4j)
# Branch: hybrid | APP_Opzione_Ibrida
#
# Uso:
#   .\scripts\debezium.ps1
#
# Prerequisiti:
#   - docker compose -f docker-compose.infra.yml up -d  (Debezium su :8083)
#   - PostgreSQL attivo su :5432
#   - Neo4j attivo su :7687
# =============================================================================

$ErrorActionPreference = "Stop"

$DEBEZIUM_URL = "http://localhost:8083"
$CONNECTOR_NAME = "tap-postgres-connector"

Write-Host "[debezium] Verifica che Debezium Connect sia attivo su $DEBEZIUM_URL ..."

# Aspetta che Debezium sia pronto (max 60 secondi)
$maxAttempts = 12
$attempt = 0
do {
    $attempt++
    try {
        $response = Invoke-RestMethod -Uri "$DEBEZIUM_URL/connectors" -Method GET -TimeoutSec 5
        Write-Host "[debezium] Debezium Connect e' attivo."
        break
    } catch {
        if ($attempt -ge $maxAttempts) {
            Write-Host "[debezium] ERRORE: Debezium non risponde dopo $maxAttempts tentativi."
            Write-Host "[debezium] Assicurati che lo stack sia attivo:"
            Write-Host "[debezium]   docker compose -f docker-compose.infra.yml up -d"
            exit 1
        }
        Write-Host "[debezium] Attesa Debezium... (tentativo $attempt/$maxAttempts)"
        Start-Sleep -Seconds 5
    }
} while ($true)

# Controlla se il connettore esiste gia'
Write-Host "[debezium] Controllo connettore esistente '$CONNECTOR_NAME'..."
try {
    $existing = Invoke-RestMethod -Uri "$DEBEZIUM_URL/connectors/$CONNECTOR_NAME" -Method GET -TimeoutSec 5
    Write-Host "[debezium] Il connettore '$CONNECTOR_NAME' esiste gia'. Eliminazione e ricreazione..."
    Invoke-RestMethod -Uri "$DEBEZIUM_URL/connectors/$CONNECTOR_NAME" -Method DELETE -TimeoutSec 5 | Out-Null
    Start-Sleep -Seconds 2
} catch {
    Write-Host "[debezium] Connettore non esistente, verra' creato."
}

# Payload configurazione connettore CDC
$connectorConfig = @{
    name   = $CONNECTOR_NAME
    config = @{
        # Tipo connettore
        "connector.class"                         = "io.debezium.connector.postgresql.PostgresConnector"
        "plugin.name"                             = "pgoutput"

        # Connessione PostgreSQL (CHRONOS DB)
        "database.hostname"                       = "postgres"
        "database.port"                           = "5432"
        "database.user"                           = "tap"
        "database.password"                       = "tap"
        "database.dbname"                         = "chronos"
        "database.server.name"                    = "tap"

        # Tabelle da monitorare (scritture CHRONOS che devono aggiornare Neo4j)
        "table.include.list"                      = "public.gamma_scores,public.extraction_runs,public.provenance_events"

        # Topic Kafka di output (CDC events)
        "topic.prefix"                            = "tap.cdc"

        # Slot di replica PostgreSQL
        "slot.name"                               = "tap_debezium_slot"
        "publication.name"                        = "tap_debezium_pub"

        # Gestione schema
        "schema.history.internal.kafka.bootstrap.servers" = "kafka:9092"
        "schema.history.internal.kafka.topic"    = "tap.cdc.schema-history"

        # Trasformazioni: estrae solo il valore after per ogni evento
        "transforms"                              = "unwrap"
        "transforms.unwrap.type"                  = "io.debezium.transforms.ExtractNewRecordState"
        "transforms.unwrap.drop.tombstones"       = "false"
        "transforms.unwrap.delete.handling.mode" = "rewrite"

        # Heartbeat ogni 30s per mantenere attivo il replication slot
        "heartbeat.interval.ms"                   = "30000"
    }
} | ConvertTo-Json -Depth 5

Write-Host "[debezium] Registrazione connettore '$CONNECTOR_NAME'..."

try {
    $result = Invoke-RestMethod `
        -Uri "$DEBEZIUM_URL/connectors" `
        -Method POST `
        -ContentType "application/json" `
        -Body $connectorConfig `
        -TimeoutSec 15

    Write-Host "[debezium] Connettore registrato con successo!"
    Write-Host "[debezium] Nome    : $($result.name)"
    Write-Host "[debezium] Stato   : controlla con GET $DEBEZIUM_URL/connectors/$CONNECTOR_NAME/status"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "[debezium] ERRORE nella registrazione (HTTP $statusCode): $_"
    exit 1
}

# Verifica stato finale
Start-Sleep -Seconds 3
Write-Host ""
Write-Host "[debezium] Verifica stato connettore..."
try {
    $status = Invoke-RestMethod -Uri "$DEBEZIUM_URL/connectors/$CONNECTOR_NAME/status" -Method GET -TimeoutSec 5
    $connState = $status.connector.state
    Write-Host "[debezium] Stato connettore : $connState"
    if ($connState -eq "RUNNING") {
        Write-Host "[debezium] CDC attivo! PostgreSQL(CHRONOS) -> Kafka -> Neo4j(V-Genome)"
    } else {
        Write-Host "[debezium] ATTENZIONE: stato non RUNNING. Controlla i log Debezium:"
        Write-Host "[debezium]   docker compose -f docker-compose.infra.yml logs debezium"
    }
} catch {
    Write-Host "[debezium] Non riesco a verificare lo stato. Controlla manualmente:"
    Write-Host "[debezium]   Invoke-RestMethod $DEBEZIUM_URL/connectors/$CONNECTOR_NAME/status"
}

Write-Host ""
Write-Host "[debezium] Topic CDC creati su Kafka:"
Write-Host "[debezium]   tap.cdc.public.gamma_scores"
Write-Host "[debezium]   tap.cdc.public.extraction_runs"
Write-Host "[debezium]   tap.cdc.public.provenance_events"
