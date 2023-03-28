from datetime import datetime

user_history = {}


def add_to_history(user_id, city):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append((city, timestamp))


def get_history(user_id):
    if user_id not in user_history or not user_history[user_id]:
        history_text = "История пуста."
    else:
        history_text = "История запросов:\n"
        for city, timestamp in user_history[user_id]:
            history_text += f"{timestamp}: {city}\n"

    return history_text
