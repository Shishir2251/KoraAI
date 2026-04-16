from tools.employee_dashboard import (
    get_my_appointments_today,
    get_my_leave_status,
    get_my_leave_balance,
    get_single_leave_status,
)
from tools.booking import (
    check_availability,
    get_all_schedules,
    get_appointments_by_date,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
)
from tools.employees import (
    invite_employee,
    get_all_employees,
    get_employee_by_id,
    update_employee,
    delete_employee,
    toggle_employee_status,
)
from tools.leave import apply_for_leave, check_leave_status
from tools.notifications import notify_staff

all_tools = [
    get_my_appointments_today,
    get_my_leave_status,
    get_my_leave_balance,
    get_single_leave_status,
    check_availability,
    get_all_schedules,
    get_appointments_by_date,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
    invite_employee,
    get_all_employees,
    get_employee_by_id,
    update_employee,
    delete_employee,
    toggle_employee_status,
    apply_for_leave,
    check_leave_status,
    notify_staff,
]