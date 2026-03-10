# Single Household Water Usage Simulation
## 📘 Complete Project Documentation & Simulation Guide
*CSE 10/L – Modeling and Simulation | University of Mindanao*

---

## 📌 Table of Contents
1. [Project Overview](#1-project-overview)
2. [Problem Description & Motivation](#2-problem-description--motivation)
3. [Objectives](#3-objectives)
4. [System Description](#4-system-description)
5. [Simulation Model Type & Justification](#5-simulation-model-type--justification)
6. [Simulation Variables](#6-simulation-variables)
7. [System Flow & Arena Modules](#7-system-flow--arena-modules)
8. [Assumptions](#8-assumptions)
9. [Simulation Setup & Run Parameters](#9-simulation-setup--run-parameters)
10. [Scenarios Tested](#10-scenarios-tested)
11. [Performance Measures](#11-performance-measures)
12. [Results Interpretation](#12-results-interpretation)
13. [Recommendations](#13-recommendations)
14. [Simulation Study Steps Applied](#14-simulation-study-steps-applied)
15. [Deliverables Checklist](#15-deliverables-checklist)
16. [Instructor Notes & Suggested Improvements](#16-instructor-notes--suggested-improvements)

---

## 1. Project Overview

| Field | Details |
|-------|---------|
| **Project Title** | Single Household Multi-User Water Usage Simulation |
| **Course** | CSE 10/L – CS Professional Elective 2 (Modeling and Simulation) |
| **Institution** | University of Mindanao – College of Computing Education |
| **Simulation Type** | Discrete-Event Simulation (DES) with Stochastic and Continuous sub-models |
| **Tool Used** | Custom Web-based Dashboard (JavaScript) / Python SimPy |
| **Pricing Basis** | Davao City Water District pricing structure |
| **Household Configuration** | 4-user household |
| **Simulation Duration** | 24 hours per run; 30 independent replications |

### Background

Water consumption in residential settings involves complex interactions between multiple users, various fixtures, behavioral patterns, and utility pricing structures. By modeling these interactions through simulation, analysts can:

- Evaluate current water usage patterns without modifying the real system.
- Identify waste and behavioral inefficiencies before they result in high utility bills.
- Detect leaks using statistical anomaly detection rather than waiting for physical evidence.
- Test conservation strategies computationally before implementing them in a real home.

This project applies the core principles of CSE 10/L — specifically Discrete-Event Simulation, stochastic modeling, and system analysis — to a practical, decision-support application in household resource management.

---

## 2. Problem Description & Motivation

### Core Problem Statement

In a typical multi-user household, water consumption occurs **across multiple fixtures simultaneously** — showers, faucets, toilets, washing machines, dishwashers, and outdoor irrigation systems. Despite the significant volume of water consumed daily, residents often remain unaware of:

1. Their **total real-time water usage** at any given moment.
2. The **cumulative cost impact** of their daily habits under tiered or time-of-use (TOU) pricing structures.
3. The **existence and location of leaks** until they receive unexpectedly high utility bills.
4. The **quantifiable benefit** of adopting conservation measures.

### Identified Problem Areas

| # | Problem | Description |
|---|---------|-------------|
| 1 | **Invisible Consumption** | Household members cannot see real-time water flow or its cumulative cost impact in real time. |
| 2 | **Behavioral Inefficiency** | Long showers, running faucets while brushing teeth, and partial laundry loads waste significant water volumes daily. |
| 3 | **Undetected Leaks** | Small leaks can waste thousands of gallons annually without producing obvious visible signs until the billing cycle ends. |
| 4 | **Pricing Complexity** | Tiered or time-of-use water rates make it difficult for household members to understand the true cost of their usage patterns. |
| 5 | **Conservation Uncertainty** | Homeowners lack quantitative tools to measure how much water and money a specific behavioral or fixture change would actually save. |

### Why Simulation Is the Appropriate Solution

Directly experimenting with a real household water system to study these behaviors is impractical:
- You cannot "undo" a month of wasteful habits to compare costs.
- Deliberately inducing a leak to study detection response is dangerous and wasteful.
- Real data from utility bills arrives too infrequently and at too coarse a granularity to support detailed analysis.

Simulation provides a **safe, repeatable, cost-free laboratory** in which all five problem areas can be studied systematically.

---

## 3. Objectives

The simulation study has six specific, measurable objectives aligned with CSE 10/L Course Outcomes CO2 and CO3.

| # | Objective | CO Alignment |
|---|-----------|-------------|
| 1 | Model a multi-user household water system using discrete-event simulation principles | CO2 |
| 2 | Detect abnormal usage patterns indicative of potential leaks | CO3 |
| 3 | Compare system performance under different conservation scenarios (low-flow fixtures, behavior changes) | CO3 |
| 4 | Provide visual feedback through an interactive dashboard for user education | CO3 |
| 5 | Measure total daily/weekly water consumption and associated costs under various pricing schemes | CO3 |
| 6 | Project potential cost savings from recommended conservation measures | CO3 |

---

## 4. System Description

### System Definition

The **household water system** is a service system in which multiple users (entities) compete for shared water fixtures (resources), generating discrete usage events that consume a quantifiable resource (water measured in liters or gallons per minute).

### Entities

| Entity | Description |
|--------|-------------|
| **Water Flow** | The primary entity moving through the system, measured in gallons per minute (GPM) or liters per minute (LPM). Each fixture activation produces a water flow entity. |
| **Users (U1–U4)** | Household members who initiate water-consuming events according to probabilistic daily schedules. They are the agents that trigger fixture events. |
| **Fixture Events** | Individual water usage occurrences — shower sessions, faucet operations, toilet flushes, appliance cycles. Each event has a start time, duration, and flow rate. |

### Resources

| Resource | Description |
|----------|-------------|
| **Water Supply** | The household's water connection from the utility provider. Modeled with finite pressure and capacity constraints. |
| **Fixtures** | Physical water delivery devices — showerheads, faucets, toilets, washing machines, dishwashers, garden hoses. Each fixture has defined flow rates and usage patterns. |
| **Water Meter** | Measures and records cumulative consumption for billing purposes. In the simulation, this is the data logging module. |

### State Variables

| Variable | Description | Data Type |
|----------|-------------|-----------|
| `current_flow_rate` | Total active flow across all running fixtures at time *t* | Float (GPM/LPM) |
| `cumulative_usage` | Total water consumed from simulation start to time *t* | Float (Liters) |
| `fixture_status[f]` | On/Off/Leaking status for each fixture *f* | Enum |
| `daily_cost` | Accumulated water cost under the active pricing scheme | Float (₱) |
| `leak_flag` | Boolean flag raised when anomalous flow is detected | Boolean |
| `active_users` | Number of users currently consuming water simultaneously | Integer |

---

## 5. Simulation Model Type & Justification

This project uses a **hybrid simulation** approach combining three paradigms.

### Primary: Discrete-Event Simulation (DES)

Water fixtures turn ON and OFF at specific, identifiable points in time — these are discrete events. The system state (flow rate, cost, fixture statuses) only changes when an event occurs. Between events, the system remains unchanged.

```
Event Types in This Simulation:
  ● User shower start / shower end
  ● Faucet turned on / faucet turned off
  ● Toilet flush (instantaneous high-flow event)
  ● Washing machine cycle start / cycle end
  ● Dishwasher cycle start / cycle end
  ● Garden hose start / garden hose end
  ● Leak onset (anomalous continuous flow event)
```

**Why DES is appropriate:** Every water usage action in a household is a user-triggered event. The event-driven time advancement is computationally efficient and maps naturally to how household water use actually works — activity-based, intermittent, and discrete.

### Secondary: Stochastic Simulation

User behavior is inherently random. Shower duration, time of first morning use, number of toilet flushes per day, and laundry frequency all vary between days and between users. The model samples these from appropriate probability distributions.

```
Stochastic Variables:
  ● Shower duration          → Normal or Uniform distribution
  ● Inter-event times        → Exponential distribution (Poisson process)
  ● Number of toilet flushes → Poisson distribution
  ● Garden hose duration     → Uniform distribution
```

**Why stochastic modeling is appropriate:** Because outputs are random variables, single-run results are meaningless. The model requires **30 independent replications** to produce statistically reliable performance estimates.

### Tertiary: Continuous Sub-model

Minor but persistent water losses — dripping faucets, pipe seepage, slow toilet leaks — cannot be modeled as discrete events because they occur continuously at a low, constant rate.

```
Continuous Variables:
  ● Drip leak rate           → Constant flow (e.g., 0.02 LPM continuously)
  ● Pipe condensation loss   → Small fixed daily volume
```

**Why a continuous sub-model is appropriate:** These losses are too small to register as events but accumulate significantly over days and weeks. They are best modeled as a background continuous drain on the cumulative usage counter.

### Summary

| Simulation Type | Role in This Project | Why It Fits |
|----------------|----------------------|-------------|
| **Discrete-Event** | Models all fixture ON/OFF actions and user activity events | Fixtures activate/deactivate at specific points in time |
| **Stochastic** | Models variability in user behavior and fixture usage patterns | Real household behavior follows probability distributions |
| **Continuous** | Models minor background losses such as drips and pipe seepage | Small losses occur at every instant, not at discrete points |

> **Recommendation:** A **Hybrid DES + Stochastic** approach with continuous sub-models for background losses is the most accurate representation of this real-world system.

---

## 6. Simulation Variables

### Household Configuration Variables

| Variable | Type | Description | Example Values |
|----------|------|-------------|----------------|
| `num_users` | Integer | Number of household members | 2, 3, 4, 5 |
| `simulation_period` | Integer | Simulation duration in hours | 24 (daily), 168 (weekly) |
| `pricing_scheme` | Enum | Water billing structure | Flat Rate, Tiered, Peak Hour |
| `season` | Enum | Season affecting usage patterns | Dry, Wet |
| `warm_up_period` | Integer | Hours before data collection starts | 1–2 hours |

### Fixture Variables

Each fixture is characterized by a set of parameters that define its water consumption behavior.

| Fixture | Flow Rate (LPM) | Avg. Duration | Frequency per User/Day | Notes |
|---------|-----------------|---------------|------------------------|-------|
| **Toilet** | 6–8 LPM flush | ~1 min | 5–8 flushes | Instantaneous high-flow event |
| **Faucet** | 3–5 LPM | 0.5–3 min | Multiple short uses | Teeth brushing, hand washing |
| **Shower** | 8–12 LPM (standard); 5–7 LPM (low-flow) | 7–15 min | 1 per user/day | Largest single-use contributor |
| **Dishwasher** | 6–9 LPM | 45–90 min (full cycle) | 0–1 cycles/day | Depends on household habit |
| **Washing Machine** | 8–12 LPM | 45–90 min (full cycle) | 0–1 cycles/day | Stochastic day of use |
| **Garden Hose** | 15–20 LPM | 10–30 min | 0–1 session/day | Seasonal and weather-dependent |

### Pricing Variables

| Pricing Scheme | Rate | Application Rule |
|----------------|------|------------------|
| **Flat Rate** | ₱0.004 per liter | Applied uniformly to all consumption |
| **Tiered Pricing** | Rate increases as usage volume rises | Tier 1: ₱0.003/L (0–500L); Tier 2: ₱0.005/L (500–1000L); Tier 3: ₱0.007/L (>1000L) |
| **Peak Hour Surcharge** | ₱0.0045 per liter | Applied during peak hours (6–9 AM, 6–9 PM); base rate off-peak |

---

## 7. System Flow & Arena Modules

### Complete System Flow

```
┌─────────────────────────────────────────────────────┐
│            SYSTEM FLOW (ARENA LOGIC)                │
└─────────────────────────────────────────────────────┘

[1. CREATE MODULE]
    User/Event Generation
    → Generates water usage events per user schedule
    → Each event has: user ID, fixture type, start time
         |
         ▼
[2. ASSIGN MODULE]
    Fixture Properties Assignment
    → Assigns flow rate, duration, pricing tier
    → Sets fixture_status = ACTIVE
    → Calculates expected water volume = flow_rate × duration
         |
         ▼
[3. DECIDE MODULE — Multi-Fixture Check]
    Are other fixtures currently running?
    → YES: Check total combined flow vs. supply capacity
    → NO: Proceed normally
    → Concurrent usage → models resource sharing
         |
         ▼
[4. PROCESS MODULE]
    Water Flow & Cost Calculation
    → Accumulates water_usage += flow_rate × duration
    → Calculates cost based on active pricing scheme
    → Updates real-time dashboard counters
         |
         ▼
[5. DECIDE MODULE — Leak Check]
    Is current_flow_rate abnormal?
    → CONDITION: Flow detected during expected idle hours
    → CONDITION: Continuous flow > threshold duration
    → CONDITION: Daily usage > historical_average × 1.5
         |
    YES → RAISE LEAK ALERT
    NO  → Continue
         |
         ▼
[6. DISPOSE MODULE — LOG & VISUALIZE]
    → Records event to event log (time, user, fixture, volume)
    → Updates hourly distribution chart
    → Updates fixture monitor counters
    → Updates conservation comparison panel
    → Fixture_status = INACTIVE
```

### Arena Module Configuration Details

#### Module 1: CREATE (User/Event Generation)

| Parameter | Value |
|-----------|-------|
| Entity Type | Water Usage Event |
| Time Between Arrivals | Exponential(mean = avg inter-event time per user) |
| Entities per Arrival | 1 per event |
| Max Arrivals | Unlimited within simulation period |
| Number of Users | 4 (U1, U2, U3, U4 — each follows own schedule) |

#### Module 2: ASSIGN (Fixture Properties)

| Assignment | Expression |
|------------|------------|
| Flow Rate | Based on fixture type lookup table |
| Duration | Sampled from Normal/Uniform distribution per fixture |
| Expected Volume | `volume = flow_rate × duration` |
| Fixture Status | `fixture_status[f] = ACTIVE` |

#### Module 3: DECIDE (Multi-Fixture / Leak Check)

| Decision | Condition | Branch |
|----------|-----------|--------|
| Concurrent use check | `active_fixtures > 1` | YES → check pressure; NO → proceed |
| Leak detection | `flow_rate > 0 AND time IN idle_hours` | YES → alert; NO → proceed |
| Overuse detection | `daily_usage > baseline × 1.5` | YES → alert; NO → proceed |

#### Module 4: PROCESS (Water Flow & Cost Calculation)

```
ACTION TYPE:        Delay (duration of fixture use)
RESOURCE:           Water Supply (household connection)
DELAY TYPE:         Random (sampled from fixture duration distribution)
SEIZE/RELEASE:      Seize water supply → hold for duration → release

After PROCESS:
  cumulative_usage  += flow_rate × actual_duration
  daily_cost        += cumulative_usage × pricing_rate
  fixture_monitor   += volume (per fixture type)
```

#### Module 5: DISPOSE (Log & Visualize)

```
RECORDS:   Event timestamp, user ID, fixture type, volume (L), cost (₱)
UPDATES:   Hourly distribution chart, fixture totals, event log table
FLAGS:     Sets fixture_status = INACTIVE
```

---

## 8. Assumptions

The following assumptions define the boundaries and constraints of the simulation model. These are explicitly stated to support validation and reproducibility.

| # | Assumption | Justification |
|---|------------|---------------|
| 1 | Fixture flow rates are **constant** during active use | Simplifies calculation; pressure variations are considered negligible for this study scope |
| 2 | User behavior follows **probability distributions** | Real household behavior is stochastic, not deterministic |
| 3 | Users do **not adjust habits** unless a specific conservation scenario is explicitly selected | Isolates the effect of each conservation measure |
| 4 | Water pricing follows one of three defined structures: **Flat Rate (₱0.004/L)**, **Tiered Pricing**, or **Peak Hour Surcharge (₱0.0045/L)** | Based on Davao City Water District rate structures |
| 5 | Cost is **recalculated after every usage event** throughout the 24-hour simulation | Ensures cost accuracy at event-level granularity |
| 6 | Leak events are modeled as **continuous low-flow anomalies** during hours when all users are expected to be inactive | Operationalizes the leak detection objective |
| 7 | All 4 users follow **independent, non-synchronized schedules** | Real household members do not coordinate bathroom schedules |
| 8 | The simulation uses a **warm-up period** before collecting performance data | Eliminates initialization bias from unrealistic early-state conditions |
| 9 | Water supply capacity is **sufficient** to handle simultaneous fixture use under normal conditions | Focuses study on consumption patterns, not infrastructure stress testing |
| 10 | **30 replications** with different random seeds are performed to ensure statistical validity | Stochastic outputs require multiple independent runs for reliable mean estimates |

---

## 9. Simulation Setup & Run Parameters

### Core Run Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Simulation Duration** | 24 hours (1 full day) | Covers one complete water billing/usage cycle |
| **Warm-Up Period** | 1–2 hours | Allows system to reach steady-state before data collection begins |
| **Number of Replications** | 30 independent runs | Ensures statistical reliability of stochastic output |
| **Random Seeds** | Different per replication | Each run produces independent, slightly different results |
| **Time Units** | Minutes | Consistent with fixture duration and event granularity |
| **Household Size** | 4 users (U1, U2, U3, U4) | Represents a typical Filipino household |
| **Total Events per Run** | ~52 events | Based on typical fixture usage frequency per 4-user household per day |

### How the Warm-Up Period Works

```
Time 0:00 ─────── [Warm-Up Zone] ──────── Time 1:00 ──── [Data Collection Begins] ───── Time 24:00
    │                                           │                                              │
No statistics                          Steady-state           All performance measures
collected here                         reached                  recorded from here
```

> **Why this matters:** At time zero, the simulation starts with an artificially clean state — no users have used any water, no costs have accumulated. This does not represent a real household mid-day. The warm-up period allows the model to settle into a realistic operational pattern before the analyst begins collecting data.

---

## 10. Scenarios Tested

The simulation tests four distinct scenarios to evaluate the impact of conservation strategies and detect system anomalies.

### Scenario 1: Baseline (Normal Usage)
**Description:** All users operate with standard fixture flow rates and typical behavioral patterns. No conservation measures are applied.

```
Fixtures:         Standard flow rates (full GPM/LPM specifications)
User Behavior:    Typical daily patterns (probabilistic, no modification)
Pricing:          Active pricing scheme (Flat, Tiered, or Peak)
Purpose:          Establish baseline consumption and cost for comparison
```

### Scenario 2: Low-Flow Fixtures
**Description:** Standard fixtures are replaced with low-flow equivalents. User behavior remains unchanged.

```
Changes Applied:
  Shower:         12 LPM → 7 LPM (low-flow showerhead)
  Faucet:         5 LPM  → 3 LPM (aerator installed)
  Toilet:         8 LPM  → 5 LPM (dual-flush mechanism)
  
User Behavior:    Unchanged (same durations, same frequencies)
Purpose:          Isolate the impact of fixture efficiency alone
Expected Result:  15–30% reduction in daily water consumption
```

### Scenario 3: Behavior Modification
**Description:** Original fixtures are retained but users adopt conservation behaviors.

```
Changes Applied:
  Shower duration:        Reduced by 2–3 minutes per shower
  Faucet during brushing: Turned off while brushing (not left running)
  Laundry loads:          Full loads only (no partial loads)
  Garden watering:        Shifted to cooler hours (5–7 AM, 7–9 PM)
  
Fixtures:         Standard (unchanged)
Purpose:          Isolate the impact of behavioral change alone
Expected Result:  10–20% reduction in daily consumption and cost
```

### Scenario 4: Leak Detection
**Description:** A simulated leak is introduced at a random fixture during a designated idle period (overnight or mid-day when users are away).

```
Leak Parameters:
  Onset Time:      Random (between 00:00–05:00 or 10:00–14:00)
  Leak Flow Rate:  0.5–2.0 LPM (slow but continuous)
  Duration:        Until detected by anomaly logic or end of run
  
Detection Logic:  
  → Continuous flow > 30 min with no active user events = LEAK ALERT
  → Daily usage > 1.5 × historical_average = ANOMALY FLAG
  
Purpose:          Test effectiveness of statistical leak detection
Expected Result:  Alert triggered within 30–60 minutes of leak onset
```

---

## 11. Performance Measures

The following metrics are collected during simulation execution and displayed on the real-time dashboard.

| Performance Measure | Description | Unit |
|--------------------|-------------|------|
| **Total Water Consumption** | Cumulative liters used across all fixtures and users for the day | Liters (L) |
| **Average Daily Cost** | Mean water bill cost across all 30 replications | Philippine Peso (₱) |
| **Peak Flow Rate** | Maximum simultaneous flow rate observed during the simulation period | Liters per Minute (LPM) |
| **Fixture Usage Breakdown** | Per-fixture consumption totals and usage count | Liters & number of uses |
| **Leak Detection Time** | Time elapsed from leak onset to alert trigger | Minutes |
| **Conservation Savings** | Difference in consumption and cost between Baseline and conservation scenarios | Liters saved, ₱ saved |
| **Server (Fixture) Utilization** | Percentage of time each fixture is actively in use | % |
| **Hourly Distribution** | Water consumption pattern by hour of day | Liters per hour |

### Sample Results Reference (from Simulation Dashboard)

Based on the simulation run captured at time 21:50 (with 51/52 events completed):

| Metric | Observed Value |
|--------|---------------|
| Total Usage | 894.5 L |
| Total Cost (Flat Rate) | ₱3.58 |
| Events Completed | 51 / 52 |
| Leaks Detected | 0 |
| Shower (8 uses) | 496.8 L |
| Faucet (19 uses) | 76.6 L |
| Toilet (12 uses) | 73.1 L |
| Garden Hose (4 uses) | 178.6 L |
| Washing Machine (4 uses) | 41.3 L |
| Dishwasher (4 uses) | 28.1 L |

> **Interpretation:** The shower is the single largest water consumer (55.6% of total), followed by the garden hose (20%). These two fixtures are the highest-priority targets for conservation scenarios 2 and 3.

---

## 12. Results Interpretation

### Reading the Hourly Distribution Chart
The hourly distribution chart shows water consumption volume (in liters) plotted against the 24-hour simulation period. Key patterns to look for:

- **Morning peak (6–9 AM):** High activity from showers, faucets, and toilet flushes as users prepare for school/work.
- **Midday lull (10 AM–3 PM):** Reduced usage if household members are away.
- **Evening peak (6–9 PM):** Second spike from cooking, bathing, appliance use.
- **Overnight baseline (11 PM–5 AM):** Should be near-zero. Any usage here is a **leak signal**.

### Reading the Conservation Comparison Panel
The comparison panel shows side-by-side cost estimates for each pricing scenario. Values of ₱1.26 and ₱0.90 (as seen in the results screenshot) represent cost savings achievable through conservation measures — quantifying the financial benefit of behavioral or fixture changes.

### Event Log Interpretation
The event log records every discrete water usage event with: `timestamp | user ID | fixture type | volume (L) | status`.

```
Sample Entries:
  07:04  U2  Shower       63.01L   ✓   ← Long shower event
  07:04  U2  Faucet        4.05L   ✓   ← Concurrent faucet use
  08:02  U1  Garden Hose  42.90L   ✓   ← Morning garden watering
  20:14  U1  Shower       63.75L   ✓   ← Evening shower
```

Any entry during hours 23:00–05:00 with no corresponding user activity = **investigate for leak**.

---

## 13. Recommendations

Based on simulation results, the following recommendations are derived for a typical 4-user household:

### Fixture-Level Recommendations

| Recommendation | Estimated Savings | Implementation Difficulty |
|---------------|------------------|--------------------------|
| Install low-flow showerheads (12 → 7 LPM) | ~25–35% of shower usage | Low cost, easy to install |
| Add faucet aerators to all taps | ~30% of faucet usage | Very low cost |
| Upgrade to dual-flush toilets | ~35–40% of toilet usage | Moderate cost |
| Use dishwasher/washer only when fully loaded | ~30% of appliance usage | Behavioral, no cost |

### Behavioral Recommendations

| Behavior Change | Estimated Savings |
|----------------|-----------------|
| Reduce shower time by 3 minutes per person | ~18 L/day per person (72 L/day for 4 users) |
| Turn off faucet while brushing teeth | ~8 L/person/day |
| Shift garden watering to 5–7 AM | No consumption savings but reduces peak-hour surcharge cost |

### Leak Detection Recommendations

- Implement a **baseline usage profile** by recording 7 days of normal usage data.
- Set an automated alert threshold at **1.5× the daily average**.
- Monitor overnight flow (11 PM–5 AM) — any nonzero reading triggers inspection.

---

## 14. Simulation Study Steps Applied

This project follows all 11 steps of the CSE 10/L Simulation Study methodology.

| Step | Activity in This Project | Output |
|------|-------------------------|--------|
| **1. Problem Definition** | Identified 5 household water problems: invisible consumption, behavioral inefficiency, undetected leaks, pricing complexity, conservation uncertainty | Scoped problem statement with 6 specific objectives |
| **2. System Analysis & Data Collection** | Identified entities (water flow, users, fixture events), resources (water supply, fixtures, meter), and state variables | System description document |
| **3. Model Conceptualization** | Designed hybrid DES + Stochastic model; defined fixture library, user behavior module, pricing module | Model flow diagram, Arena module layout, assumptions list |
| **4. Model Translation** | Implemented as interactive web dashboard with JavaScript simulation engine and Python/SimPy backend logic | Executable simulation model |
| **5. Verification** | Tested event logic: fixture ON/OFF sequences, cost calculation formulas, concurrent usage handling | Verified event sequences and calculations |
| **6. Validation** | Compared simulated daily water bill against actual Davao City household utility bill data | Calibrated model within acceptable error margin |
| **7. Experimental Design** | Designed 4 scenarios × 30 replications; defined warm-up period and data collection window | Experiment plan document |
| **8. Simulation Execution** | Ran 24-hour simulation with 52 events for 4-user household under each scenario | Raw results: 894.5L usage, ₱3.58 cost, 0 leaks (baseline run) |
| **9. Output Analysis** | Analyzed fixture breakdown (shower = 55.6%), identified peak hours, compared conservation savings | Performance evaluation report |
| **10. Documentation** | Created full project paper with all required chapters; developed interactive dashboard | Project paper + dashboard |
| **11. Implementation** | Recommendations: install low-flow fixtures, reduce shower time, monitor overnight flow | Actionable household conservation plan |

---

## 15. Deliverables Checklist

### Required Project Deliverables

- [ ] **Chapter 1 – Introduction:** Background, problem statement, 6 objectives, scope, significance
- [ ] **Chapter 2 – System Description:** Entity/resource/state variable identification, system representations
- [ ] **Chapter 3 – Model Design:** Conceptual framework, use case diagram, process flow, Arena module layout, assumptions
- [ ] **Chapter 4 – Implementation:** Arena/Python code or model, fixture library, data inputs, verification results
- [ ] **Chapter 5 – Results & Analysis:** Simulation output tables, charts, scenario comparisons, validation
- [ ] **Chapter 6 – Conclusion & Recommendations:** Summary, conservation recommendations, future work

### Required Diagrams & Visual Outputs

- [ ] Context Diagram (household system boundary)
- [ ] Use Case Diagram (users ↔ fixtures ↔ simulation system)
- [ ] Activity / Flow Diagram (system flow: CREATE → ASSIGN → DECIDE → PROCESS → DECIDE → DISPOSE)
- [ ] Arena Model Screenshot or equivalent tool layout
- [ ] Hourly Distribution Chart (liters per hour across 24 hours)
- [ ] Fixture Breakdown Chart (pie or bar chart of usage by fixture type)
- [ ] Conservation Comparison Panel (baseline vs. scenario savings)
- [ ] Event Log Table (sample entries from simulation run)
- [ ] Dashboard Screenshot (full model design interface)

---

## 16. Instructor Notes & Suggested Improvements

These improvement notes were provided by the instructor (as seen on page 18 of the presentation) and should be addressed in the final paper and simulation revision.

| Improvement Item | Description | How to Implement |
|-----------------|-------------|-----------------|
| **Legends for Leak Detection Baseline** | Add a clear visual baseline reference line on all usage charts so that anomalous leak readings are clearly distinguishable | Add a horizontal "Normal Range" band to the hourly distribution chart |
| **Increase Parameters (Fixtures)** | Allow users to configure the number of each fixture type rather than using fixed defaults | Add input fields to the Controls panel: "# of showers," "# of faucets," etc. |
| **More Detailed Results Section** | Current results show totals only; need per-user and per-hour breakdowns | Add a "Results Detail" tab showing usage by user (U1–U4) and by hour |
| **Increase Simulation Duration** | 24-hour runs only show one day; extend to 7-day or 30-day simulations | Add a `simulation_period` input (24h / 7 days / 30 days) to the Controls panel |

### Proposed Extended Simulation Parameters

```
Enhanced Simulation Setup (Recommended):
  Period:           7 days (168 hours) or 30 days (720 hours)
  Replications:     30 independent runs
  Per-user logging: Track U1, U2, U3, U4 usage separately
  Fixture count:    Configurable (1–3 showers, 2–4 faucets, 1–2 toilets, etc.)
  Leak baseline:    Computed from first 3 days of normal operation
  Alert threshold:  Daily usage > mean + 2 standard deviations
```

---

## 📊 Quick Reference: Key Simulation Formulas

| Formula | Purpose |
|---------|---------|
| `Volume (L) = Flow Rate (LPM) × Duration (min)` | Calculate water consumed per fixture event |
| `Cost = Volume × Rate (per pricing scheme)` | Calculate cost of each usage event |
| `Total Daily Usage = Σ(all fixture events per day)` | Sum all events in a 24-hour run |
| `Fixture Utilization = Active Time / Total Time × 100%` | Measure how often a fixture is in use |
| `Leak Alert = daily_usage > baseline_avg × 1.5` | Statistical anomaly detection threshold |
| `Conservation Savings = Baseline_Usage − Scenario_Usage` | Quantify conservation impact (liters) |
| `Cost Savings = Baseline_Cost − Scenario_Cost` | Quantify financial impact (₱) |
| `Server Utilization = Busy Time / Total Time × 100%` | Applied to each fixture as a "server" |

---

## 📚 Simulation Type Classification Summary

| Model Layer | Type | Variables | Role |
|-------------|------|-----------|------|
| Primary | **Discrete-Event (DES)** | Fixture ON/OFF events, user actions | Core simulation engine |
| Secondary | **Stochastic** | Shower duration, inter-event times, flush frequency | Injects real-world variability |
| Tertiary | **Continuous** | Drip leak rate, pipe seepage | Models background water losses |

---

*Project Guide prepared for CSE 10/L – Modeling and Simulation*  
*University of Mindanao | College of Computing Education*  
*Based on Single Household Water Usage Simulation presentation and design document*
