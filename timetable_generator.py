import json
from ortools.sat.python import cp_model

# Load JSON data 
with open('assets/rooms.json') as f: rooms_data = json.load(f)
with open('assets/subjects.json') as f: subjects_data = json.load(f)

# Parameters
D = 6
P = 5
w = [1, 2, 3, 4, 5]
M = 2  # Limit to 2 rooms

# Extract data
classes = ['1']
S_c = {'1': ['INF111', 'INF121']}  # Limit to 2 courses
teacher_of = {('1', 'INF111'): 'ATSA', ('1', 'INF121'): 'KOUOKAM'}
teachers = set(teacher_of.values())
S_t = {t: [(c, s) for (c, s) in teacher_of if teacher_of[(c, s)] == t] for t in teachers}

# Create CP model
model = cp_model.CpModel()

# Variables
day = {c: {s: model.NewIntVar(0, D-1, f'day_{c}_{s}') for s in S_c[c]} for c in classes}
period = {c: {s: model.NewIntVar(0, P-1, f'period_{c}_{s}') for s in S_c[c]} for c in classes}
room = {c: {s: model.NewIntVar(0, M-1, f'room_{c}_{s}') for s in S_c[c]} for c in classes}
is_scheduled = {
    c: {
        s: {
            d: {p: model.NewBoolVar(f'is_scheduled_{c}_{s}_{d}_{p}') for p in range(P)}
            for d in range(D)
        } for s in S_c[c]
    } for c in classes
}

# Link is_scheduled to day and period
for c in classes:
    for s in S_c[c]:
        for d in range(D):
            for p in range(P):
                model.Add(day[c][s] == d).OnlyEnforceIf(is_scheduled[c][s][d][p])
                model.Add(period[c][s] == p).OnlyEnforceIf(is_scheduled[c][s][d][p])
                model.Add(day[c][s] != d).OnlyEnforceIf(is_scheduled[c][s][d][p].Not())
                model.Add(period[c][s] != p).OnlyEnforceIf(is_scheduled[c][s][d][p].Not())

# Constraints
# 1. Class exclusivity
for c in classes:
    for d in range(D):
        for p in range(P):
            model.AddAtMostOne([is_scheduled[c][s][d][p] for s in S_c[c]])

# 2. Teacher exclusivity
for t in teachers:
    for d in range(D):
        for p in range(P):
            model.AddAtMostOne([is_scheduled[c][s][d][p] for (c, s) in S_t[t]])

# 3. Room exclusivity (corrected)
for r in range(M):
    for d in range(D):
        for p in range(P):
            bool_vars = []
            for c in classes:
                for s in S_c[c]:
                    is_room_and_time = model.NewBoolVar(f'is_room_{r}_{c}_{s}_{d}_{p}')
                    model.Add(room[c][s] == r).OnlyEnforceIf(is_room_and_time)
                    model.Add(is_scheduled[c][s][d][p] == 1).OnlyEnforceIf(is_room_and_time)
                    model.Add(room[c][s] != r).OnlyEnforceIf(is_room_and_time.Not())
                    model.Add(is_scheduled[c][s][d][p] == 0).OnlyEnforceIf(is_room_and_time.Not())
                    bool_vars.append(is_room_and_time)
            model.AddAtMostOne(bool_vars)

# Objective
cost = {c: {s: model.NewIntVar(min(w), max(w), f'cost_{c}_{s}') for s in S_c[c]} for c in classes}
for c in classes:
    for s in S_c[c]:
        model.AddElement(period[c][s], w, cost[c][s])
total_cost = sum(cost[c][s] for c in classes for s in S_c[c])
model.Minimize(total_cost)

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300.0
status = solver.Solve(model)
print(f"Solver Status: {solver.StatusName(status)}")

# Output
period_times = ['7:00am-9:55am', '10:05am-12:55pm', '1:05pm-3:55pm', '4:05pm-6:55pm', '7:05pm-9:55pm']
room_nums = [room['num'] for room in rooms_data['Informatique']]
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print('Timetable Generated:')
    for c in classes:
        print(f'\nClass Level {c}:')
        for s in S_c[c]:
            d = solver.Value(day[c][s])
            p = solver.Value(period[c][s])
            r = solver.Value(room[c][s])
            print(f'  Course {s}: Day {d}, Period {period_times[p]}, Room {room_nums[r]}')
    print(f'\nTotal Cost (lower is earlier): {solver.ObjectiveValue()}')
else:
    print('No feasible solution found within time limit.')