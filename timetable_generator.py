import json
from ortools.sat.python import cp_model
from tabulate import tabulate
import time

# Load JSON data
with open('assets/rooms.json') as f:
    rooms_data = json.load(f)
with open('assets/subjects.json') as f:
    subjects_data = json.load(f)

# Define sets
classes = ['1', '2', '3', '4']
S_c = {}  # Courses per class
teacher_of = {}  # Teacher for (class, course)
course_name = {}  # Course name for display
course_credits = {}  # Credits for prioritizing high-credit courses
for c in classes:
    subjects = []
    for sem in ['s1', 's2']:
        subjects.extend(subjects_data['niveau'][c][sem]['subjects'])
    # Remove duplicates (e.g., INF4048) by keeping the first occurrence
    seen_codes = set()
    S_c[c] = []
    for subj in subjects:
        if subj.get('code') and subj['code'] and subj['name'] != "" and subj['code'] not in seen_codes:
            S_c[c].append(subj['code'])
            seen_codes.add(subj['code'])
            teacher = subj.get('Course Lecturer', [""])[0].strip()
            teacher = teacher if teacher else f"Unknown_{c}_{subj['code']}"
            teacher_of[(c, subj['code'])] = teacher
            course_name[subj['code']] = subj['name']
            course_credits[subj['code']] = subj.get('credit', 0)

teachers = set(teacher_of.values())
S_t = {t: [(c, s) for (c, s) in teacher_of if teacher_of[(c, s)] == t] for t in teachers}
M = len(rooms_data['Informatique'])  # Number of rooms
D = 6  # Days
P = 5  # Periods
T = D * P  # Total time slots (30)
w = [2, 1, 0, 0, 0]  # Weights for p1, p2 (morning), others 0
period_times = ['7:00-9:55', '10:05-12:55', '13:05-15:55', '16:05-18:55', '19:05-21:55']
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

# Diagnostics
total_courses = sum(len(S_c[c]) for c in classes)
max_courses = min(total_courses, T)  # Cap courses at available slots
print("=" * 80)
print("DIAGNOSTICS".center(80))
print("=" * 80)
print(f"Total Courses: {total_courses} (Capped at {max_courses} for {T} slots)")
print(f"Available Time Slots: {T} (Days: {D}, Periods: {P})")
print(f"Available Rooms: {M}")
print("\nCourses per Class:")
for c in classes:
    print(f"  Level {c}: {len(S_c[c])} courses")
print("\nTeachers with Multiple Courses (Potential Conflicts):")
for t in sorted(teachers):
    if len(S_t[t]) > 1:
        print(f"  {t}: {len(S_t[t])} courses {S_t[t]}")
if total_courses > T:
    print(f"\nWARNING: {total_courses} courses exceed {T} slots. {total_courses - T} will be unscheduled.")

# Create CP model
model = cp_model.CpModel()

# Decision variables
x = {}  # x[c][s][t][r] = 1 if class c, course s is at time t, room r
is_scheduled = {}  # Tracks if a course is scheduled
for c in classes:
    x[c] = {}
    is_scheduled[c] = {}
    for s in S_c[c]:
        x[c][s] = {}
        is_scheduled[c][s] = model.NewBoolVar(f'is_scheduled_{c}_{s}')
        for t in range(T):
            x[c][s][t] = {}
            for r in range(M):
                x[c][s][t][r] = model.NewBoolVar(f'x_{c}_{s}_{t}_{r}')

# Constraints
# 1. Each course scheduled at most once
for c in classes:
    for s in S_c[c]:
        model.Add(sum(x[c][s][t][r] for t in range(T) for r in range(M)) == is_scheduled[c][s])

# 2. No class overlap
for c in classes:
    for t in range(T):
        model.Add(sum(x[c][s][t][r] for s in S_c[c] for r in range(M)) <= 1)

# 3. No teacher overlap
for t in teachers:
    for t_slot in range(T):  # Renamed 'time' to 't_slot' to avoid shadowing
        model.Add(sum(x[c][s][t_slot][r] for (c, s) in S_t[t] for r in range(M)) <= 1)

# 4. No room overlap
for r in range(M):
    for t in range(T):
        model.Add(sum(x[c][s][t][r] for c in classes for s in S_c[c]) <= 1)

# Phase 1: Maximize scheduled courses
model.Maximize(sum(is_scheduled[c][s] * (100 + course_credits[s]) for c in classes for s in S_c[c]))  # Prioritize high-credit courses

# Solve Phase 1
solver = cp_model.CpSolver()
solver.parameters.num_search_workers = 8
solver.parameters.max_time_in_seconds = 300
solver.parameters.log_search_progress = False
solver.parameters.random_seed = 42  # Consistent results
solver.parameters.cp_model_presolve = True  # Enable presolve for efficiency

start_time = time.time()
status = solver.Solve(model)
phase1_time = time.time() - start_time

# Output Phase 1 Results
print("\n" + "=" * 80)
print("PHASE 1: MAXIMIZE SCHEDULED COURSES".center(80))
print("=" * 80)
print(f"Solver Status: {solver.StatusName(status)}")
print(f"Time Taken: {phase1_time:.2f} seconds")
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    scheduled_count = sum(solver.Value(is_scheduled[c][s]) for c in classes for s in S_c[c])
    print(f"Scheduled Courses: {scheduled_count}/{total_courses}")
else:
    print("No feasible solution found. Likely causes:")
    print(f"- Too many courses ({total_courses} vs. {T} slots)")
    print("- Teacher conflicts (check multiple assignments above)")
    print("- Insufficient rooms (unlikely with 16 rooms)")
    print("Suggestions: Reduce courses, add slots, or assign unique teachers.")
    print("=" * 80)
    exit()

# Phase 2: Optimize for morning periods
if scheduled_count > 0:
    # Fix scheduled courses
    for c in classes:
        for s in S_c[c]:
            model.Add(is_scheduled[c][s] == solver.Value(is_scheduled[c][s]))
    
    # New objective: Maximize morning periods
    model.Maximize(sum(w[t % P] * x[c][s][t][r]
                       for c in classes for s in S_c[c] for t in range(T) for r in range(M)))

    # Solve Phase 2
    solver.parameters.max_time_in_seconds = 300
    start_time = time.time()
    status = solver.Solve(model)
    phase2_time = time.time() - start_time

# Output Final Results
print("\n" + "=" * 80)
print("FINAL TIMETABLE RESULTS".center(80))
print("=" * 80)
print(f"Solver Status: {solver.StatusName(status)}")
print(f"Time Taken (Phase 2): {phase2_time:.2f} seconds")
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    scheduled_count = sum(solver.Value(is_scheduled[c][s]) for c in classes for s in S_c[c])
    morning_count = sum(solver.Value(x[c][s][t][r]) * w[t % P]
                       for c in classes for s in S_c[c] for t in range(T) for r in range(M))
    print(f"Objective Value: {solver.ObjectiveValue()}")
    print(f"Scheduled Courses: {scheduled_count}/{total_courses}")
    print(f"Morning Periods Scheduled: {morning_count}")
    print("\nScheduled Courses:")
    print("-" * 80)
    for c in classes:
        print(f"\nClass Level {c}:")
        table = []
        for s in sorted(S_c[c]):
            for t in range(T):
                for r in range(M):
                    if solver.Value(x[c][s][t][r]) == 1:
                        d = t // P
                        p = t % P
                        room_num = rooms_data['Informatique'][r]['num']
                        teacher = teacher_of[(c, s)]
                        table.append([
                            course_name[s],
                            s,
                            days[d],
                            f"P{p+1} ({period_times[p]})",
                            room_num,
                            teacher
                        ])
        if table:
            headers = ["Course Name", "Code", "Day", "Period", "Room", "Teacher"]
            print(tabulate(table, headers=headers, tablefmt="fancy_grid"))
        else:
            print("  No courses scheduled for this class.")

    # Unscheduled courses
    print("\nUnscheduled Courses:")
    print("-" * 80)
    unscheduled_table = []
    for c in classes:
        for s in S_c[c]:
            if solver.Value(is_scheduled[c][s]) == 0:
                teacher = teacher_of[(c, s)]
                reason = "Insufficient time slots or teacher/room conflict"
                if len(S_t[teacher]) > T:
                    reason = f"Teacher {teacher} has too many courses ({len(S_t[teacher])})"
                unscheduled_table.append([c, course_name[s], s, teacher, reason])
    if unscheduled_table:
        headers = ["Level", "Course Name", "Code", "Teacher", "Reason"]
        print(tabulate(unscheduled_table, headers=headers, tablefmt="fancy_grid"))
    else:
        print("  All courses scheduled successfully.")

    # Conflict Analysis
    print("\n" + "-" * 80)
    print("CONFLICT ANALYSIS".center(80))
    print("-" * 80)
    print("Time Slot Usage:")
    slot_usage = {}
    for t in range(T):
        d = t // P
        p = t % P
        slot_key = f"{days[d]} P{p+1}"
        slot_usage[slot_key] = {'classes': 0, 'rooms': []}
        for c in classes:
            for s in S_c[c]:
                for r in range(M):
                    if solver.Value(x[c][s][t][r]) == 1:
                        slot_usage[slot_key]['classes'] += 1
                        slot_usage[slot_key]['rooms'].append(rooms_data['Informatique'][r]['num'])
    table = [[slot, data['classes'], ', '.join(data['rooms'])] for slot, data in slot_usage.items() if data['classes'] > 0]
    if table:
        headers = ["Time Slot", "Classes Scheduled", "Rooms Used"]
        print(tabulate(table, headers=headers, tablefmt="fancy_grid"))
    else:
        print("  No slots assigned.")
else:
    print("No feasible solution found.")
    print(f"Reasons: Likely {total_courses} courses exceed {T} slots, or teacher/room conflicts.")
    print("Suggestions: Reduce courses, add slots, or assign unique teachers/rooms.")
print("=" * 80)