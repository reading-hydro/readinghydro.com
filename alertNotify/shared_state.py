import threading


STATE_LOCK = threading.RLock()
_who_is_oncall = {'primary': 'Unknown', 'second': 'Unknown'}
_alert_log_list = []


def get_on_call_snapshot():
    with STATE_LOCK:
        return dict(_who_is_oncall)


def get_on_call_person(role):
    with STATE_LOCK:
        return _who_is_oncall.get(role)


def update_on_call_person(role, name):
    with STATE_LOCK:
        previous_name = _who_is_oncall.get(role)
        _who_is_oncall[role] = name
        return previous_name


def append_alert_log(timestamp, message):
    with STATE_LOCK:
        _alert_log_list.append({'time': timestamp, 'message': message})
        if len(_alert_log_list) > 30:
            del _alert_log_list[:-30]


def get_alert_log_snapshot():
    with STATE_LOCK:
        return [dict(entry) for entry in _alert_log_list]
