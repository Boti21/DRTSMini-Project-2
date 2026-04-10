This document serves as a comprehensive technical brief for an AI Agent to develop **Mini-project 2** for the **02225 Distributed Real-Time Systems (DRTS)** course.

---

# Technical Specification: TSN CBS Analysis & Simulation Tool

## 1. Project Objective
Develop a software suite to analyze and simulate **Worst-Case Response Times (WCRT)** for Audio-Video Bridging (AVB) streams in a Time-Sensitive Network (TSN). The goal is to validate a mathematical analytical model against a discrete-event simulation and compare the **Credit-Based Shaper (CBS)** against **Strict Priority (SP)**.

## 2. Input Data Specifications
The system must parse four primary JSON files based on the `tsn-test-cases` repository format, found here https://github.com/paulpop/tsn-test-cases/tree/main.

### A. Topology (`topology.json`)
*   **Nodes:** `switches` and `end_systems`.
*   **Links:** Unidirectional connections.
    *   `source`, `destination`, `bandwidth_mbps`, `delay` (propagation delay).
    *   *Important:* 100 Mbps or 1000 Mbps links are common. Bandwidth determines transmission time ($C = \text{size} / \text{bandwidth}$).

### B. Streams (`streams.json`)
*   **Properties:** `id`, `source`, `destinations` (with `deadline`), `PCP` (Priority Code Point), `size` (bytes), `period` ($\mu s$).
*   **Mapping:** PCP values determine which queue a stream enters.

### C. Routes (`routes.json`)
*   **Paths:** A hardcoded sequence of nodes and egress ports for each `flow_id`.
*   **Logic:** The tool must follow these paths; do not implement autonomous routing.

### D. Switch Configuration (`switch_config.json`)
*   **Queue Mapping:** Maps `PCP_list` to `queue_index`.
*   **Shaper Parameters:** Defines the `shaper_type` (CBS or StrictPriority).
*   **CBS Parameters:** `idle_slope` and `send_slope`. (Standard convention: `idle_slope` + `send_slope` = port rate).

---

## 3. High-Level Architecture

### Layer 1: The Parser & Object Model
*   **Parser:** Reads JSON files and builds a Graph representation of the network.
*   **Model:**
    *   `Link` objects contain three `Queue` objects: **Class A (CBS)**, **Class B (CBS)**, and **Best Effort (SP)**.
    *   `Stream` objects calculate their own transmission time ($C$) per link based on the link's bandwidth.

### Layer 2: Analytical Engine (WCRT Calculator)
Implement the "Independent Tight WCRT Analysis" (Cao et al., 2016).
*   **End-to-End WCRT:** $WCRT_i = \sum_{l \in path} (WCRT_{link, l} + \text{propagation\_delay}_l)$.
*   **Per-Link WCRT Components:**
    1.  **$C_i$:** Transmission time of the frame itself.
    2.  **SPI (Same-Priority Interference):** Delay from other frames in the same queue, including credit recovery time.
    3.  **HPI (Higher-Priority Interference):** For Class B, the impact of Class A bursts.
    4.  **LPI (Lower-Priority Interference/Blocking):** Time to finish a lower-priority frame (Max Ethernet frame = 1500 bytes) if it started just before the arrival.

### Layer 3: Simulation Engine (Discrete Event Simulator)
Build a simulator to track frames across time.
*   **Events:** `FrameArrival`, `TransmissionStart`, `TransmissionEnd`, `CreditUpdate`.
*   **CBS State Machine:**
    *   While transmitting: `credit -= send_slope * time`.
    *   While waiting with frames in queue: `credit += idle_slope * time`.
    *   While idle (no frames): `credit` moves toward 0.
    *   **Gate Condition:** A frame can only start if `credit >= 0` AND the link is idle AND it is the highest priority eligible frame.
*   **Metric Collection:** Track the actual entry-to-exit time for every frame to find the `observed_max_delay`.

### Layer 4: Comparative Evaluator
*   Run the same scenario twice: once with CBS and once with Strict Priority.
*   Compare Analytical WCRT vs. Simulated Max Delay.

---

## 4. Technical Logic & Formulas

### CBS Parameters (Standardized)
*   $bw$: Port Bandwidth.
*   $R$: Reserved bandwidth for the class.
*   $idleSlope = R$.
*   $sendSlope = R - bw$.

### Analytical Bound (Simplified)
For a class $M$ (Medium priority) interfered by $H$ (High) and $L$ (Low):
$$WCRT_{int} = WCRT_{no-int} + LPI_{blocking} \cdot (1 + \frac{idleSlope_H}{sendSlope_H}) + C_{max, H}$$
*(Refer to Cao 2016, Theorem 3 for the precise Tight WCRT recurrence).*

---

## 5. AI Agent Task List

1.  **Core Framework:** Create the data structures for Nodes, Links, Queues (with Credit tracking), and Streams.
2.  **JSON Parser:** Implement a robust loader for the `test-case-1` files. Ensure you handle the mapping in `switch_config.json` correctly.
3.  **Analytical Tool:** Implement the WCRT math. Output a table of `StreamID | LinkID | WCRT_link`.
4.  **Simulation Tool:** 
    *   Implement a priority scheduler for each output port.
    *   Implement the CBS credit logic (slopes and zeroing).
    *   Implement non-preemptive blocking (LPI).
    *   Run simulation until 1,000,000 $\mu s$ (or a sufficient hyperperiod).
5.  **Validation:** Create a script that compares the two results.
    *   Requirement: `Analytical WCRT >= Simulated Max Delay`.
6.  **SP vs CBS:** Implement a toggle to switch CBS queues to Strict Priority and measure the impact on Best Effort (Queue 0) starvation.

## 6. Verification Test Case (`test-case-1`)
*   **Topology:** 2 Switches, 2 End Systems.
*   **Streams:** IDs 0-9 with varying PCPs.
*   **Expected Analytical WCRTs:**
    *   Stream 0: ~603.2 $\mu s$
    *   Stream 4: ~884.48 $\mu s$
*   *Note:* The tool is successful if simulation results are close to, but do not exceed, these analytical values.

---
**End of Specification**

**Implementation Example (PseudoCode)**
```python 
class TSNPort:
    def step(self, dt):
        # 1. Update active transmission
        if self.link_busy:
            self.remaining_time -= dt
            # Update credit for the queue currently sending
            self.queues[self.active_queue_idx].credit += self.queues[self.active_queue_idx].send_slope * dt
            
            if self.remaining_time <= 0:
                self.link_busy = False
                return self.currently_sending_frame # Output the frame
        
        # 2. Update credits for waiting queues
        for q in self.cbs_queues:
            if not q.is_transmitting and q.has_frames():
                q.credit += q.idle_slope * dt
            elif q.is_empty() and q.credit != 0:
                # Logic to reset/recover credit to zero
                pass

        # 3. Schedule next frame if link is free
        if not self.link_busy:
            for i, q in enumerate(self.priority_sorted_queues):
                if q.has_frames() and (q.type == "BE" or q.credit >= 0):
                    self.start_transmission(q, i)
                    break
```