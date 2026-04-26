# from tools.booking import (
#     get_available_slots,
#     create_appointment,
#     get_my_appointments,
#     get_my_appointments_by_date,
#     get_single_appointment,
#     reschedule_appointment,
#     cancel_appointment,
# )
# from tools.employee_dashboard import (
#     get_my_appointments_today,
#     get_my_appointment_calendar,
#     get_my_leave_status,
#     get_my_leave_balance,
#     get_single_leave_status,
# )
# from tools.leave import apply_for_leave, check_leave_status
# from tools.notifications import notify_staff

# all_tools = [
#     # User — full booking flow
#     get_available_slots,
#     create_appointment,
#     get_my_appointments,
#     get_my_appointments_by_date,
#     get_single_appointment,
#     reschedule_appointment,
#     cancel_appointment,
#     # Employee — view only
#     get_my_appointments_today,
#     get_my_appointment_calendar,
#     get_my_leave_status,
#     get_my_leave_balance,
#     get_single_leave_status,
#     # Leave — apply only (employee submits, manager approves)
#     apply_for_leave,
#     check_leave_status,
#     # Utility
#     notify_staff,
# ]



from tools.booking import make_booking_tools
from tools.employee_dashboard import make_employee_tools
from tools.leave import make_leave_tools
from tools.notifications import notify_staff

# all_tools is now built per session inside agent.py using build_kora()
# This file only exports the factory functions and notify_staff

__all__ = [
    "make_booking_tools",
    "make_employee_tools",
    "make_leave_tools",
    "notify_staff",
]