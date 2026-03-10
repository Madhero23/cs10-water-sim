# CSE 10/L – Modeling and Simulation
## 📘 Complete Project Guide & Study Reference
*University of Mindanao | College of Computing Education*

---

## 📌 Table of Contents
1. [Course Overview](#course-overview)
2. [Simulation Fundamentals](#simulation-fundamentals)
3. [Steps in a Simulation Study](#steps-in-a-simulation-study)
4. [Types of Simulation](#types-of-simulation)
5. [Discrete-Event Simulation (DES)](#discrete-event-simulation)
6. [Single-Server System Modeling](#single-server-system-modeling)
7. [Inventory System Simulation](#inventory-system-simulation)
8. [Queuing Theory & Probability Distributions](#queuing-theory--probability-distributions)
9. [Petri Nets](#petri-nets)
10. [High-Level Petri Nets (Colored Petri Nets)](#high-level-petri-nets)
11. [Linear Programming](#linear-programming)
12. [Project Paper Structure & Requirements](#project-paper-structure--requirements)
13. [Assessment Rubrics](#assessment-rubrics)

---

## 1. Course Overview

| Item | Details |
|------|---------|
| Course | CSE 10/L – CS Professional Elective 2 |
| Topic | Modeling and Simulation |
| Credits | 3.0 units (2.0 Lecture / 1.0 Lab) |
| Pre-requisite | CS 6/L |

### Course Outcomes (CO)
- **CO1:** Explain the underlying principles of simulation to understand concepts and operations in certain situations.
- **CO2:** Develop a model that represents the interaction of events to mimic the behavior of objects in actual settings.
- **CO3:** Conduct a simulation to test the model's effectiveness as a guide in the decision-making process.

---

## 2. Simulation Fundamentals

### What is Simulation?
> **Simulation** is the imitation of a real-world process or system over time, usually via a model.

### System, Models, and Simulation
- **System** – a set of connected components that work together toward a common objective (e.g., people, tools, materials, procedures).
- **Model** – a representation of the system used to study its behavior.
- **Simulation** – running the model over time to observe how the system performs.

### Problem Areas Solvable Using Simulation
Simulation is used when:
- Real systems are too **expensive, dangerous, or complex** to experiment on directly.
- We want to test **"what-if" scenarios** before making real changes.
- **Analytical formulas** are not practical or do not exist.

| Application Area | What Simulation Tests |
|---|---|
| Manufacturing Systems | Machine layouts, production schedules, bottlenecks |
| Communication Networks | Bandwidth, router capacity, protocols |
| Computer Systems | CPU speed, memory requirements, response time |
| Transportation Systems | Airports, highways, subways, ports |
| Service Organizations | Customer wait time, number of servers, service speed |
| Business Process Re-engineering | Old vs. new workflows, delays, redundancies |
| Supply Chains | Delays, transportation costs, inventory levels |
| Inventory Systems | Reorder levels, order quantity, shortage prevention |
| Mining Operations | Equipment scheduling, downtime reduction, safety |

### Ways to Study a System

| Approach | Description |
|---|---|
| Experiment with Actual System | Often impractical – too expensive, risky, or system doesn't exist yet |
| Physical Model | Tangible representation (e.g., wind tunnel model, flight simulator) |
| Mathematical Model | Describes system using equations (e.g., d = r × t) |
| Analytical Solution | Exact formula-based solution (preferred when available) |
| **Simulation** | Used for complex systems where analytical solutions are difficult |

### Simulation Tools
- **Spreadsheet:** Microsoft Excel
- **General Purpose Languages:** Python, Java, MATLAB, Visual C++
- **General Simulation Languages:** GPSS, SIMSCRIPT, **Arena**, SimProcess
- **Special Purpose Packages:** OPNET, COMNET, SIMFACTORY

---

## 3. Steps in a Simulation Study

```
Step 1: Problem Definition
    ↓
Step 2: System Analysis & Data Collection
    ↓
Step 3: Model Conceptualization
    ↓
Step 4: Model Translation (Model Development)
    ↓
Step 5: Verification
    ↓
Step 6: Validation
    ↓
Step 7: Experimental Design
    ↓
Step 8: Simulation Execution
    ↓
Step 9: Output Analysis & Interpretation
    ↓
Step 10: Documentation & Reporting
    ↓
Step 11: Implementation (Optional)
```

### Detailed Step Descriptions

#### Step 1 – Problem Definition
- Clearly define the problem to be solved.
- Identify **objectives**, **scope**, and **performance measures**.
- **Key Output:** Well-defined problem statement.
- *Example: Reduce customer waiting time in a bank.*

#### Step 2 – System Analysis & Data Collection
- Study the real system.
- Identify components, inputs, outputs, and constraints.
- Collect real or estimated data.
- **Key Output:** System description and dataset.
- *Example: Customer arrival rate, service time per teller.*

#### Step 3 – Model Conceptualization
- Create a conceptual (logical) model.
- Decide the type of simulation: Discrete-Event, Continuous, or Stochastic.
- **Key Output:** Flow diagrams, assumptions, model structure.
- *Example: Represent customers as entities and tellers as resources.*

#### Step 4 – Model Translation (Development)
- Convert the conceptual model into a computer program.
- **Key Output:** Executable simulation model.
- *Tools: Python, MATLAB, Arena.*

#### Step 5 – Verification
- Check whether the model is **correctly implemented**.
- Ensure the logic and code work as intended.
- **Key Question:** *"Did we build the model right?"*
- *Example: Debugging code, checking event sequences.*

#### Step 6 – Validation
- Compare simulation results with the **real system**.
- Check if the model accurately represents reality.
- **Key Question:** *"Did we build the right model?"*
- *Example: Compare simulated waiting time with actual bank data.*

#### Step 7 – Experimental Design
- Decide on number of simulation runs, simulation length, and parameter variations.
- **Key Output:** Experiment plan.
- *Example: Testing 1 teller vs 2 tellers.*

#### Step 8 – Simulation Execution
- Run the simulation based on the experiment design.
- Collect output data.
- **Key Output:** Raw simulation results.
- *Example: Run model 100 times to get average waiting time.*

#### Step 9 – Output Analysis & Interpretation
- Analyze results using statistics or graphs.
- Interpret findings for decision-making.
- **Key Output:** Performance evaluation.
- *Example: Average waiting time reduced by 30%.*

#### Step 10 – Documentation & Reporting
- Document assumptions, model details, and results.
- Prepare reports and presentations.
- **Key Output:** Final simulation report / project paper.

#### Step 11 – Implementation (Optional)
- Apply recommendations to the real system.
- *Example: Hire an additional teller based on simulation findings.*

---

## 4. Types of Simulation

### 1. Discrete-Event Simulation (DES)
A simulation model where **state changes occur only at specific points in time** called events.

| Characteristic | Description |
|---|---|
| Time progression | Advances event by event |
| State changes | Occur instantly at event points |
| Common structures | Queues and resources |
| Examples | Bank queues, hospital patient flow, call centers, traffic intersections |

### 2. Continuous Simulation
Models systems where **state variables change continuously** over time.

| Characteristic | Description |
|---|---|
| Time progression | Flows continuously |
| State changes | Smooth, no sudden jumps |
| Described by | Differential or mathematical equations |
| Examples | Temperature variation, water level in tank, population growth |

### 3. Stochastic Simulation
Includes **randomness or probability** in the model.

| Characteristic | Description |
|---|---|
| Variability | Results vary from run to run |
| Requires | Multiple runs for reliable results |
| Analysis | Statistical interpretation |
| Examples | Monte Carlo simulation, random machine breakdowns, stock price modeling |

---

## 5. Discrete-Event Simulation

### Key Components
| Component | Description | Example |
|---|---|---|
| **Entities** | Objects moving through the system | Customers |
| **Events** | Actions that change the system | Arrival, Service Start, Service End |
| **Resources** | Things that serve entities | Cashier, Server |
| **State Variables** | System status | # in queue, server busy/idle |

### DES Algorithm (Pseudocode)
```
START
Set current_time = 0
Queue = empty
Server = idle

WHILE current_time < simulation_end_time:
    Generate next arrival
    IF server is idle:
        Start service
    ELSE:
        Add customer to queue
    Process next event
END
```

### Python Code Example – Random Number Generation
```python
import random

num_customers = 5
arrival_times = []
service_times = []

for i in range(num_customers):
    arrival = random.randint(1, 10)   # random arrival time (minutes)
    service = random.randint(2, 8)    # random service time (minutes)
    arrival_times.append(arrival)
    service_times.append(service)

print("Customer\tArrival Time\tService Time")
for i in range(num_customers):
    print(f"{i+1}\t\t{arrival_times[i]}\t\t{service_times[i]}")
```

### Process Flow
```
Customer Arrival → Queue → Service → Exit
```

---

## 6. Single-Server System Modeling

### Definition
A single-server system is a simulation model where **one server provides service to arriving customers** one at a time. If the server is busy, entities wait in a queue.

### System Flow
```
[Arrival] → [Check Server]
                  |
          Server Free? 
          Yes → [Service] → [Exit]
          No  → [Wait in Queue] → [Service] → [Exit]
```

### Performance Measures

| Measure | Formula | Example |
|---|---|---|
| **Waiting Time** | Service Start Time − Arrival Time | Customer arrives at t=2, served at t=5 → WT = 3 min |
| **Queue Length** | # of customers waiting at given time | 4 customers in line → QL = 4 |
| **Server Utilization** | (Total Busy Time / Total Time) × 100 | 45 min busy / 60 min total = 75% |
| **System Performance** | Combination of all measures | Average wait, throughput, efficiency |

### Arena Simulation Setup
```
[Create] → [Process] → [Dispose]
  ↑             ↑           ↑
Arrival      Service      Exit
```

---

## 7. Inventory System Simulation

### Purpose
Models how items are **stored, used, replenished, and monitored** over time to ensure enough stock while minimizing cost.

### Key Questions Answered
- When should we **reorder**?
- How much should we **order**?
- Will stock **run out**?
- How much inventory should be **maintained**?

### Sample Scenario
```
Initial Inventory   = 50 items
Daily Demand        = 10 items
Reorder Level       = 20 items
Order Quantity      = 40 items
Delivery Time       = 2 days
```

### Arena Model Structure
```
[Create] → [Assign] → [Decide] ——No——→ [Dispose]
                          |
                         Yes
                          ↓
                      [Process]
                          ↓
                      [Dispose]
```

### Arena Modules Configuration

| Module | Purpose | Key Data |
|---|---|---|
| **Create** | Demand arrival | Entity type, time between arrivals, units |
| **Assign** | Reduce inventory | `Inventory_Level = Inventory_Level - Demand_Quantity` |
| **Decide** | Check reorder level | Condition: `Inventory_Level <= Reorder_Level` |
| **Process** | Delivery/Restocking | Resource: Supplier, Delay: delivery time |
| **Dispose** | End process | Terminates entity |

> After delivery: `Inventory_Level = Inventory_Level + Order_Quantity`

---

## 8. Queuing Theory & Probability Distributions

### Queuing Theory Basics
- **Arrival rate (λ)** – average customers arriving per time unit
- **Service rate (μ)** – average customers served per time unit
- **Queue discipline** – order of service (e.g., FCFS – First Come First Serve)
- **Stable system:** μ > λ (service rate exceeds arrival rate)

---

### Discrete Probability Distributions

#### 1. Binomial Distribution
For **n independent trials** with probability of success **p**:

**Formula:** `P(X=k) = C(n,k) × p^k × (1-p)^(n-k)`

**Example:** Student guesses 5 MCQ questions (p = 0.25). P(exactly 2 correct)?
```
P(X=2) = C(5,2) × (0.25)² × (0.75)³ = 10 × 0.0625 × 0.4219 ≈ 0.2637
```

#### 2. Multinomial Distribution
Generalization of Binomial for **k categories** per trial.

**Formula:** `P = n! / (x₁! x₂! ... xₖ!) × (p₁^x₁ × p₂^x₂ × ... × pₖ^xₖ)`

**Example:** Roll a die 4 times. P(each of faces 1, 2, 3, 4 appears once)?
```
P = 4! / (1!1!1!1!0!0!) × (1/6)⁴ = 24 × (1/1296) ≈ 0.0185
```

#### 3. Hypergeometric Distribution
Used when **sampling without replacement** from a finite population.

**Example:** Box has 5 defective + 15 good bulbs (N=20). Select 4 (n=4). P(exactly 1 defective)?
- Use the hypergeometric formula: `P = C(K,k) × C(N-K, n-k) / C(N,n)`

#### 4. Geometric Distribution
Probability the **first success occurs on the k-th trial**.

**Formula:** `P(X=k) = (1-p)^(k-1) × p`

**Example:** Passing probability = 0.3. P(first pass on 3rd attempt)?
```
P(X=3) = (0.7)² × (0.3) = 0.49 × 0.3 = 0.147
```

#### 5. Negative Binomial Distribution
Probability the **r-th success occurs on the k-th trial**.

**Example:** p = 0.4. P(2nd success on 5th trial)?
```
P = C(4,1) × (0.4)² × (0.6)³ = 4 × 0.16 × 0.216 = 0.138
```

#### 6. Poisson Distribution
Models **number of events in a fixed interval** when events occur independently.

**Formula:** `P(X=k) = e^(-λ) × λ^k / k!`

**Example:** Call center receives λ=3 calls/min. P(exactly 2 calls)?
```
P(X=2) = e^(-3) × 3² / 2! = (0.0498 × 9) / 2 ≈ 0.224
```

---

### Continuous Probability Distributions

#### 1. Normal Distribution
Symmetric, **bell-shaped** distribution. **Standardization (Z-score):**

**Formula:** `Z = (X - μ) / σ`

**Example:** μ=50, σ=10. Find P(X < 60):
```
Z = (60 - 50) / 10 = 1
P(Z < 1) = 0.8413  → Look up Z-table
```

#### 2. Exponential Distribution
Models **waiting time until the next event**.

**Formula:** `P(X > t) = e^(-λt)`

**Example:** λ = 3/hour. Find P(X > 1 hour):
```
P(X > 1) = e^(-3×1) = e^(-3) ≈ 0.0498
```

#### 3. Weibull Distribution
Models **lifetime of products and failure times**.

**CDF Formula:** `P(X < x) = 1 - e^(-(x/λ)^k)`

**Example:** k=2, λ=3. Find P(X < 2):
```
P(X < 2) = 1 - e^(-(2/3)²) = 1 - e^(-0.4444) ≈ 1 - 0.6412 = 0.3588
```

#### 4. Beta Distribution
Defined on interval **[0, 1]**, controlled by parameters α and β.

**Mean:** `E(X) = α / (α + β)`  
**Variance:** `Var(X) = αβ / (α+β)²(α+β+1)`

**Example:** X ~ Beta(2, 3) → E(X) = 2/5 = 0.4

#### 5. Lognormal Distribution
`ln(X)` is normally distributed. `X ~ Lognormal(μ, σ²)`

**Mean Formula:** `E(X) = e^(μ + σ²/2)`

**Example:** μ=0, σ=1: `E(X) = e^(0.5) ≈ 1.6487`

#### 6. Uniform Distribution
All values in an interval **equally likely**.

**Formula:** `P(a ≤ X ≤ b) = interval length / total length`

**Example:** X ~ U(2, 8). Find P(3 ≤ X ≤ 6):
```
P = (6-3) / (8-2) = 3/6 = 0.5
Mean: E(X) = (2+8)/2 = 5
Variance: Var(X) = (8-2)²/12 = 3
```

---

## 9. Petri Nets

### Definition
A **Petri Net** is a mathematical modeling tool used to describe and analyze systems where events happen **concurrently (at the same time)**.

Used for: Distributed systems, Logical systems, Real-time systems, Manufacturing systems.

### Components

| Component | Symbol | Description | Example |
|---|---|---|---|
| **Places** | ○ Circle | States or conditions | "Order Received", "Machine Available" |
| **Transitions** | □ Rectangle/Bar | Events or actions | "Process Order", "Start Machine" |
| **Tokens** | • Dot | Resources, objects, current status | 1 token = 1 customer |
| **Arcs** | → Arrow | Flow direction connecting places & transitions | Student Registered → Submit Form → Approved |
| **Marking** | Token distribution | Current system state | 10 tokens in "Submitted", 0 in "Graded" |

### Key Concepts

#### Enabling & Firing
- **Enabling:** A transition is enabled if required tokens are present in all input places.
- **Firing:** When transition fires → tokens removed from input places → tokens added to output places.

#### Concurrency (Parallel Activities)
Multiple processes happen at the same time.
*Example: Students taking exam simultaneously, multiple orders processed at once.*

#### Synchronization
A process waits for multiple conditions before proceeding.
*Example: Student graduates only if Thesis Approved AND All Subjects Passed.*

#### Conflict (Decision Making)
One token can enable multiple transitions but only one fires.
*Example: Order is either Approved OR Rejected.*

#### Resource Sharing
One resource shared by multiple processes.
*Example: One printer shared by many employees — token in "Resource Available" controls access.*

### Step-by-Step Petri Net Execution
```
Step 1: Initial Marking — place tokens in starting positions
Step 2: Check Enabled Transition — verify required tokens are present
Step 3: Fire Transition — remove tokens from input, add to output
Step 4: New Marking — system moves to new configuration
```

### Example: Order Processing System
```
Places:        [Order Received] → [Payment Confirmed] → [Order Shipped]
Transitions:       Verify Payment          Ship Order

Flow:
1. Token in "Order Received"
2. Verify Payment fires → token moves to "Payment Confirmed"
3. Ship Order fires → token moves to "Order Shipped"
```

---

## 10. High-Level Petri Nets

### Colored Petri Nets (CPN)
An advanced version where **tokens carry data values** (called "colors"), making the model more compact and powerful.

**Key features:**
- Backward-compatible extension of basic Petri Nets
- Each token has a "color" representing its type/identity
- One model handles multiple entity types

### Advantages

| Advantage | Description |
|---|---|
| Compact models | One net handles multiple scenarios |
| Easier simulation | Less complexity than multiple basic nets |
| Verification | Safety properties can be formally checked |
| Deadlock detection | Identify states where system gets stuck |
| Real-time systems | Better suited for time-critical applications |

### Example: Railway System (CPN)
```
Scenario: Two trains share one track
Colors:   Train A = Red token, Train B = Blue token
Places:   Track Free, Train Waiting, Train On Track

Instead of two separate nets, one CPN handles both trains
using color-coded tokens.
```

---

## 11. Linear Programming

### Definition
**Linear Programming (LP)** is a mathematical method to find the **optimal solution** (maximum profit or minimum cost) subject to linear constraints.

### Components

| Component | Description | Example |
|---|---|---|
| **Decision Variables** | What we control | x = tables, y = chairs |
| **Objective Function** | What we optimize | Maximize Z = 50x + 30y |
| **Constraints** | Resource limitations | 2x + y ≤ 100 (wood), x + y ≤ 80 (labor) |
| **Non-negativity** | Values must be ≥ 0 | x ≥ 0, y ≥ 0 |

### Graphical Method – Step by Step

```
Step 1: Write Objective Function:      Z = 50x + 30y
Step 2: Write Constraints:             2x + y ≤ 100
                                        x + y ≤ 80
Step 3: Convert to Equalities:         2x + y = 100
                                        x + y = 80
Step 4: Find Corner Points (solve simultaneously)
Step 5: Compute objective value at each corner point
Step 6: Select the point with Maximum Z (or Minimum Z for cost)
```

### Sample Problem

**Problem:** Produce Tables (x) and Chairs (y).
- Profit: Table = $50, Chair = $30
- Wood: 2x + y ≤ 100 | Labor: x + y ≤ 80

**Solution:**
```
From x + y = 80 → y = 80 - x
Substitute: 2x + (80-x) = 100 → x = 20, y = 60
Corner point: (20, 60)
Z = 50(20) + 30(60) = 1000 + 1800 = $2,800 ← Maximum Profit
```

---

## 12. Project Paper Structure & Requirements

### Project Timeline

| Week | Deliverable |
|------|------------|
| Week 1–3 | Problem Definition, Setting Objectives, Project Planning |
| Week 4–5 | Conceptual Model, Context Diagram, Activity Diagrams, UML, Process Flow |
| Week 6–7 | Model Development, Coding, Data Collection, Test Runs |
| Week 8 | Presentation & Revision |
| Week 9 | **Final Project Submission** |

### Required Project Paper Chapters

#### Chapter 1 – Introduction / Problem Definition
- Background of the study
- Problem statement
- Objectives (aligned with CO3)
- Scope and limitations
- Significance of the study

#### Chapter 2 – System Analysis & Literature Review
- Description of the real system being simulated
- Related studies and literature
- Identification of entities, resources, events
- Data collection and sources

#### Chapter 3 – Model Design & Conceptualization
- Conceptual framework / model overview
- **Use Case Diagram**
- **Process Flow / Flowchart**
- **Context Diagram**
- UML Diagrams (Activity, State Charts, Database)
- Assumptions made in the model

#### Chapter 4 – Model Implementation
- Simulation tool used (Arena / MATLAB / Python / Excel)
- Model translation details
- Code or Arena model screenshots
- Input data used (random number generation, distribution used)
- Verification results (was the model built correctly?)

#### Chapter 5 – Simulation Results & Analysis
- Simulation runs conducted
- Output data and statistics
- Charts and graphs of results
- Validation (does it match the real system?)
- Performance measures: waiting time, queue length, server utilization

#### Chapter 6 – Conclusion & Recommendations
- Summary of findings
- Answer to the problem statement
- Recommendations for the real system
- Future work suggestions

### Supporting Diagrams Required
- ✅ Context Diagram
- ✅ Use Case Diagram
- ✅ Activity Diagrams
- ✅ Flowchart of the simulation model
- ✅ Database diagrams (if applicable)
- ✅ UML State Chart
- ✅ Arena/MATLAB/Code screenshots
- ✅ Output graphs and tables

---

## 13. Assessment Rubrics

### Practice-Based Assessment Criteria

#### CO1 – Explain Modeling & Simulation (Laboratory Exam 1, Week 1–3)

| Grade | Score | Description |
|-------|-------|-------------|
| Excellent | 97–100 | Confidently and thoroughly explains the relationship between modeling, abstraction, and simulation |
| Very Good | 90–96 | Confidently explains with good understanding |
| Good | 83–89 | Explains with considerable understanding |
| Fair | 76–82 | Explains with minimal understanding |
| Poor | ≤75 | Unable to explain confidently |

#### CO2 – Develop a Model (Laboratory Exam 2, Week 4–5)

| Grade | Score | Description |
|-------|-------|-------------|
| Excellent | 97–100 | Shows extensive ability to develop a model representing interaction of events |
| Very Good | 90–96 | Shows sufficient ability |
| Good | 83–89 | Shows average ability |
| Fair | 76–82 | Shows fair ability |
| Poor | ≤75 | Unable to develop the model |

#### CO3 – Conduct Simulation (Final Exam – Project, Week 1–8)

| Grade | Score | Description |
|-------|-------|-------------|
| Excellent | 97–100 | Strong ability to conduct simulation and test model effectiveness as decision-making guide |
| Very Good | 90–96 | Considerable ability |
| Good | 83–89 | Average ability |
| Fair | 76–82 | Some ability |
| Poor | ≤75 | Unable to conduct simulation |

### Assessment Weight Summary

| Assessment Task | CO1 | CO2 | CO3 |
|---|---|---|---|
| Written Quiz / Oral Recitation | 3% | 3% | 4% |
| Laboratory Exercises | 5% | 5% | 10% |
| Laboratory Quiz | 3% | 3% | 4% |
| Research | — | — | 20% |
| Written Exam | 10% (E1) | 10% (E2) | 10% (E3) + 40% (E4) |
| Laboratory Exam | 15% (E1) | 15% (E2) | 40% (E3) |

---

## 📝 Quick Reference: Key Formulas

| Formula | Use |
|---|---|
| `Z = (X - μ) / σ` | Normal distribution standardization |
| `P(X=k) = C(n,k) p^k (1-p)^(n-k)` | Binomial distribution |
| `P(X=k) = e^(-λ) λ^k / k!` | Poisson distribution |
| `P(X=k) = (1-p)^(k-1) × p` | Geometric distribution |
| `P(X > t) = e^(-λt)` | Exponential distribution (survival) |
| `P(X < x) = 1 - e^(-(x/λ)^k)` | Weibull CDF |
| `E(X) = α / (α + β)` | Beta distribution mean |
| `E(X) = e^(μ + σ²/2)` | Lognormal distribution mean |
| `Z = c₁x₁ + c₂x₂` | Linear programming objective function |
| `Server Utilization = (Busy Time / Total Time) × 100` | Queueing performance |

---

## ⚠️ Academic Policies
1. **No cheating or plagiarism** — Copying from any source (including ChatGPT) verbatim is prohibited.
2. **Base-15 grading** — Students with failing exam scores are recommended for tutorial/intervention.
3. Refer to the **Student Handbook** for other guidelines.

---

*Prepared based on CSE 10/L Course Syllabus (August 7, 2023) and Discussion Materials | University of Mindanao*
