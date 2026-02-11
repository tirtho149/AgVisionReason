# Agentic Classification Flow

## Simple Version

```mermaid
flowchart LR
    A[Input Image] --> B[Agent]
    B --> C[Read Symptoms]
    C --> D[View Image]
    D --> E[Compare & Reason]
    E --> F{Confident?}
    F -->|No| G[View Reference Images]
    G --> E
    F -->|Yes| H[Prediction]
```

## Detailed Version

```mermaid
flowchart TB
    subgraph Input
        I1[Test Image Path]
        I2[Expected Classes]
        I3[Dataset Description]
    end

    subgraph Agent["Claude Code Agent (Haiku)"]
        direction TB

        subgraph Step1["Step 1: Load Knowledge"]
            S1A[Read disease_symptoms.md]
            S1B[Parse symptom descriptions]
            S1C[Note reference image paths]
        end

        subgraph Step2["Step 2: Analyze Target"]
            S2A[View test image]
            S2B[Identify visual features]
            S2C[Note pustules, colors, patterns]
        end

        subgraph Step3["Step 3: Compare & Match"]
            S3A[Match features to symptoms]
            S3B[Rank likely classes]
            S3C{Confident?}
        end

        subgraph Step4["Step 4: Verify (Optional)"]
            S4A[View reference images]
            S4B[Compare side-by-side]
            S4C[Refine prediction]
        end
    end

    subgraph Output
        O1[Prediction JSON]
        O2[Reasoning Log]
    end

    I1 --> S2A
    I2 --> S3A
    I3 --> S1A

    S1A --> S1B --> S1C
    S2A --> S2B --> S2C
    S1C --> S3A
    S2C --> S3A
    S3A --> S3B --> S3C

    S3C -->|No| S4A
    S4A --> S4B --> S4C --> S3B

    S3C -->|Yes| O1
    S3B --> O2
```

## Prompt Structure

```mermaid
flowchart TB
    subgraph Prompt["Agent Prompt"]
        P1["<b>ROLE</b><br/>Plant disease classification agent"]
        P2["<b>CONTEXT</b><br/>Dataset: Yellow Rust Severity Levels<br/>Classes: [Resistant_R, MR, MRMS, MS, Susceptible_S]"]
        P3["<b>TASK</b><br/>Classify image at: /path/to/test_001.jpg"]
        P4["<b>INSTRUCTIONS</b><br/>1. Read knowledge base<br/>2. View target image<br/>3. Compare to symptoms<br/>4. View reference images if uncertain<br/>5. Make prediction"]
        P5["<b>OUTPUT FORMAT</b><br/>{prediction: class_name}"]
    end

    P1 --> P2 --> P3 --> P4 --> P5
```

## Tool Usage Flow

```mermaid
sequenceDiagram
    participant User
    participant Agent as Claude Agent
    participant Read as Read Tool
    participant FS as File System

    User->>Agent: Classify test_001.jpg

    Note over Agent: Step 1: Load Knowledge
    Agent->>Read: Read disease_symptoms.md
    Read->>FS: Load file
    FS-->>Read: Symptom descriptions + reference paths
    Read-->>Agent: Knowledge base content

    Note over Agent: Step 2: View Target
    Agent->>Read: Read test_001.jpg
    Read->>FS: Load image
    FS-->>Read: Image data
    Read-->>Agent: Visual content

    Note over Agent: Step 3: Initial Analysis
    Agent->>Agent: Compare features to symptoms
    Agent->>Agent: Narrow to 2-3 candidate classes

    Note over Agent: Step 4: Verify with References
    loop For each candidate class
        Agent->>Read: Read reference_image.jpg
        Read->>FS: Load image
        FS-->>Read: Image data
        Read-->>Agent: Reference visual
        Agent->>Agent: Compare to test image
    end

    Note over Agent: Step 5: Final Decision
    Agent-->>User: {"prediction": "Moderately_Susceptible_MS"}
```

## Baseline vs Agent Comparison

```mermaid
flowchart LR
    subgraph Baseline["Baseline (API Only)"]
        B1[Image] --> B2[Claude API]
        B2 --> B3[Prediction]
    end

    subgraph Agent["Agent (Claude Code)"]
        A1[Image] --> A2[Claude Code]
        A2 --> A3[Read Symptoms]
        A3 --> A4[View Image]
        A4 --> A5[View References]
        A5 --> A6[Reason]
        A6 --> A7[Prediction]
    end

    style Baseline fill:#ffcccc
    style Agent fill:#ccffcc
```

| Aspect | Baseline | Agent |
|--------|----------|-------|
| Knowledge | None (zero-shot) | Symptoms + Reference Images |
| Tool Access | No | Read tool |
| Reasoning | Single inference | Multi-step with verification |
| Adaptability | Fixed prompt | Dynamic exploration |
