from tools.booking import (
    get_available_slots,
    create_appointment,
    get_my_appointments,
    get_single_appointment,
    reschedule_appointment,
    cancel_appointment,
    update_appointment_status_employee,
)
from tools.employee_dashboard import (
    get_my_appointments_today,
    get_my_appointment_calendar,
    get_my_leave_status,
    get_my_leave_balance,
    get_single_leave_status,
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
    # User — appointment booking flow
    get_available_slots,
    create_appointment,
    get_my_appointments,
    get_single_appointment,
    reschedule_appointment,
    cancel_appointment,
    # Employee — appointment management
    get_my_appointments_today,
    get_my_appointment_calendar,
    update_appointment_status_employee,
    # Employee — leave
    get_my_leave_status,
    get_my_leave_balance,
    get_single_leave_status,
    apply_for_leave,
    check_leave_status,
    # Admin — employee management
    invite_employee,
    get_all_employees,
    get_employee_by_id,
    update_employee,
    delete_employee,
    toggle_employee_status,
    # Notifications
    notify_staff,
]