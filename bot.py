import requests
 
def send_msg(id, text):
    try:
        token = "5745625677:AAH8zJW4RW9R4wtUMsm45HjXZKkaZ2wyZ3c"
        chat_id = id
        url_req = "https://api.telegram.org/bot" + token + "/sendMessage" + "?chat_id=" + chat_id + "&text=" + text
        results = requests.get(url_req)
        return results
    except Exception as e:
        return False