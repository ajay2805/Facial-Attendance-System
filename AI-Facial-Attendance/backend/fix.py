import sys, re

with open('views.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = r'        punch_type = "In"\n\n        if log:\n.*?else:\n            # FIRST PUNCH IN today.*?work_status="Present"\n            \)'

replacement = """        punch_type = "In"

        if log:
            return JsonResponse({"error": "Attendance already marked for today."}, status=400)
        else:
            # FIRST PUNCH IN today
            log = TimeLog.objects.create(
                employee=employee,
                organization=employee.organization,
                punch_date=today,
                punch_in_time=now_dt.time(),
                initial_punch_in=now_dt.time(),
                punch_out_time=now_dt.replace(hour=17, minute=30).time(),
                status="Out",
                work_status="Present",
                total_hours=8
            )"""

new_text = re.sub(target, replacement, text, flags=re.DOTALL)
if new_text != text:
    with open('views.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print('Replaced successfully')
else:
    print('Failed to replace.')
