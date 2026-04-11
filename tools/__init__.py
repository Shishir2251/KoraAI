from tools.appointments import (
    get_appointments,
    create_appointment,
    reschedule_appointment,
    cancel_appointment,
)
from tools.slots import get_available_slots
from tools.leave import apply_for_leave, check_leave_status
from tools.employees import get_employee_info, list_employees
from tools.notifications import notify_staff

all_tools = [
    get_appointments,
    create_appointment,
    reschedule_appointment,
    cancel_appointment,
    get_available_slots,
    apply_for_leave,
    check_leave_status,
    get_employee_info,
    list_employees,
    notify_staff,
]