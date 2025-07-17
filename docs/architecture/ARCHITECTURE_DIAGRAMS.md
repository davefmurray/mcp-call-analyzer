# Architecture Diagrams - MCP Call Analyzer

This document contains detailed architecture diagrams showing the system design, data flow, and component interactions of the MCP Call Analyzer.

## 📊 System Overview

### High-Level Architecture

```mermaid
graph TB
    subgraph "External Services"
        DC[Digital Concierge API]
        CF[CloudFront CDN]
        DG[Deepgram API]
        OAI[OpenAI GPT-4]
    end
    
    subgraph "MCP Call Analyzer"
        subgraph "Data Collection"
            AS[API Scraper]
            BS[Browser Scraper]
            AD[Audio Downloader]
        end
        
        subgraph "Processing Pipeline"
            TP[Transcription Processor]
            AP[Analysis Processor]
            QM[Queue Manager]
        end
        
        subgraph "Storage"
            DB[(Supabase DB)]
            FS[File Storage]
        end
        
        subgraph "Output"
            API[REST API]
            WH[Webhooks]
            RPT[Reports]
        end
    end
    
    DC -->|Metadata| AS
    DC -->|Auth| BS
    CF -->|Audio URLs| BS
    BS -->|Downloads| AD
    AD -->|Audio Files| FS
    FS -->|Audio| TP
    TP -->|Transcript| DG
    DG -->|Text| AP
    AP -->|Analysis| OAI
    OAI -->|Insights| DB
    AS -->|Call Data| DB
    DB -->|Data| API
    DB -->|Triggers| WH
    DB -->|Analytics| RPT
    QM -->|Orchestrates| TP
    QM -->|Orchestrates| AP
```

## 🔄 Data Flow Diagram

### Complete Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant Pipeline
    participant DCApi as DC API
    participant Browser
    participant CloudFront
    participant Deepgram
    participant OpenAI
    participant Database
    
    User->>Pipeline: Start Processing
    Pipeline->>DCApi: Authenticate
    DCApi-->>Pipeline: JWT Token
    
    Pipeline->>DCApi: Fetch Calls
    DCApi-->>Pipeline: Call Metadata
    Pipeline->>Database: Store Calls
    
    loop For Each Call
        Pipeline->>Browser: Navigate to Call
        Browser->>CloudFront: Request Audio
        CloudFront-->>Browser: Signed URL
        Browser->>Pipeline: Download Audio
        Pipeline->>Deepgram: Transcribe Audio
        Deepgram-->>Pipeline: Transcript
        Pipeline->>OpenAI: Analyze Transcript
        OpenAI-->>Pipeline: Analysis
        Pipeline->>Database: Store Results
    end
    
    Pipeline-->>User: Processing Complete
```

## 🏗️ Component Architecture

### Modular Design

```mermaid
graph LR
    subgraph "Scrapers Module"
        API[APIScraper]
        MCP[MCPBrowserScraper]
        BASE[BaseScraper]
        API --> BASE
        MCP --> BASE
    end
    
    subgraph "Pipelines Module"
        FHP[FinalHybridPipeline]
        BP[BatchProcessor]
        QP[QueueProcessor]
        FHP --> BP
        BP --> QP
    end
    
    subgraph "Utils Module"
        AU[AudioUtils]
        DBU[DatabaseUtils]
        CU[CacheUtils]
        LU[LoggingUtils]
    end
    
    subgraph "Models Module"
        CM[CallModel]
        RM[RecordingModel]
        TM[TranscriptionModel]
        AM[AnalysisModel]
    end
    
    FHP --> API
    FHP --> MCP
    FHP --> AU
    FHP --> DBU
    BP --> QP
    QP --> DBU
```

## 💾 Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    CALLS ||--o| RECORDINGS : has
    CALLS ||--o| TRANSCRIPTIONS : has
    CALLS ||--o| CALL_ANALYSIS : has
    CALLS ||--o{ PROCESSING_QUEUE : queued_in
    CALLS }|--|| ANALYTICS_SUMMARY : aggregated_in
    
    CALLS {
        string call_id PK
        string dc_call_id UK
        string customer_name
        string customer_number
        string call_direction
        int duration_seconds
        timestamp date_created
        boolean has_recording
        string status
        text dc_transcript
        numeric dc_sentiment
        string extension
    }
    
    RECORDINGS {
        int id PK
        string call_id FK
        string file_name
        bigint file_size_bytes
        string mime_type
        string storage_path
        text storage_url
        string upload_status
        timestamp uploaded_at
    }
    
    TRANSCRIPTIONS {
        int id PK
        string call_id FK
        text transcript
        jsonb speaker_segments
        numeric confidence_score
        string language_code
        string model_used
        int processing_time_ms
        int word_count
    }
    
    CALL_ANALYSIS {
        int id PK
        string call_id FK
        jsonb analysis_data
        string category
        string sentiment
        text customer_intent
        boolean follow_up_needed
        string model_used
        int prompt_tokens
        int completion_tokens
    }
    
    PROCESSING_QUEUE {
        int id PK
        string call_id FK
        int priority
        string status
        int attempts
        timestamp last_attempt_at
        text error_message
        string worker_id
    }
    
    ANALYTICS_SUMMARY {
        int id PK
        date date
        int hour
        int total_calls
        int total_duration_seconds
        numeric avg_duration_seconds
        int positive_calls
        int neutral_calls
        int negative_calls
        jsonb category_counts
    }
```

## 🔐 Security Architecture

### Authentication & Authorization Flow

```mermaid
graph TD
    subgraph "Client Layer"
        CL[Client Application]
    end
    
    subgraph "Authentication"
        AUTH[Auth Service]
        JWT[JWT Validator]
        SESS[Session Manager]
    end
    
    subgraph "API Gateway"
        GW[API Gateway]
        RL[Rate Limiter]
        VAL[Request Validator]
    end
    
    subgraph "Services"
        AS[API Service]
        BS[Browser Service]
        PS[Processing Service]
    end
    
    subgraph "Security"
        ENC[Encryption Service]
        SEC[Secrets Manager]
        LOG[Security Logger]
    end
    
    CL -->|Credentials| AUTH
    AUTH -->|Token| JWT
    JWT -->|Valid Token| SESS
    SESS -->|Session| GW
    GW --> RL
    RL --> VAL
    VAL --> AS
    VAL --> BS
    VAL --> PS
    AS --> ENC
    BS --> SEC
    PS --> LOG
```

## 🚀 Deployment Architecture

### Production Infrastructure

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Application Load Balancer]
    end
    
    subgraph "Application Tier"
        APP1[App Instance 1]
        APP2[App Instance 2]
        APP3[App Instance 3]
    end
    
    subgraph "Worker Tier"
        W1[Worker 1]
        W2[Worker 2]
        W3[Worker 3]
        WQ[Work Queue]
    end
    
    subgraph "Data Tier"
        DB[(Primary DB)]
        DBR[(Read Replica)]
        CACHE[(Redis Cache)]
        S3[Object Storage]
    end
    
    subgraph "External Services"
        EXT[External APIs]
    end
    
    LB --> APP1
    LB --> APP2
    LB --> APP3
    APP1 --> WQ
    APP2 --> WQ
    APP3 --> WQ
    WQ --> W1
    WQ --> W2
    WQ --> W3
    W1 --> DB
    W2 --> DB
    W3 --> DB
    APP1 --> CACHE
    APP2 --> CACHE
    APP3 --> CACHE
    APP1 --> DBR
    APP2 --> DBR
    APP3 --> DBR
    W1 --> S3
    W2 --> S3
    W3 --> S3
    W1 --> EXT
    W2 --> EXT
    W3 --> EXT
```

## 📈 Performance Architecture

### Caching Strategy

```mermaid
graph LR
    subgraph "Request Flow"
        REQ[Request]
        L1[L1 Cache<br/>Application]
        L2[L2 Cache<br/>Redis]
        DB[Database]
    end
    
    subgraph "Cache Layers"
        MC[Memory Cache<br/>5min TTL]
        RC[Redis Cache<br/>1hr TTL]
        DC[DB Cache<br/>24hr TTL]
    end
    
    REQ --> L1
    L1 -->|Miss| L2
    L2 -->|Miss| DB
    L1 --> MC
    L2 --> RC
    DB --> DC
    
    DB -->|Update| L2
    L2 -->|Update| L1
```

## 🔄 State Machine

### Call Processing States

```mermaid
stateDiagram-v2
    [*] --> pending_download
    pending_download --> downloading: Start Download
    downloading --> downloaded: Success
    downloading --> download_failed: Error
    download_failed --> pending_download: Retry
    downloaded --> transcribing: Start Transcription
    transcribing --> transcribed: Success
    transcribing --> transcription_failed: Error
    transcription_failed --> transcribing: Retry
    transcribed --> analyzing: Start Analysis
    analyzing --> analyzed: Success
    analyzing --> analysis_failed: Error
    analysis_failed --> analyzing: Retry
    analyzed --> [*]
    
    download_failed --> error: Max Retries
    transcription_failed --> error: Max Retries
    analysis_failed --> error: Max Retries
    error --> [*]
```

## 🌐 API Architecture

### RESTful Endpoints

```mermaid
graph TD
    subgraph "API Routes"
        AUTH[/auth]
        CALLS[/calls]
        TRANS[/transcriptions]
        ANAL[/analysis]
        STATS[/statistics]
    end
    
    subgraph "Auth Endpoints"
        LOGIN[POST /auth/login]
        LOGOUT[POST /auth/logout]
        REFRESH[POST /auth/refresh]
    end
    
    subgraph "Call Endpoints"
        LIST[GET /calls]
        GET[GET /calls/:id]
        PROC[POST /calls/:id/process]
        RETRY[POST /calls/:id/retry]
    end
    
    subgraph "Analysis Endpoints"
        GETA[GET /analysis/:call_id]
        REDO[POST /analysis/:call_id/redo]
    end
    
    AUTH --> LOGIN
    AUTH --> LOGOUT
    AUTH --> REFRESH
    CALLS --> LIST
    CALLS --> GET
    CALLS --> PROC
    CALLS --> RETRY
    ANAL --> GETA
    ANAL --> REDO
```

## 🔍 Monitoring Architecture

### Observability Stack

```mermaid
graph TB
    subgraph "Application"
        APP[Application]
        METRICS[Metrics Collector]
        LOGS[Log Aggregator]
        TRACES[Trace Collector]
    end
    
    subgraph "Collection"
        PROM[Prometheus]
        ELK[ELK Stack]
        JAEGER[Jaeger]
    end
    
    subgraph "Visualization"
        GRAF[Grafana]
        KIB[Kibana]
        JAEG_UI[Jaeger UI]
    end
    
    subgraph "Alerting"
        AM[Alert Manager]
        PD[PagerDuty]
        SLACK[Slack]
    end
    
    APP --> METRICS
    APP --> LOGS
    APP --> TRACES
    METRICS --> PROM
    LOGS --> ELK
    TRACES --> JAEGER
    PROM --> GRAF
    ELK --> KIB
    JAEGER --> JAEG_UI
    PROM --> AM
    AM --> PD
    AM --> SLACK
```

## 🚦 Error Handling Flow

### Retry and Recovery Strategy

```mermaid
flowchart TD
    START[Start Processing]
    TRY[Try Operation]
    SUCCESS{Success?}
    ERROR[Error Occurred]
    RETRY_CHECK{Retries < Max?}
    BACKOFF[Exponential Backoff]
    RETRY[Retry Operation]
    LOG_ERROR[Log Error]
    NOTIFY[Notify Admin]
    QUEUE_DLQ[Dead Letter Queue]
    END[End]
    
    START --> TRY
    TRY --> SUCCESS
    SUCCESS -->|Yes| END
    SUCCESS -->|No| ERROR
    ERROR --> RETRY_CHECK
    RETRY_CHECK -->|Yes| BACKOFF
    BACKOFF --> RETRY
    RETRY --> TRY
    RETRY_CHECK -->|No| LOG_ERROR
    LOG_ERROR --> NOTIFY
    NOTIFY --> QUEUE_DLQ
    QUEUE_DLQ --> END
```

---

## 📚 Additional Resources

- [System Requirements](../SYSTEM_REQUIREMENTS.md)
- [API Documentation](../api/API_REFERENCE.md)
- [Database Schema](../database/schema.sql)
- [Deployment Guide](../DEPLOYMENT_GUIDE.md)

---

*These diagrams are maintained using Mermaid syntax and can be rendered in any Markdown viewer that supports Mermaid diagrams.*