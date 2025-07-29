# HR Module Migration Utilities

This directory contains HR-specific migration utilities and scripts that complement the global Alembic setup.

## Purpose

While the main database migrations are handled by the global Alembic configuration in `/migrations/`, this directory serves for:

- **Data seeding scripts** specific to HR
- **Module-specific migration utilities**
- **Custom data transformation scripts**
- **HR schema documentation**

## Scripts

### Data Seeding
- `seed_default_departments.py` - Creates default department structure
- `seed_employee_roles.py` - Sets up standard employee roles
- `seed_hr_settings.py` - Initializes HR module configuration

### Utilities  
- `employee_data_import.py` - Bulk employee data import utilities
- `department_restructure.py` - Department reorganization helpers
- `performance_data_migration.py` - Performance review data migration

## Usage

These scripts are run independently of the main Alembic migrations:

```bash
# Run HR-specific data seeding
python app/modules/hr/migrations/seed_default_departments.py

# Import employee data
python app/modules/hr/migrations/employee_data_import.py --file employees.csv
```

## Note

For actual database schema changes (creating/modifying tables), use the global Alembic:

```bash
# From project root
alembic revision --autogenerate -m "HR: Add new employee fields"
alembic upgrade head
```
