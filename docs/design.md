# Testing Automation Pipeline System Design

Last Updated: 2024-mm-dd

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Testing Automation Pipeline System Design](#testing-automation-pipeline-system-design)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Context](#context)
  - [Goals and Non-Goals](#goals-and-non-goals)
  - [Milestones](#milestones)
  - [Existing Solution](#existing-solution)
    - [Entities](#entities)
      - [Jira](#jira)
      - [Valkyrie Workstation](#valkyrie-workstation)
      - [NFS File Storage](#nfs-file-storage)
        - [PCAP Naming Convention](#pcap-naming-convention)
      - [Lidar](#lidar)
    - [Data Collection](#data-collection)
    - [Data Processing](#data-processing)
  - [Proposed Solution](#proposed-solution)
    - [Entities](#entities-1)
  - [Cross-Team Impact](#cross-team-impact)
  - [Open Questions](#open-questions)
  - [Detailed Scoping and Timeline](#detailed-scoping-and-timeline)

<!-- mdformat-toc end -->

<!-- https://www.freecodecamp.org/news/how-to-write-a-good-software-design-document-66fcf019569c/ -->

## Overview

<!--
A high level summary that every engineer at the company should understand and use to decide if it’s useful for them to read the rest of the doc. It should be 3 paragraphs max.
-->

Functional testing (FT) monitors a lidar's performance and functionality under various conditions and different lengths of time.
Three different types of FT testing (FT1, FT2, and FT3) is performed by the Product Assurance Teams on batches of sensors.

This document describes the current [FT2 process](https://luminartech.sharepoint.com/:p:/s/SharedFiles/EQHOJNqx7GxIuGgJ0OetWdwBdkQNoR8Q46KQb3aKOsfmQg?e=C4qzhl) as well as the proposed automation for parts of this process. 

## Context

<!-- 
A description of the problem at hand, why this project is necessary, what people need to know to assess this project, and how it fits into the technical strategy, product strategy, or the team’s quarterly goals.
-->

The Product Assurance Team has automated several of the individual steps required for FT2 testing.
These individual automation steps have allowed the team to put together their current semi-automated process.

The current FT2 process relies upon a series of steps requiring users to input file names, copy files to various locations, trigger data analysis, and extract and manipulate data from .csv files to produce reports. 
All of these steps are prone to user error which causes delays.
Perhaps more importantly though, the ability to view the test data over time against KPIs as well as interogating the report analysis is lacking. This makes trend analysis of sensor issues not possible without investing an extradorinary amount of time.

The proposed software solution is to 

The complete automation of the FT2 process is not currently feasible.
A test engineer will still be required even with the proposed automation solution.

The proposed FT2 automation steps will address:
- Test output files not being transfered
- Storing sensor test output in a commonly accessible and searchable way
- Automatic triggering of data analysis (target extraction)
- Storing target extraction results in a commonly accessible and searchable way
- Reducing the time required for analysis and report creation
- The lack of dashboards for viewing data against KPIs


## Goals and Non-Goals

<!--
The Goals section should:

    describe the user-driven impact of your project — where your user might be another engineering team or even another technical system
    specify how to measure success using metrics — bonus points if you can link to a dashboard that tracks those metrics

Non-Goals are equally important to describe which problems you won’t be fixing so everyone is on the same page.
-->

## Milestones

<!-- 
A list of measurable checkpoints, so your PM and your manager’s manager can skim it and know roughly when different parts of the project will be done. I encourage you to break the project down into major user-facing milestones if the project is more than 1 month long.

Use calendar dates so you take into account unrelated delays, vacations, meetings, and so on. It should look something like this:

Start Date: June 7, 2018
Milestone 1 — New system MVP running in dark-mode: June 28, 2018
Milestone 2 - Retire old system: July 4th, 2018
End Date: Add feature X, Y, Z to new system: July 14th, 2018

Add an [Update] subsection here if the ETA of some of these milestone changes, so the stakeholders can easily see the most up-to-date estimates.
-->
FTD open telemetry tracing complete
Distributed Tracing Solution (Jaeggar, Grafana Loki, etc) tested and choosen
  - Corresponding database selected


## Existing Solution

### Entities

#### Jira

A Jira board is used along with epics, stories, and tasks to track the current testing tasks.

An epic is used to track a batch of sensor to test, e.g. [Iris Slim V1- PV (70-0025007/008)](https://luminartech.atlassian.net/browse/TV-5628)

Stories are used to group tasks in an adhoc manner. E.g. [PV: Leg1 ReTest_PV1-002753](https://luminartech.atlassian.net/browse/TV-8426)

Tasks (not currently linked to epics) are used to track a certain type of test result for multiple sensors.
A single sensor's test completion is tracked as a comment. E.g. [PV Retest Leg 1 FT1 Data Collection - Post FW Update](https://luminartech.atlassian.net/browse/TV-8763)

#### Valkyrie Workstation

A Windows workstation running the Valkyrie (Labview) software.  
Valykrie is a GUI that allows operators to select and run various tests for a sensor.  
The output of these tests, currently telnet .csv and point cloud .pcap captures, are stored on the NFS.  

#### NFS File Storage

A common network file share (NFS) used to store output test data before it is processed.

The current base location for FT2 data is: `\\mco1-fs03\Workgroups\validation-data\`

Example output location: `Iris_Sensor_Head_70-0025-010\P32406697T00003188VAE7E3\`

```
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

##### PCAP Naming Convention

PCAP files are automatically captured by [Valkyrie](#valkyrie-workstation) at various points in the testing.
The output file name is based upon the test parameters. E.g. `282_200m_28fov_n4offs_n60_LO123_1_00002_20220428101251.pcap`

#### Lidar

The Iris, Iris+, or Halo (future) sensor under test.

### Data Collection

The existing data collection portion of the FT2 testing is shown in the diagram below.

![system_context_diagram](architecture/views/container_diagram_existing_data_collection.svg)

### Data Processing

<!-- 
In addition to describing the current implementation, you should also walk through a high level example flow to illustrate how users interact with this system and/or how data flow through it.

A user story is a great way to frame this. Keep in mind that your system might have different types of users with different use cases.
-->



## Proposed Solution

### Entities
<!--
Some people call this the Technical Architecture section. Again, try to walk through a user story to concretize this. Feel free to include many sub-sections and diagrams.

Provide a big picture first, then fill in lots of details. Aim for a world where you can write this, then take a vacation on some deserted island, and another engineer on the team can just read it and implement the solution as you described.
Alternative Solutions

What else did you consider when coming up with the solution above? What are the pros and cons of the alternatives? Have you considered buying a 3rd-party solution — or using an open source one — that solves this problem as opposed to building your own?
Testability, Monitoring and Alerting

I like including this section, because people often treat this as an afterthought or skip it all together, and it almost always comes back to bite them later when things break and they have no idea how or why.
-->

## Cross-Team Impact

<!--
How will this increase on call and dev-ops burden?
How much money will it cost?
Does it cause any latency regression to the system?
Does it expose any security vulnerabilities?
What are some negative consequences and side effects?
How might the support team communicate this to the customers?
-->

## Open Questions

<!--
Any open issues that you aren’t sure about, contentious decisions that you’d like readers to weigh in on, suggested future work, and so on. A tongue-in-cheek name for this section is the “known unknowns”.
-->



## Detailed Scoping and Timeline

<!--
This section is mostly going to be read only by the engineers working on this project, their tech leads, and their managers. Hence this section is at the end of the doc.

Essentially, this is the breakdown of how and when you plan on executing each part of the project. There’s a lot that goes into scoping accurately, so you can read this post to learn more about scoping.

I tend to also treat this section of the design doc as an ongoing project task tracker, so I update this whenever my scoping estimate changes. But that’s more of a personal preference.
-->