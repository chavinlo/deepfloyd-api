from main import tokens

def fail(r = None, c = None):
    return {"status": "fail", "reason": r, "content": c}
def succ(r = None, c = None):
    return {"status": "succ", "reason": r, "content": c}

#on solaris this checks against the db, but since this is just for the oss repo
def check_token_existance(token: str):
    if token in tokens:
        return True
    else:
        return False