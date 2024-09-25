# Testing Automation Pipeline System Design

Last Updated: 2024-mm-dd

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Table of Contents](#table-of-contents)
- [Document Notes](#document-notes)
- [Overview](#overview)
- [Context](#context)
- [Goals](#goals)
- [Non-Goals](#non-goals)
- [Milestones](#milestones)
- [Existing Solution](#existing-solution)
  - [Existing Entities](#existing-entities)
    - [Data Analysis (Target Extraction - Matlab)](#data-analysis-target-extraction---matlab)
    - [Jira](#jira)
    - [Lidar](#lidar)
    - [NFS File Storage](#nfs-file-storage)
    - [Valkyrie Workstation](#valkyrie-workstation)
      - [PCAP Naming Convention](#pcap-naming-convention)
  - [Existing Data Collection](#existing-data-collection)
  - [Existing Data Processing](#existing-data-processing)
- [Proposed Solution](#proposed-solution)
  - [Proposed Entities](#proposed-entities)
    - [Database](#database)
    - [Data Compilation (TBD)](#data-compilation-tbd)
    - [Data Analysis](#data-analysis)
    - [Diagnostics and Flashing Tool (DFT)](#diagnostics-and-flashing-tool-dft)
    - [File Monitor](#file-monitor)
    - [Front End](#front-end)
    - [Jira (Existing)](#jira-existing)
    - [NAS (File Storage - Existing)](#nas-file-storage---existing)
    - [OpenTelemetry Collector](#opentelemetry-collector)
    - [Pcap Recorder (Replacement)](#pcap-recorder-replacement)
    - [Valkyrie Workstation (Existing)](#valkyrie-workstation-existing)
  - [System Overview](#system-overview)
  - [Proposed Data Collection](#proposed-data-collection)
  - [Proposed Data Processing](#proposed-data-processing)
- [Alternative Solutions](#alternative-solutions)
- [Cross-Team Impact](#cross-team-impact)
- [Open Questions](#open-questions)
- [Detailed Scoping and Timeline](#detailed-scoping-and-timeline)

<!-- mdformat-toc end -->

<!-- 
Document template taken from:
https://www.freecodecamp.org/news/how-to-write-a-good-software-design-document-66fcf019569c/
-->

## Document Notes

The software architecture diagrams in this document use the [C4 model](https://c4model.com/).
See [here](https://youtu.be/x2-rSnhpw0g) for a brief tutorial.

## Overview

<!--
A high level summary that every engineer at the company should understand and use to decide if it's useful for them to read the rest of the doc. It should be 3 paragraphs max.
-->

An integral step in the manufacturing of lidar is ensuring they perform to the system requirements.
While each sensor at a manufacturing facility undergoes a series of tests before leaving that facility, it's necessary to perform more robust testing to ensure no sensor performance degredation occurs over time.
This extra step, referred to as parameter testing (and monitoring), involves adjusting inputs to the sensor within certain boundaries.
The goal is to observe the sensor's output and confirm it operates as anticipated under the varied conditions.

The System Test Team is responsible for performing these additional tests on select batches of sensors.
Note that there are different levels of parameter testing.
These can range from comprehensive testing that covers system-level requirements, to more limited testing that focuses on a subset of these parameters, or even continuous monitoring of certain intrinsic parameters during operation.

The 3 different type of parameter test defintions for Iris and Iris+ is shown in the table below.

|                                     Iris (VCC) Test ID                                     | Description for Iris | Iris+ (MB) Test ID |   Description for Iris+ | Luminar Test ID |             Luminar Description              |
| :----------------------------------------------------------------------------------------: | :------------------: | :----------------: | ----------------------: | :-------------: | :------------------------------------------: |
| [FT1](https://luminar.jamacloud.com/perspective.req#/testPlans/2252407/home/?projectId=87) |  Functional Test 1   |        P02         | Parameter Testing Small |       FPT       |    Functional Parameter Testing (Limited)    |
| [FT2](https://luminar.jamacloud.com/perspective.req#/testPlans/1824961/home/?projectId=87) |  Functional Test 2   |        P03         | Parameter Testing Large |       APT       | Acceptance Parameter Testing (Comprehensive) |
| [FT3](https://luminar.jamacloud.com/perspective.req#/testPlans/2319205/home/?projectId=87) |  Functional Test 3   |        P01         |   Continuous Monitoring |       CPM       |       Continuous Parameter Monitoring        |

While the exact specifications of these tests are outside the scope of this document (though details can be found [here](https://luminartech.sharepoint.com/:p:/s/SharedFiles/EQHOJNqx7GxIuGgJ0OetWdwBdkQNoR8Q46KQb3aKOsfmQg?e=C4qzhl))
the testing process, how test engineers collect data, and how that process can be automated is the focus of this design.

**It is important to note that this automated process is required as part of the transition of manufacturing to TPK(?) in 2025/2026.**

## Context

<!-- 
A description of the problem at hand, why this project is necessary, what people need to know to assess this project, and how it fits into the technical strategy, product strategy, or the team's quarterly goals.
-->

This document describes the current [FT2 process](https://luminartech.sharepoint.com/:p:/s/SharedFiles/EQHOJNqx7GxIuGgJ0OetWdwBdkQNoR8Q46KQb3aKOsfmQg?e=C4qzhl) as well as the proposed automation for parts of this process.

The complete automation of the FT2 process is outside the scope of this design, and a test engineer will still be required.

It is understood that the FT2 automation process needs to be architectured in a manner that will allow the eventual support of additional test processes, i.e., FT1 and FT3 for Iris, as well as Iris+ (P01 - P03), and Halo.
However, for the purposes of this design, those additional test processes are considered out of scope.

The current FT2 process is a primarly manual process with a few automation steps built in for convenience.
It primarily consists of a series of steps requiring users to input file names, copy files to various locations, trigger data analysis for specific test runs, and extract and manipulate data from .csv files to produce reports.
These steps are prone to user error which causes delays.
Perhaps more importantly though, the ability to view the test data over time against KPIs as well as interogating the test data over time is lacking.
This makes the trend analysis of sensor parameter testing not possible without investing an extradorinary amount of time.

## Goals

The proposed FT2 solution will address:

- The manual processing of test output data
- Retrieving sensor diagnostics over DOIP
- Storing sensor test output in a commonly accessible and searchable way
- Automatic triggering of data analysis (target extraction)
- Porting the existing Matlab target extraction code to Python
- Storing target extraction results in a commonly accessible and searchable way
- Reducing the time required for analysis and report creation
- Providing dashboards for viewing data against KPIs
- The initial deployment and upgrade mechanisms for the software

<!--
The Goals section should:

    - describe the user-driven impact of your project — where your user might be another engineering team or even another technical system
    - specify how to measure success using metrics — bonus points if you can link to a dashboard that tracks those metrics
-->

## Non-Goals

<!--
Non-Goals are equally important to describe which problems you won't be fixing so everyone is on the same page.
-->

The proposed FT2 solution will intentionally **NOT** address:

- Fully automating FT2
- Processing telnet data in the existing workflow
- Replacing Valkyrie
- Upgrading Valkyrie

## Milestones

<!-- 
A list of measurable checkpoints, so your PM and your manager's manager can skim it and know roughly when different parts of the project will be done. I encourage you to break the project down into major user-facing milestones if the project is more than 1 month long.

Use calendar dates so you take into account unrelated delays, vacations, meetings, and so on. It should look something like this:

Start Date: June 7, 2018
Milestone 1 — New system MVP running in dark-mode: June 28, 2018
Milestone 2 - Retire old system: July 4th, 2018
End Date: Add feature X, Y, Z to new system: July 14th, 2018

Add an [Update] subsection here if the ETA of some of these milestone changes, so the stakeholders can easily see the most up-to-date estimates.
-->

- File outputs from tests
- FTD open telemetry tracing complete for VCC
- Docker Linux instance stood up
- Distributed Tracing Solution (Jaeggar, Grafana Loki, openobserve.ai, etc) tested and choosen
  - Corresponding database selected
- Matlab target extraction running with single pcap
  - Code ported to Python

## Existing Solution

<!-- 
In addition to describing the current implementation, you should also walk through a high level example flow to illustrate how users interact with this system and/or how data flow through it.

A user story is a great way to frame this. Keep in mind that your system might have different types of users with different use cases.
-->

### Existing Entities

#### Data Analysis (Target Extraction - Matlab)

\[External System\]

The data analysis is performed by a Matlab application which performs target extraction on the test pcaps.

Repository: [IrisDataTools](https://github.com/luminartech/IrisDataTools)

POC: Daniel Ferrone

**- Outstanding Questions**

- How can I run target extraction manually on a single pcap file?
- What are the outputs, how many are there, and how are they used in reporting? (Mehdi Chaouqi)

#### Jira

\[External System\]

A Jira board is used along with epics, stories, and tasks to track the current testing tasks.

An epic is used to track a batch of sensor to test, e.g. [Iris Slim V1 - PV (70-0025007/008)](https://luminartech.atlassian.net/browse/TV-5628)

Stories are used to group tasks in an adhoc manner, e.g. [PV: Leg1 ReTest_PV1-002753](https://luminartech.atlassian.net/browse/TV-8426)

Tasks (not currently linked to epics) are used to track a certain type of test result for multiple sensors.
A single sensor's test completion is tracked as a comment, e.g. [PV Retest Leg 1 FT1 Data Collection - Post FW Update](https://luminartech.atlassian.net/browse/TV-8763)

#### Lidar

\[External System\]

The Iris sensor under test. Iris+ and Halo support are [out of scope](#context) for the initial FT2 design.

#### NFS File Storage

\[External System\]

A common network file share (NFS) used to store output test data before it is processed.
It's a NAS that is accessible from all workstations.

The current base location for FT2 data is: `\\mco1-fs03\Workgroups\validation-data\`

Example output location: `Iris_Sensor_Head_70-0025-010\P32406697T00003188VAE7E3\`

```shell
Iris_Sensor_Head_XX-YYYY-ZZZ        - (XX-YYYY-ZZZ is the numeric sensor hardware pedigree) 
└── <Sensor Serial Number> 
    ├── FT2-Pre
    │   ├── Adams_YYYYMMDD_HHMM     - (near field station)
    │   ├── Eve_YYYYMMDD_HHMM       - (near field station)
    │   ├── Bishop_YYYYMMDD_HHMM    - (long range test facility)
    │   └── Skippy_YYYYMMDD_HHMM    - (long range test facility)
    └── FT2-Post
        └── <Same layout as FT2-Post>
```

#### Valkyrie Workstation

\[External System\]

A Windows workstation running the Valkyrie (Labview) software.
Valykrie is a GUI that allows operators to select and run various tests for a sensor.
The output of these tests, currently telnet .csv and point cloud .pcap captures, are stored on the NFS.

Valkyrie will be kept as part of the new process.

Repository: [SystemTestTools](https://github.com/luminartech/SystemTestTools)

POC: Jeff Hawkins

**- Outstanding Questions**

- How is Valkyrie going to be deployed as part of the solution?
  - What is the current update process?
- Can Valkyrie be integrated with the Jira REST API so ticket numbers can be sourced and test completion results written?
  - Seems like the answer is [yes](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z0000019VpgSAE&l=en-US), thought not sure on the level of effort.
- PCAP recording is currently done with Wireshark, is that going to be replaced with a homegrown app?
  - Is this in scope, and who will do this work?
  - Could we switch this to another cli tool like PyPCAPKit (Python package)?

##### PCAP Naming Convention

PCAP files are automatically captured by [Valkyrie](#valkyrie-workstation) at various points in the testing.
The output file name is based upon the test parameters. E.g. `282_200m_28fov_n4offs_n60_LO123_1_00002_20220428101251.pcap`

**- Outstanding Questions**

- The file names contain metadata that presumably is relevant to the data analysis phase.
  - Parsing these strings seems error prone and complicated.
    Can we write a pcap file with some basic identifiers in the name, but then store the metadata in a corresponding .csv or .json file?

### Existing Data Collection

The existing data collection process for the FT2 testing is shown in the diagram below.

![container_diagram_existing_data_collection](architecture/views/container_diagram_existing_data_collection.svg)

### Existing Data Processing

The existing data processing process for the FT2 testing is shown in the diagram below.

![container_diagram_existing_data_processing](architecture/views/container_diagram_existing_data_processing.svg)

## Proposed Solution

### Proposed Entities

#### Database

\[Internal\]

Backend storage for traces and target extraction results.

**- Outstanding Questions**

- What database to use for non tracing? PostgreSQL? MySQL (MariaDB)
- Are 2 databases going to be needed? 1 for traces, 1 for other data? Seems like yes.
  - If yes, should trace data be "transferred" to the other database in some way before/after target extraction? Maybe it doesn't matter as Grafana can have multiple data stores?

#### Data Compilation (TBD)

TBD

#### Data Analysis

\[Internal\]

Performs target extraction and stores results.
This Python code will replace the existing Matlab code.

**- Outstanding Questions**

- What is the estimated level of effort for this task?
- How many algorithms are being run today?
- How long does an analysis of a .pcap take?
- What do the outputs look like?

#### Diagnostics and Flashing Tool (DFT)

\[External\]

A command line tool for issuing diagnostics commands to a luminar sensor.
It replaces telnet and allows parameters to be read from the sensor via DOIP.

DFT uses OpenTelemetry spans as a way to measure the request and response time of a parameter over DOIP as well as recording the parameter's value.

OpenTelemetry provides a general-purpose API and schema for logs, metrics, and traces.

Logs are a time-ordered collection of discrete events, each of which contains a timestamp and some descriptive data.
They are often used for debugging or auditing purposes.
Logs can include any kind of data, such as error messages, information about the execution state, or user activities.
They are highly flexible but can be more difficult to analyze due to their unstructured nature.

Metrics are numerical values that represent the state of a system at a point in time.
They are typically used for quantitative analysis of system performance and health.
Metrics can be aggregated and analyzed over time to identify trends, spikes, or dips in system behavior.
Examples of metrics include CPU usage, memory consumption, network latency, or the number of active users.

A span represents a single unit of work within a system.
It encapsulates information about a specific operation, including its start time, duration, associated attributes, and any events or errors during its execution.

A trace is a collection of spans. They provide a detailed picture of a single operation or transaction as it flows through a distributed system.
A trace captures the entire journey of a request, including all the services it interacts with and how long each interaction takes.
Traces are essential for understanding the performance and behavior of complex, distributed systems.
They can help identify bottlenecks, failures, or unexpected behavior in a system.

Repository: [DFT](https://github.com/luminartech/dft)

POC: Zach Heylmun

**- Outstanding Questions**

- Are only traces being provided, or is there other data to ingest?
- There still seems to be a bit of work here by Zach in order to get is usable for testing.
  - Automate timing of read requests
  - Proof of concept for Mehdi
  - Common generate of DIDs (data identifiers)?
- How to integrate this tool with Valkyrie?

#### File Monitor

\[Internal\]

Monitors a directory on the NAS for new test data that needs to be processed.

Processing a test includes writing the .pcap metadata to the database, triggering the target extraction analysis, and performing any file cleanup or archiving.

**- Outstanding Questions**

- We should probably poll (once a minute) for tests to process.
- What signals the "end" of test data output so the monitor knows to trigger target extraction? A single file in the same directory?
- How is an interrupted test handled?
- Does a test need to be archived (i.e. zipped and moved?)

#### Front End

\[External\]

GUI allowing for two disparate activities.

1. View KPI data and export graphs
1. View / administer(?) the system status

Grafana seems like an obvious front end choice.

**- Outstanding Questions**

- Will Grafana be adequate? What other options are there?
- Is a cloud solution an option? Databricks is a cloud only.
- What data is currently being exported for graphs and diagrams today?

#### Jira (Existing)

[Jira](#jira)

#### NAS (File Storage - Existing)

\[Internal\]

[NFS File Storage](#nfs-file-storage)

**- Outstanding Questions**

- Who maintains this resource (backups, data transfers, etc) once manufacturing is moved?
- It's unclear where the NAS needs to exist in the entire solution.
- Could it host the databases and the Docker Container mount them?
- Is storing the pcaps necessary?
  - What should the storage layout be?
  - If so, what about backups, archiving, storing, database storage path, etc.

#### OpenTelemetry Collector

\[External\]

Open source or COTS solution to collect the spans emitted by \[#diagnostics-and-flashing-tool-(DFT)\] and store them in a database.

Current possible solution for storing and visualizing traces:

- Yaegar
  - Complicated. Needs storage or forwarding mechanism.
  - Supports: Cassandra, ElasticSearch
- OpenObserve
  - No external data connections
- Grafana Tempo
- Grafana Loki (for logs, not traces)
  - Single Store TSDB (indexed database)
  - File System

**- Outstanding Questions**

- How important is the visualization of the trace data?
- How do we tie the spans to the corresponding pcaps?
- What backend database is used?
  - It may not be possible to store the trace data and the target extraction analysis together (though that would be advantageous).
  - Do we need 2 database? And do we need to transform the trace data and then also put it into SQL database that will also house the target extraction data?
- Is a paid solution acceptable or possible here? Seems like no.

#### Pcap Recorder (Replacement)

\[External\]

This is a replacement for recording the .pcap test data with Wireshark.
It will still be executed by Valkyrie in some fashion.

The pcap file will no longer be written with metadata in the filename.

Instead the filename will be:

- Some combination of the name of the test run and a date timestamp.
- A metadata file name the same as above with a different extension.

**- Outstanding Questions**

- Why don't we want to use wireshark on the commandline? Perhaps because of installing the package?
- Does this just need to be a CLI tool?
- Can we use an existing python pcap library like PyPCAPKit? No need to reinvent the wheel.

#### Valkyrie Workstation (Existing)

[Valkyrie Workstation](#valkyrie-workstation)

<!-- End entities ----------------------------------------------------------------------------------------------------->

### System Overview

The proposed system level diagram the FT2 automation testing is shown in the diagram below.

![system_context_diagram](architecture/views/system_context_diagram.svg)

### Proposed Data Collection

The proposed data collection process for the FT2 automation testing is shown in the diagram below.

![container_diagram_proposal_data_collection](architecture/views/container_diagram_proposal_data_collection.svg)

### Proposed Data Processing

The proposed data processing for the FT2 automation testing is shown in the diagram below.

![container_diagram_proposal_data_processing](architecture/views/container_diagram_proposal_data_processing.svg)

<!--
The proposed data processing process for the FT2 testing is shown in the diagram below.

![system_context_diagram](architecture/views/container_diagram_existing_data_processing.svg)
-->

<!--
Some people call this the Technical Architecture section. Again, try to walk through a user story to concretize this. Feel free to include many sub-sections and diagrams.

Provide a big picture first, then fill in lots of details. Aim for a world where you can write this, then take a vacation on some deserted island, and another engineer on the team can just read it and implement the solution as you described.
-->

## Alternative Solutions

<!--
What else did you consider when coming up with the solution above? What are the pros and cons of the alternatives? Have you considered buying a 3rd-party solution — or using an open source one — that solves this problem as opposed to building your own?
Testability, Monitoring and Alerting

I like including this section, because people often treat this as an afterthought or skip it all together, and it almost always comes back to bite them later when things break and they have no idea how or why.
-->

## Cross-Team Impact

The biggest dependency on

<!--
- How will this increase on call and dev-ops burden?
- How much money will it cost?
- Does it cause any latency regression to the system?
- Does it expose any security vulnerabilities?
- What are some negative consequences and side effects?
- How might the support team communicate this to the customers?
-->

## Open Questions

<!--
Any open issues that you aren't sure about, contentious decisions that you'd like readers to weigh in on, suggested future work, and so on. A tongue-in-cheek name for this section is the “known unknowns”.
-->

- Is this project approved?
- How long and for what parts of the project am I committed?
- What's the desired start time for contractors?

## Detailed Scoping and Timeline

<!--
This section is mostly going to be read only by the engineers working on this project, their tech leads, and their managers. Hence this section is at the end of the doc.

Essentially, this is the breakdown of how and when you plan on executing each part of the project. There's a lot that goes into scoping accurately, so you can read this post to learn more about scoping.

I tend to also treat this section of the design doc as an ongoing project task tracker, so I update this whenever my scoping estimate changes. But that's more of a personal preference.
-->
