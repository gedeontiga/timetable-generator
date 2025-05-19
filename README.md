# 📅 Timetable Generator for University of Yaounde I

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Google OR-Tools](https://img.shields.io/badge/Google%20OR--Tools-CP--SAT-orange)
![License](https://img.shields.io/badge/License-MIT-green)

Welcome to the **Timetable Generator**, a robust and flexible software system designed for the Department of Computer Science at the University of Yaounde I. This tool automatically generates class timetables that adhere to strict scheduling constraints while optimizing for early time slots (before noon). Built with Google OR-Tools' CP-SAT solver, it ensures efficient, conflict-free scheduling for classes, courses, teachers, and rooms.

---

## 🎯 Project Overview

The Timetable Generator addresses the scheduling needs of the Department of Computer Science, ensuring:

- **No Conflicts**: No class is scheduled for multiple courses simultaneously.
- **Weekly Scheduling**: Each course is scheduled exactly once per week.
- **Curriculum Compliance**: Only courses from a class’s curriculum are included.
- **Early Scheduling**: Maximizes classes before noon for better student and faculty experience.

The system uses a constraint programming approach, leveraging data from `rooms.json` and `subjects.json`, and schedules across 6 days and 5 periods per day.

---

## ✨ Features

- **Constraint-Based Scheduling**: Ensures no overlaps for classes, teachers, or rooms.
- **Optimization**: Prioritizes early periods (7:00 AM–12:55 PM) using a weighted cost function.
- **Robust Data Handling**: Gracefully manages missing or incomplete data (e.g., unknown lecturers).
- **Flexible Design**: Easily adaptable to new semesters, additional constraints, or different room counts.
- **User-Friendly Output**: Generates clear, readable timetables with day, period, and room assignments.

---

## 🛠️ Installation

### Prerequisites

- **Python 3.8+**: Ensure Python is installed.
- **Google OR-Tools**: Install the OR-Tools library for constraint programming.
- **Input Files**: Ensure `rooms.json` and `subjects.json` are in the project directory.

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/gedeontiga/timetable-generator.git
   cd timetable-generator
   ```
2. Install dependencies:
   ```bash
   pip install ortools
   ```
3. Place `rooms.json` and `subjects.json` in the project root.

---

## 🚀 Usage

Run the script to generate a timetable:

```bash
python timetable_generator.py
```

### Example Output

```
Timetable Generated:

Class Level 1:
  Course INF111: Day 1, Period 7:00am-9:55am, Room A1001
  Course INF121: Day 2, Period 10:05am-12:55pm, Room A1002
  ...

Class Level 2:
  Course INF211: Day 1, Period 10:05am-12:55pm, Room A250
  ...

Total Cost (lower is earlier): 45
```

The output lists each course’s assigned day, period, and room, optimized to minimize scheduling in later periods.

---

## 🧠 Implementation Details

### Mathematical Model

The timetable is modeled as a constraint optimization problem:

- **Entities**:

  - **Classes**: Levels 1, 2, 3.
  - **Courses**: From `subjects.json` (e.g., INF111 for Level 1).
  - **Teachers**: Extracted from "Course Lecturer" fields.
  - **Rooms**: 16 rooms from `rooms.json`.
  - **Time Slots**: 6 days × 5 periods (30 slots total).

- **Decision Variables**:

  - For each class \( c \) and course \( s \):
    - \( day\_{c,s} \): Day (0–5).
    - \( period\_{c,s} \): Period (0–4).
    - \( room\_{c,s} \): Room (0–15).

- **Constraints**:

  - **Class Exclusivity**: No class has multiple courses at the same time.
  - **Teacher Exclusivity**: No teacher is double-booked.
  - **Room Exclusivity**: No room hosts multiple courses simultaneously.
  - **Curriculum Compliance**: Only valid courses are scheduled.
  - **Once per Week**: Each course is scheduled exactly once.

- **Objective**:
  - Minimize \( \sum*{c,s} w*{period\_{c,s}} \), where weights \( w = [1, 2, 3, 4, 5] \) prioritize earlier periods.

### Technology Stack

- **Google OR-Tools CP-SAT**: Efficiently solves the constraint satisfaction problem.
- **Python**: Handles data processing and model implementation.
- **JSON**: Input data format for rooms and courses.

### Robustness & Flexibility

- **Error Handling**: Manages missing lecturer names or invalid course codes.
- **Scalability**: Supports additional classes, rooms, or constraints.
- **Time Limit**: Solver capped at 60 seconds to prevent hangs.

---

## 📝 Example Code

Below is a snippet of the core scheduling logic:

```python
from ortools.sat.python import cp_model

# Initialize model
model = cp_model.CpModel()

# Define variables
day = {c: {s: model.NewIntVar(0, 5, f'day_{c}_{s}') for s in S_c[c]} for c in classes}
period = {c: {s: model.NewIntVar(0, 4, f'period_{c}_{s}') for s in S_c[c]} for c in classes}
room = {c: {s: model.NewIntVar(0, 15, f'room_{c}_{s}') for s in S_c[c]} for c in classes}

# Add constraints (example: class exclusivity)
for c in classes:
    for d in range(6):
        for p in range(5):
            model.AddAtMostOne([(day[c][s] == d) & (period[c][s] == p) for s in S_c[c]])

# Objective: Minimize total period weights
w = [1, 2, 3, 4, 5]
cost = {c: {s: model.NewIntVar(1, 5, f'cost_{c}_{s}') for s in S_c[c]} for c in classes}
for c in classes:
    for s in S_c[c]:
        model.AddElement(period[c][s], w, cost[c][s])
model.Minimize(sum(cost[c][s] for c in classes for s in S_c[c]))

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0
status = solver.Solve(model)
```

For the full code, see `timetable_generator.py`.

---

## 🤝 Contributing

We welcome contributions to enhance the Timetable Generator! To contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/YourFeature`).
3. Commit changes (`git commit -m 'Add YourFeature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a Pull Request.

Please ensure your code follows PEP 8 guidelines and includes tests.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📬 Contact

For questions or feedback, contact the Department of Computer Science at the University of Yaounde I or open an issue on GitHub.

🌟 **Happy Scheduling!** 🌟
