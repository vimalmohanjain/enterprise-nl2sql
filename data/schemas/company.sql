CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    name TEXT,
    department_id INTEGER,
    salary REAL,
    FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
);

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    employee_id INTEGER,
    title TEXT,
    FOREIGN KEY(employee_id)
        REFERENCES employees(employee_id)
);