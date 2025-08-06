# AquaScene Content Engine - Technical Diagrams Collection

## Table of Contents
1. [Diagram Overview](#diagram-overview)
2. [System Architecture Diagrams](#system-architecture-diagrams)
3. [Service Architecture Diagrams](#service-architecture-diagrams)
4. [Database Architecture Diagrams](#database-architecture-diagrams)
5. [Infrastructure Diagrams](#infrastructure-diagrams)
6. [Security Architecture Diagrams](#security-architecture-diagrams)
7. [Performance and Scaling Diagrams](#performance-and-scaling-diagrams)
8. [Data Flow Diagrams](#data-flow-diagrams)
9. [Deployment Architecture Diagrams](#deployment-architecture-diagrams)

## Diagram Overview

This document consolidates all technical diagrams for the AquaScene Content Engine, providing visual representations of the system's architecture, data flows, and operational patterns. All diagrams are created using Mermaid syntax for consistency and maintainability.

### Diagram Legend
```mermaid
graph TB
    subgraph "Legend - Components"
        A[Application Service]
        B[(Database)]
        C[Load Balancer]
        D{{Cache}}
        E[External API]
        F[Queue System]
    end
    
    subgraph "Legend - Connections"
        G[Service A] -->|HTTP/REST| H[Service B]
        I[Service C] -.->|Async/Queue| J[Service D]
        K[Service E] ==>|High Volume| L[Service F]
    end
    
    subgraph "Legend - Colors"
        M[Core Service]
        N[Infrastructure]
        O[External System]
        P[Monitoring]
    end
    
    classDef coreService fill:#e1f5fe
    classDef infrastructure fill:#f3e5f5
    classDef external fill:#fff3e0
    classDef monitoring fill:#e8f5e8
    
    class M coreService
    class N infrastructure
    class O external
    class P monitoring
```

## System Architecture Diagrams

### 1. High-Level System Architecture
```mermaid
graph TB
    subgraph "External Systems"
        A[Airtable CMS]
        B[OpenAI/Anthropic/Ollama]
        C[SendGrid Email]
        D[Instagram API]
        E[Web Sources]
    end
    
    subgraph "Load Balancer & Reverse Proxy"
        F[Nginx]
    end
    
    subgraph "Frontend Layer"
        G[Admin Dashboard<br/>React SPA]
    end
    
    subgraph "API Gateway & Core Services"
        H[Content Manager<br/>API Gateway]
        I[AI Processor<br/>Content Generation]
        J[Web Scraper<br/>Data Collection]
        K[Distributor<br/>Multi-Channel Publishing]
        L[Subscriber Manager<br/>User Management]
    end
    
    subgraph "Data Layer"
        M[(PostgreSQL<br/>Primary Database)]
        N[(Redis<br/>Cache & Queue)]
        O[(MinIO<br/>Object Storage)]
    end
    
    subgraph "Monitoring & Observability"
        P[Prometheus<br/>Metrics]
        Q[Grafana<br/>Dashboards]
        R[Loki<br/>Logs]
        S[AlertManager<br/>Alerts]
    end
    
    %% External connections
    A --> H
    B --> I
    C --> K
    D --> K
    E --> J
    
    %% Frontend connections
    F --> G
    G --> H
    
    %% Service connections
    F --> H
    H --> I
    H --> J
    H --> K
    H --> L
    
    %% Data connections
    H --> M
    I --> M
    J --> M
    K --> M
    L --> M
    
    H --> N
    I --> N
    J --> N
    K --> N
    L --> N
    
    K --> O
    
    %% Monitoring connections
    H --> P
    I --> P
    J --> P
    K --> P
    L --> P
    P --> Q
    P --> S
    R --> Q
    
    classDef coreService fill:#e1f5fe
    classDef infrastructure fill:#f3e5f5
    classDef external fill:#fff3e0
    classDef monitoring fill:#e8f5e8
    
    class H,I,J,K,L coreService
    class M,N,O,F infrastructure
    class A,B,C,D,E external
    class P,Q,R,S monitoring
```

### 2. Service Interaction Flow
```mermaid
sequenceDiagram
    participant C as Client
    participant CM as Content Manager
    participant AI as AI Processor
    participant WS as Web Scraper
    participant D as Distributor
    participant SM as Subscriber Manager
    participant DB as Database
    participant R as Redis
    
    Note over C,R: Content Creation Workflow
    
    C->>CM: Create Content Request
    CM->>DB: Store Content Metadata
    CM->>R: Queue AI Processing
    AI-->>R: Poll for Tasks
    AI->>DB: Fetch Source Materials
    AI->>AI: Generate Content
    AI->>DB: Store Generated Content
    AI->>R: Publish Content Ready Event
    CM-->>R: Listen for Events
    CM->>D: Queue for Distribution
    D->>SM: Get Subscriber Lists
    SM->>DB: Fetch Subscribers
    SM-->>D: Return Subscriber Data
    D->>D: Generate Newsletters
    D->>C: Send via SendGrid/Instagram
    D->>DB: Update Distribution Metrics
```

## Service Architecture Diagrams

### 3. Microservices Communication Patterns
```mermaid
graph TB
    subgraph "Content Manager (API Gateway)"
        CM_API[FastAPI Router]
        CM_AUTH[Authentication]
        CM_CACHE[Response Cache]
        CM_QUEUE[Task Queue]
    end
    
    subgraph "AI Processor Service"
        AI_WORKER[Content Worker]
        AI_CLIENT[LLM Client Manager]
        AI_QUEUE[Job Queue]
        AI_CACHE[Model Cache]
    end
    
    subgraph "Web Scraper Service"
        WS_CRAWLER[Web Crawler]
        WS_PARSER[Content Parser]
        WS_QUEUE[URL Queue]
        WS_CACHE[Request Cache]
    end
    
    subgraph "Distributor Service"
        D_EMAIL[Email Service]
        D_SOCIAL[Social Media]
        D_TEMPLATE[Template Engine]
        D_QUEUE[Distribution Queue]
    end
    
    subgraph "Subscriber Manager"
        SM_API[Subscriber API]
        SM_SEGMENT[Segmentation]
        SM_PRIVACY[GDPR Compliance]
        SM_CACHE[User Cache]
    end
    
    %% Inter-service communication
    CM_API --> AI_WORKER
    CM_API --> WS_CRAWLER
    CM_API --> D_EMAIL
    CM_API --> SM_API
    
    D_EMAIL --> SM_SEGMENT
    AI_WORKER --> WS_PARSER
    
    %% Queue connections
    CM_QUEUE -.-> AI_QUEUE
    CM_QUEUE -.-> WS_QUEUE
    CM_QUEUE -.-> D_QUEUE
    
    classDef apiLayer fill:#e1f5fe
    classDef processingLayer fill:#f1f8e9
    classDef queueLayer fill:#fff3e0
    classDef cacheLayer fill:#fce4ec
    
    class CM_API,AI_WORKER,WS_CRAWLER,D_EMAIL,SM_API apiLayer
    class AI_CLIENT,WS_PARSER,D_TEMPLATE,SM_SEGMENT processingLayer
    class CM_QUEUE,AI_QUEUE,WS_QUEUE,D_QUEUE queueLayer
    class CM_CACHE,AI_CACHE,WS_CACHE,SM_CACHE cacheLayer
```

### 4. Event-Driven Architecture
```mermaid
graph TB
    subgraph "Event Producers"
        EP1[Content Manager]
        EP2[AI Processor]
        EP3[Web Scraper]
        EP4[Distributor]
        EP5[Subscriber Manager]
    end
    
    subgraph "Event Bus (Redis Streams)"
        EB[Event Streams]
        EQ1[content.created]
        EQ2[content.generated]
        EQ3[content.published]
        EQ4[email.sent]
        EQ5[user.subscribed]
    end
    
    subgraph "Event Consumers"
        EC1[Analytics Service]
        EC2[Notification Service]
        EC3[Search Indexer]
        EC4[Backup Service]
        EC5[Audit Logger]
    end
    
    %% Producer to Event Bus
    EP1 --> EQ1
    EP2 --> EQ2
    EP1 --> EQ3
    EP4 --> EQ4
    EP5 --> EQ5
    
    %% Event Bus to Consumers
    EQ1 --> EC1
    EQ1 --> EC3
    EQ2 --> EC1
    EQ2 --> EC3
    EQ3 --> EC2
    EQ4 --> EC1
    EQ5 --> EC2
    
    %% All events to audit
    EQ1 --> EC5
    EQ2 --> EC5
    EQ3 --> EC5
    EQ4 --> EC5
    EQ5 --> EC5
    
    classDef producer fill:#e1f5fe
    classDef eventBus fill:#fff3e0
    classDef consumer fill:#e8f5e8
    
    class EP1,EP2,EP3,EP4,EP5 producer
    class EB,EQ1,EQ2,EQ3,EQ4,EQ5 eventBus
    class EC1,EC2,EC3,EC4,EC5 consumer
```

## Database Architecture Diagrams

### 5. Database Schema Relationships
```mermaid
erDiagram
    raw_content {
        uuid id PK
        text source_url
        varchar source_domain
        varchar content_type
        text content
        timestamp scraped_at
        boolean processed
    }
    
    generated_content {
        uuid id PK
        varchar content_type
        text title
        text content
        decimal quality_score
        varchar status
        timestamp published_at
    }
    
    subscribers {
        uuid id PK
        varchar email UK
        varchar first_name_encrypted
        varchar last_name_encrypted
        varchar status
        timestamp subscription_date
    }
    
    newsletter_issues {
        uuid id PK
        varchar template_type
        text subject_line
        uuid_array content_ids
        timestamp sent_at
        varchar status
    }
    
    content_metrics {
        uuid id PK
        uuid content_id FK
        varchar metric_type
        varchar metric_name
        decimal metric_value
        date date_bucket
    }
    
    raw_content ||--o{ generated_content : "source_materials"
    generated_content ||--o{ content_metrics : "has_metrics"
    generated_content ||--o{ newsletter_issues : "included_in"
    subscribers ||--o{ newsletter_issues : "receives"
```

### 6. Data Flow Architecture
```mermaid
graph LR
    subgraph "Data Sources"
        A[Web Scraping]
        B[Airtable Import]
        C[Manual Input]
        D[AI Generation]
    end
    
    subgraph "Raw Data Processing"
        E[Data Validation]
        F[Content Extraction]
        G[Deduplication]
        H[Quality Scoring]
    end
    
    subgraph "Content Processing"
        I[AI Enhancement]
        J[SEO Optimization]
        K[Brand Validation]
        L[Template Application]
    end
    
    subgraph "Distribution Preparation"
        M[Newsletter Assembly]
        N[Social Media Formatting]
        O[Personalization]
        P[Segmentation]
    end
    
    subgraph "Output Channels"
        Q[Email Delivery]
        R[Instagram Posts]
        S[Website Publishing]
        T[API Distribution]
    end
    
    A --> E
    B --> E
    C --> E
    D --> I
    
    E --> F
    F --> G
    G --> H
    H --> I
    
    I --> J
    J --> K
    K --> L
    
    L --> M
    L --> N
    M --> O
    N --> O
    O --> P
    
    P --> Q
    P --> R
    P --> S
    P --> T
```

## Infrastructure Diagrams

### 7. Container Orchestration Architecture
```mermaid
graph TB
    subgraph "Load Balancer Tier"
        LB[Nginx Load Balancer]
    end
    
    subgraph "Kubernetes Cluster"
        subgraph "Namespace: aquascene-content-engine"
            subgraph "Content Manager Pods"
                CM1[content-manager-1]
                CM2[content-manager-2]
                CM3[content-manager-3]
            end
            
            subgraph "AI Processor Pods"
                AI1[ai-processor-1]
                AI2[ai-processor-2]
            end
            
            subgraph "Other Service Pods"
                WS1[web-scraper-1]
                D1[distributor-1]
                SM1[subscriber-manager-1]
            end
            
            subgraph "Infrastructure Pods"
                PG[PostgreSQL StatefulSet]
                R[Redis Cluster]
                M[MinIO Cluster]
            end
        end
        
        subgraph "Monitoring Namespace"
            PROM[Prometheus]
            GRAF[Grafana]
            LOKI[Loki]
        end
    end
    
    LB --> CM1
    LB --> CM2
    LB --> CM3
    
    CM1 --> AI1
    CM1 --> WS1
    CM1 --> D1
    CM1 --> SM1
    
    CM1 --> PG
    CM1 --> R
    
    AI1 --> PG
    WS1 --> PG
    D1 --> M
    
    PROM --> CM1
    PROM --> AI1
    PROM --> WS1
```

### 8. Network Architecture
```mermaid
graph TB
    subgraph "External Network"
        INT[Internet]
        CDN[CloudFlare CDN]
    end
    
    subgraph "DMZ (10.0.1.0/24)"
        WAF[Web Application Firewall]
        ALB[Application Load Balancer]
    end
    
    subgraph "Application Tier (10.0.10.0/24)"
        APP1[App Server 1]
        APP2[App Server 2]
        APP3[App Server N]
    end
    
    subgraph "Data Tier (10.0.20.0/24)"
        DB1[(Primary DB)]
        DB2[(Replica DB)]
        CACHE[(Redis Cluster)]
        STORAGE[(Object Storage)]
    end
    
    subgraph "Management Tier (10.0.30.0/24)"
        MON[Monitoring]
        LOG[Logging]
        BACKUP[Backup]
    end
    
    INT --> CDN
    CDN --> WAF
    WAF --> ALB
    ALB --> APP1
    ALB --> APP2
    ALB --> APP3
    
    APP1 --> DB1
    APP2 --> DB2
    APP3 --> CACHE
    APP1 --> STORAGE
    
    APP1 --> MON
    APP2 --> LOG
    DB1 --> BACKUP
    
    classDef external fill:#fff3e0
    classDef dmz fill:#ffebee
    classDef application fill:#e1f5fe
    classDef data fill:#f3e5f5
    classDef management fill:#e8f5e8
    
    class INT,CDN external
    class WAF,ALB dmz
    class APP1,APP2,APP3 application
    class DB1,DB2,CACHE,STORAGE data
    class MON,LOG,BACKUP management
```

## Security Architecture Diagrams

### 9. Authentication Flow
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as Auth Service
    participant G as API Gateway
    participant S as Service
    participant D as Database
    
    U->>F: Login Request
    F->>A: Authenticate(username, password)
    A->>D: Validate Credentials
    D-->>A: User Data + Permissions
    A->>A: Generate JWT Token
    A-->>F: JWT + Refresh Token
    F->>F: Store Tokens Securely
    F-->>U: Login Success
    
    Note over U,D: Subsequent API Requests
    
    U->>F: API Request
    F->>G: Request + JWT Token
    G->>G: Validate JWT
    G->>G: Check Permissions
    G->>S: Forward Request + User Context
    S->>D: Query Data
    D-->>S: Response Data
    S-->>G: Service Response
    G-->>F: API Response
    F-->>U: Display Data
```

### 10. Security Layers
```mermaid
graph TB
    subgraph "Layer 1: Network Security"
        L1A[Firewall Rules]
        L1B[DDoS Protection]
        L1C[IP Whitelisting]
        L1D[VPN Access]
    end
    
    subgraph "Layer 2: Transport Security"
        L2A[TLS 1.3 Encryption]
        L2B[Certificate Management]
        L2C[HSTS Headers]
        L2D[Perfect Forward Secrecy]
    end
    
    subgraph "Layer 3: Application Security"
        L3A[Authentication]
        L3B[Authorization RBAC]
        L3C[Input Validation]
        L3D[Output Encoding]
    end
    
    subgraph "Layer 4: Data Security"
        L4A[Encryption at Rest]
        L4B[Field-level Encryption]
        L4C[Secure Key Management]
        L4D[Data Classification]
    end
    
    subgraph "Layer 5: Infrastructure Security"
        L5A[Container Security]
        L5B[Secrets Management]
        L5C[Vulnerability Scanning]
        L5D[Security Monitoring]
    end
    
    L1A --> L2A
    L1B --> L2B
    L2A --> L3A
    L2B --> L3B
    L3A --> L4A
    L3B --> L4B
    L4A --> L5A
    L4B --> L5B
```

## Performance and Scaling Diagrams

### 11. Horizontal Scaling Architecture
```mermaid
graph TB
    subgraph "Load Distribution"
        CDN[CDN Global Edge]
        LB[Load Balancer]
        HPA[Horizontal Pod Autoscaler]
    end
    
    subgraph "Application Scaling"
        subgraph "Content Manager"
            CM1[Instance 1]
            CM2[Instance 2]
            CM3[Instance N]
        end
        
        subgraph "AI Processor"
            AI1[GPU Instance 1]
            AI2[CPU Instance 1]
            AI3[CPU Instance 2]
        end
        
        subgraph "Distributor"
            D1[Instance 1]
            D2[Instance 2]
        end
    end
    
    subgraph "Data Scaling"
        subgraph "Database"
            DB_PRIMARY[(Primary)]
            DB_REPLICA1[(Read Replica 1)]
            DB_REPLICA2[(Read Replica 2)]
        end
        
        subgraph "Cache"
            REDIS1{{Redis Node 1}}
            REDIS2{{Redis Node 2}}
            REDIS3{{Redis Node 3}}
        end
        
        subgraph "Storage"
            S3_1[(Storage Node 1)]
            S3_2[(Storage Node 2)]
            S3_N[(Storage Node N)]
        end
    end
    
    CDN --> LB
    LB --> HPA
    HPA --> CM1
    HPA --> CM2
    HPA --> CM3
    
    HPA --> AI1
    HPA --> AI2
    HPA --> AI3
    
    HPA --> D1
    HPA --> D2
    
    CM1 --> DB_PRIMARY
    CM2 --> DB_REPLICA1
    CM3 --> DB_REPLICA2
    
    CM1 --> REDIS1
    CM2 --> REDIS2
    CM3 --> REDIS3
    
    D1 --> S3_1
    D2 --> S3_2
```

### 12. Caching Strategy
```mermaid
graph LR
    subgraph "Request Flow"
        CLIENT[Client Request]
        CDN[CDN Cache<br/>Global Edge]
        NGINX[Nginx Cache<br/>Reverse Proxy]
        APP[Application<br/>Memory Cache]
        REDIS[Redis Cache<br/>Distributed]
        DB[(Database)]
    end
    
    CLIENT --> CDN
    CDN -->|Cache Miss| NGINX
    NGINX -->|Cache Miss| APP
    APP -->|Cache Miss| REDIS
    REDIS -->|Cache Miss| DB
    
    DB -->|Data| REDIS
    REDIS -->|Data| APP
    APP -->|Response| NGINX
    NGINX -->|Response| CDN
    CDN -->|Response| CLIENT
    
    subgraph "Cache Hierarchy"
        L1[L1: Browser Cache<br/>TTL: 5-60 min]
        L2[L2: CDN Cache<br/>TTL: 1-24 hours]
        L3[L3: Nginx Cache<br/>TTL: 5-30 min]
        L4[L4: App Memory<br/>TTL: 1-10 min]
        L5[L5: Redis<br/>TTL: 10-60 min]
        L6[L6: Database<br/>Source of Truth]
    end
```

## Data Flow Diagrams

### 13. Content Generation Pipeline
```mermaid
graph TB
    subgraph "Input Sources"
        A[Web Scraping]
        B[User Input]
        C[Airtable CMS]
        D[API Imports]
    end
    
    subgraph "Data Processing"
        E[Content Validation]
        F[Data Cleaning]
        G[Deduplication]
        H[Quality Analysis]
    end
    
    subgraph "AI Processing"
        I[Content Analysis]
        J[Topic Extraction]
        K[AI Generation]
        L[Quality Validation]
    end
    
    subgraph "Content Enhancement"
        M[SEO Optimization]
        N[Brand Alignment]
        O[Readability Check]
        P[Template Application]
    end
    
    subgraph "Distribution Preparation"
        Q[Newsletter Format]
        R[Social Media Format]
        S[Email Personalization]
        T[Scheduling]
    end
    
    subgraph "Output Channels"
        U[Email Delivery]
        V[Instagram Publishing]
        W[Website Updates]
        X[API Endpoints]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    
    E --> F
    F --> G
    G --> H
    
    H --> I
    I --> J
    J --> K
    K --> L
    
    L --> M
    M --> N
    N --> O
    O --> P
    
    P --> Q
    P --> R
    Q --> S
    R --> S
    S --> T
    
    T --> U
    T --> V
    T --> W
    T --> X
```

### 14. Newsletter Distribution Flow
```mermaid
graph TB
    subgraph "Content Preparation"
        A[Select Content]
        B[Apply Template]
        C[Personalization]
        D[A/B Test Setup]
    end
    
    subgraph "Audience Segmentation"
        E[Fetch Subscribers]
        F[Apply Segments]
        G[Preference Filtering]
        H[GDPR Compliance Check]
    end
    
    subgraph "Delivery Pipeline"
        I[Queue Generation]
        J[Rate Limiting]
        K[Send via SendGrid]
        L[Delivery Tracking]
    end
    
    subgraph "Analytics & Feedback"
        M[Open Tracking]
        N[Click Tracking]
        O[Unsubscribe Handling]
        P[Bounce Processing]
    end
    
    A --> B
    B --> C
    C --> D
    
    E --> F
    F --> G
    G --> H
    
    D --> I
    H --> I
    I --> J
    J --> K
    K --> L
    
    L --> M
    M --> N
    N --> O
    O --> P
```

## Deployment Architecture Diagrams

### 15. CI/CD Pipeline
```mermaid
graph LR
    subgraph "Development"
        A[Developer Commits]
        B[Feature Branch]
        C[Pull Request]
    end
    
    subgraph "CI Pipeline"
        D[Code Analysis]
        E[Unit Tests]
        F[Integration Tests]
        G[Security Scan]
        H[Build Images]
    end
    
    subgraph "CD Pipeline"
        I[Deploy to Staging]
        J[E2E Tests]
        K[Performance Tests]
        L[Approval Gate]
        M[Deploy to Production]
    end
    
    subgraph "Monitoring"
        N[Health Checks]
        O[Performance Monitoring]
        P[Error Tracking]
        Q[Rollback Trigger]
    end
    
    A --> B
    B --> C
    C --> D
    
    D --> E
    E --> F
    F --> G
    G --> H
    
    H --> I
    I --> J
    J --> K
    K --> L
    L --> M
    
    M --> N
    N --> O
    O --> P
    P --> Q
    Q -.->|If Issues| M
```

### 16. Multi-Environment Architecture
```mermaid
graph TB
    subgraph "Development Environment"
        DEV_LB[Local Docker Compose]
        DEV_APPS[All Services<br/>Single Host]
        DEV_DB[(Local PostgreSQL)]
        DEV_CACHE[(Local Redis)]
    end
    
    subgraph "Staging Environment"
        STAGE_LB[Load Balancer]
        STAGE_APPS[Application Services<br/>Docker Swarm]
        STAGE_DB[(PostgreSQL Primary)]
        STAGE_DB_R[(PostgreSQL Replica)]
        STAGE_CACHE[(Redis Cluster)]
        STAGE_MON[Basic Monitoring]
    end
    
    subgraph "Production Environment"
        PROD_CDN[CDN + WAF]
        PROD_LB[Multi-Zone Load Balancer]
        
        subgraph "Kubernetes Cluster"
            PROD_APPS[Microservices<br/>Auto-scaling Pods]
            PROD_MON[Full Monitoring Stack]
        end
        
        subgraph "Data Layer - Multi-Zone"
            PROD_DB[(PostgreSQL HA<br/>Multi-Zone)]
            PROD_CACHE[(Redis HA<br/>Multi-Zone)]
            PROD_STORAGE[(Object Storage<br/>Multi-Zone)]
        end
    end
    
    DEV_APPS --> DEV_DB
    DEV_APPS --> DEV_CACHE
    
    STAGE_LB --> STAGE_APPS
    STAGE_APPS --> STAGE_DB
    STAGE_APPS --> STAGE_DB_R
    STAGE_APPS --> STAGE_CACHE
    
    PROD_CDN --> PROD_LB
    PROD_LB --> PROD_APPS
    PROD_APPS --> PROD_DB
    PROD_APPS --> PROD_CACHE
    PROD_APPS --> PROD_STORAGE
    
    classDef dev fill:#e8f5e8
    classDef staging fill:#fff3e0
    classDef prod fill:#ffebee
    
    class DEV_LB,DEV_APPS,DEV_DB,DEV_CACHE dev
    class STAGE_LB,STAGE_APPS,STAGE_DB,STAGE_DB_R,STAGE_CACHE,STAGE_MON staging
    class PROD_CDN,PROD_LB,PROD_APPS,PROD_MON,PROD_DB,PROD_CACHE,PROD_STORAGE prod
```

### 17. Monitoring and Observability Architecture
```mermaid
graph TB
    subgraph "Data Collection Layer"
        A[Application Metrics]
        B[Infrastructure Metrics]
        C[Application Logs]
        D[Infrastructure Logs]
        E[Distributed Traces]
        F[Custom Events]
    end
    
    subgraph "Collection Agents"
        G[Prometheus Exporters]
        H[Node Exporter]
        I[Promtail]
        J[Fluentd]
        K[OpenTelemetry Collector]
        L[Custom Collectors]
    end
    
    subgraph "Storage & Processing"
        M[Prometheus TSDB]
        N[Loki Log Storage]
        O[Jaeger Traces]
        P[InfluxDB (Custom)]
    end
    
    subgraph "Visualization & Alerting"
        Q[Grafana Dashboards]
        R[AlertManager]
        S[Custom Dashboards]
        T[Alert Channels]
    end
    
    subgraph "External Integrations"
        U[Slack Notifications]
        V[PagerDuty]
        W[Email Alerts]
        X[Webhook Endpoints]
    end
    
    A --> G
    B --> H
    C --> I
    D --> J
    E --> K
    F --> L
    
    G --> M
    H --> M
    I --> N
    J --> N
    K --> O
    L --> P
    
    M --> Q
    N --> Q
    O --> Q
    P --> S
    
    M --> R
    R --> T
    
    T --> U
    T --> V
    T --> W
    T --> X
```

This comprehensive collection of technical diagrams provides visual documentation for all aspects of the AquaScene Content Engine architecture, enabling teams to understand system design, data flows, and operational patterns at both high and detailed levels.