from sqlalchemy import create_engine


def connect(user, password, host, db, port='5439'):
    conStr = 'postgresql://' + user + ':' + password + '@' + host + ':' + port + '/' + db
    con = create_engine(conStr)
    return con
