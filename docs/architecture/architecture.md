# Testing Automation Pipeline Software Architecture

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Table of Contents](#table-of-contents)
- [The Format](#the-format)
- [Static Architecture](#static-architecture)
  - [System Overview](#system-overview)
    - [Data Collection](#data-collection)
    - [Data Transfer](#data-transfer)

<!-- mdformat-toc end -->

## The Format

We are following the C4Model. This means we view the Context, Container, Components and Code.
For more information about it check out the video on the [C4 Model Website](https://c4model.com).

## Static Architecture

### System Overview

<!--
The proposed system level diagram the FT2 automation testing is shown in the diagram below.

![system_context_diagram](architecture/views/system_context_diagram.svg)

### Proposed Data Collection

The proposed data collection process for the FT2 automation testing is shown in the diagram below.

![container_diagram_proposal_data_collection](architecture/views/container_diagram_proposal_data_collection.svg)

### Proposed Data Processing

The proposed data processing for the FT2 automation testing is shown in the diagram below.

![container_diagram_proposal_data_processing](architecture/views/container_diagram_proposal_data_processing.svg)
-->

#### Data Collection

```mermaid
%%{
    init: {'theme': 'neutral' }
}%%

sequenceDiagram
    autonumber

    Participant Jama
    Participant WS as Wireshark CLI
    Participant DFT as DFT (doip) CLI
    Participant Lidar
    Participant Valk as Valkyrie
    Participant DB as Local Database
    Participant FS as Local File System
    Participant PConvert as Pcap Converter
    Participant TE as Target Extraction

    Valk->>Valk: Enter work item id
    Valk->>Jama: Work item ID (Rest API)
    Jama->>Valk: TBD Data (.json)
    Valk->>Valk: Select Test (GUI)
    
    Valk->>DFT: Launch  

    Valk->>Lidar: Start Test (???)

    par Record doip data
        loop 
            DFT->>Lidar: Read parameter (doip)
            Lidar->>DFT: Parameter data (doip)
            DFT->>DB: Parameter Data (sql - Key/Binary data)
        end
        Valk->>DFT: End task
        DFT-->>Valk: Done
    and Record point cloud
        loop 
            Valk->>WS: Start network capture
            Valk->>FS: Write pcap metadata file (.json)
            
            loop
                Lidar->>WS: Point cloud data (udp)
                WS->>FS: Write pcap file (.pcap)
            end

            Valk->>WS: End task - pcap capture
            WS-->>Valk: Done
            Valk->>PConvert: Trigger pcap conversion (pcap name)
            PConvert->>FS: Retrieve pcap
            FS-->>PConvert: 
            PConvert->>PConvert: Convert pcap
            PConvert-->>Valk: Done
            Valk->>TE: Trigger extraction
            TE->>DB: Results (TBD)
            TE-->>Valk: Done
        end
    end
```

#### Data Transfer

**Daemon with message queue**

```mermaid
%%{
    init: {'theme': 'neutral' }
}%%

sequenceDiagram
    autonumber

    Participant DS as Incoming Data
    Participant DB as Database
    Participant FS as File System
    Participant Daemon as Data Translate Daemon
    Participant Prod as Message Producer
    Participant Cons as Message Consumer
    Participant CloudDB as Cloud Database
    Participant CloudFS as Cloud File System

    loop
        par Record parameter data
            DS->>DB: doip data (sql - Key/Binary data)
        and Record pcap data
            DS->>FS: pcap metadata file (.json)
            DS->>FS: pcap file (.pcap)
        end
    end

    loop
        par Transfer pcap file
            Daemon->>FS: Retrieve .pcap file
            FS-->>Daemon: 
            Daemon->>CloudFS: Copy .pcap file (magic transfer protocol)
            CloudFS-->>Daemon: 

            Daemon->>FS: Retrieve .pcap metadata file
            FS-->>Daemon: 
            Daemon->>Prod: .pcap metadata (.json)
            Prod->>Cons: .pcap metadata message (.json)
            Cons->>CloudDB: .pcap metadata (sql)
            CloudDB-->>Cons: 
            Cons-->>Prod: 
            Prod-->>Daemon: 
        and Transfer doip parameter data`
            Daemon->>DB: Request doip data (sql)
            DB-->>Daemon: 
            Daemon->>Prod: doip data (.json)
            Prod->>Cons: doip data message (.json)
            Cons->>CloudDB: doip data (sql)
            CloudDB-->>Cons: 
            Cons-->>Prod: 
            Prod-->>Daemon:             
        end
    end
```

**Daemon with direct remote db access**

```mermaid
sequenceDiagram
    autonumber

    Participant DS as Incoming Data
    Participant DB as Database
    Participant FS as File System
    Participant Daemon as Data Translate Daemon

    %%Participant Prod as Message Producer
    %%Participant Cons as Message Consumer

    Participant CloudDB as Cloud Database
    Participant CloudFS as Cloud File System

    loop
        par Record parameter data
            DS->>DB: doip data (sql - Key/Binary data)
        and Record pcap data
            DS->>FS: pcap metadata file (.json)
            DS->>FS: pcap file (.pcap)
        end
    end

    loop
        par Transfer pcap file
            Daemon->>FS: Retrieve .pcap file
            FS-->>Daemon: 
            Daemon->>CloudFS: Copy .pcap file (magic transfer protocol)
            CloudFS-->>Daemon: 
            Daemon-->>FS: Write copy complete file

            Daemon->>FS: Retrieve .pcap metadata file
            FS-->>Daemon: 
            Daemon->>CloudDB: .pcap metadata (sql)
            CloudDB-->>Daemon: 
            Daemon-->>FS: Write metadata processed file

        and Transfer doip parameter data
            Daemon->>DB: Request doip data (sql)
            DB-->>Daemon: 
            Daemon->>CloudDB: doip data (sql)
            CloudDB-->>DB: Mark processed (sql)
        end
    end
```
