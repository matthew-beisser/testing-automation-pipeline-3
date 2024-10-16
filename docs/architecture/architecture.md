# Testing Automation Pipeline Software Architecture

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Table of Contents](#table-of-contents)
- [The Format](#the-format)
- [Static Architecture](#static-architecture)
  - [System Overview](#system-overview)
  - [Sequence Diagram](#sequence-diagram)

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

### Sequence Diagram

```mermaid
sequenceDiagram
    autonumber

    Participant Jama
    Participant WS as Wireshark CLI
    Participant DFT as DFT (DOIP) CLI
    Participant Lidar
    Participant Valk as Valkyrie
    Participant DB as Database
    Participant FS as File System
    Participant PConvert as pcap Converter
    Participant TE as Target Extraction

    Valk->>Jama: Work Item ID (Rest API)
    Jama->>Valk: TBD Data (.json)
    Valk->>Valk: Select Test (GUI)
    
    Valk->>DFT: Launch  

    Valk->>Lidar: Start Test (???)

    par Record DOIP data
        loop Until test completes
            DFT->>Lidar: DOIP Read Parameter
            Lidar->>DFT: DOIP Response
            DFT->>DB: Event Data (Key/Value (binary))
        end
    and Record Pointcloud
        loop Until test completes
            Valk->>WS: Start capture
            Valk->>FS: Write pcap metadata file (.json)
            
            loop
                Lidar->>WS: Pointcloud data (udp packet)
                WS->>FS: write pcap file (.pcap)
            end

            WS->>Valk: pcap capture done
            Valk->>PConvert: Trigger pcap to csv conversion (csv name)
            TE->>DB: Results (TBD)
        end
    end
```
