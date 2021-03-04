import os
import sys
import json
import time
import uuid
import base64
import sqlite3


import security_th as security
from logging_th import logger as log



# ======================================================================= encodeing and encryption ========================================================
# ----------------------------------------------------------------------- unsafe -------------------------------------------------------------------------



def de(a):
    try:
        a = base64.b64decode(str(a).encode('utf-8')).decode('utf-8')
    except:
        pass
    return a



# ----------------------------------------------------------------------- !unsafe -------------------------------------------------------------------------
# ----------------------------------------------------------------------- encodins -------------------------------------------------------------------------



# base64 encode messages
def b(a):
    return base64.b64encode(str(a).encode('utf-8')).decode('utf-8')


# base64 decode messages
def d(a):
    return base64.b64decode(str(a).encode('utf-8')).decode('utf-8')



# ----------------------------------------------------------------------- !encodins -------------------------------------------------------------------------
# ======================================================================= !encodeing and encryption ========================================================


def database_execute(chatroom='', statement='', variables=()):
    chatroom = security.sanitize_uuid(chatroom)
    if not chatroom:
        return "invalid chatrom id format", 500


    if not os.path.exists(f'storage/chatrooms/{chatroom}/main.db'):
        return "Chatroom does not exist", 500


    try:
        db_connection = sqlite3.connect(f'storage/chatrooms/{chatroom}/main.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(statement, variables)
        data = db_cursor.fetchall()
        db_connection.commit()
        db_connection.close()

    except Exception as e:
        return f"Database operation failed: {e}", 500


    return data, 200


#=========================================================================================================================================================
















# ----------------------------------------------------------------------- !access ----------------------------------------------
# ----------------------------------------------------------------------- other ----------------------------------------------





# ----------------------------------------------------------------------- !other ----------------------------------------------
# ======================================================================= !users ========================================================













# ======================================================================= chatrooms ========================================================
# ----------------------------------------------------------------------- chatroom db ------------------------------------------------------
# ----------------------------------------------------------------------- setup and esting -------------------------------------------------





# ----------------------------------------------------------------------- setup and esting -------------------------------------------------











# ----------------------------------------------------------------------- !chatroom db ------------------------------------------------------
# ----------------------------------------------------------------------- maindb ------------------------------------------------------------



# save chatroom id and name in main.db
def save_chatroom(chatroomId, chatroom_name):
    if not chatroom_name or not chatroomId:
        return "Internal database error: could not get chatname or ID"

    try:
        chatroomId = b(chatroomId)
        chatroom_name = b(chatroom_name)


    except Exception as e:
        log(level='error', msg=f"[server/dbhandler.py/save_chatroom/0] could not encode chatroomId or chatroom_name\n Traceback: {e}")
        return f"could not encode chatroom_name", 400


    try:
        db_connection = sqlite3.connect(f'storage/main.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"INSERT INTO chatrooms VALUES (?, ?)", (chatroomId, chatroom_name))
        db_connection.commit()
        db_connection.close()


    except Exception as e:
        log(level='error', msg=f"[server/dbhandler.py/save_chatroom/1] database operation failed\n Traceback: {e}")
        return f"internal database error", 500


    return "OK", 200


# get the name of a chatroom from main.db
def get_chatname(chatroomId):
    try:
        chatroomId = b(chatroomId)
        db_connection = sqlite3.connect(f'storage/main.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"SELECT chatroom_name FROM chatrooms WHERE chatroomId = ?", (chatroomId,))
        data = db_cursor.fetchall()
        db_connection.close()



    except sqlite3.OperationalError as e:
        log(level='fail', msg=f'[server/dbhandler/get_nickname/0] database operation failed:  {e}')
        return "internal database error: database operation failed", 500



    try:
        print('chatroom_name: ',data )
        if len(data) > 0:
            chatroom_name = d(data[0][0])
        else:
            chatroom_name = None


    except Exception as e:
        log(level='fail', msg=f'[server/dbhandler/get_chatname/1] corrupted data in database:  {e}')
        return "internal database error: some values may be corrupted", 500


    return chatroom_name, 200


# delete a chatroom from the main.db
def delete_chatroom_main(chatroomId):
    try:
        chatroomId = b(chatroomId)


    except Exception as e:
        log(level='error', msg=f"[server/dbhandler.py/delete_chatroom_main/0] failed to encode chatroomId while deleting chatroom \n Traceback: {e}")
        return f"could not encode chatroom_name", 500


    try:
        log(level='warning', msg=f"[server/dbhandler/delete_chatroom_main/1] deleting chatroom {d(chatroomId)}")
        db_connection = sqlite3.connect(f'storage/main.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"DELETE FROM chatrooms WHERE chatroomId = ?", (chatroomId,))
        db_connection.commit()
        db_connection.close()


    except Exception as e:
        log(level='error', msg=f"[server/dbhandler.py/save_chatroom/1] database operation failed\n Traceback: {e}")
        return f"internal database error", 500


    return "OK", 200



# ----------------------------------------------------------------------- users ------------------------------------------------------------



# save chatroom ID to user entry in main.db
def user_save_chatroom(username, new_chatroom):
    if not username or not new_chatroom:
        log(level='fail', msg=f'[server/dbhandler/user_save_chatroom/0] user_save_chatroom did not get the required arguments')
        return "internal server error", 500

    try:
        username = b(username)
        # chatrooms arent encoded individually bc they are encoded as the whole list


    except:
        return "Internal server error: usernme could not be encoded", 500


    # get stored cookies
    try:
        db_connection = sqlite3.connect("storage/main.db")
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"SELECT chatrooms FROM users WHERE username = ?", (username,))
        chatrooms = db_cursor.fetchall()
        db_connection.close()


    # fail on sqlite errors. This usually happens when the server is run without properly set up databases
    except sqlite3.OperationalError as e:
        log(level='fail', msg=f'[server/dbhandler/user_save_chatroom/1] database operation getting chatrooms failed:  {e}')
        return "Internal database error: could not connect to database", 500


    # al users should have at least '[]' stored their chatrooms, if they dont then the database is corrupted somehow
    if len(chatrooms) == 0:
        log(level='error', msg=f'[server/dbhandler/user_save_chatroom/2] user does not exists or did not get initialized properly')
        return "Internal database error", 500


    # add new chatroomId to chatrooms list
    ## cookies are being stored as a list that has been converted to string, this makes it easy to add new cookies
    try:
        #decode
        chatrooms = d(chatrooms[0][0])

        #append
        chatrooms = json.loads(chatrooms)
        chatrooms.append(new_chatroom)
        chatrooms = json.dumps(chatrooms)

        # encode
        chatrooms = b(chatrooms)


    # if the cookies cannot be decoded/encoded than the data is malformed, which is a server issue
    except:
        log(level='error', msg=f'[server/dbhandler/user_save_chatroom/3] malformed chatroom data in databse')
        return "Internal database error", 500


    # update server with new cookes list
    try:
        db_connection = sqlite3.connect("storage/main.db")
        db_cursor = db_connection.cursor()
        db_cursor.execute(f'UPDATE users SET chatrooms = ? WHERE username = ?', (chatrooms, username))
        db_connection.commit()
        db_connection.close()


    # fail on sqlite errors. This usually happens when the server is run without properly set up databases
    except sqlite3.OperationalError as e:
        log(level='fail', msg=f'[server/dbhandler/user_save_chatroom/4] database operation, saving chatroom: failed:  {e}')
        return "Internal database error", 500


    # everything worked out fine
    return "OK", 200


# get all chatrooms a user is in
def user_get_chatrooms(username):
    try:
        username = b(username)

    except Exception as e:
        log(level='error', msg=f"[server/dbhandler/user_get_chatroms/0] username could not be encoded: {e}")
        return "internal server error", 500


    # get all  stored cookies of the user
    try:
        db_connection = sqlite3.connect(f'storage/main.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"SELECT chatrooms FROM users WHERE username = ?", (username,))
        data = db_cursor.fetchall()
        db_connection.close()



    except Exception as e:
        log(level='fail', msg=f'[server/dbhandler/user_get_chatroms/1] database operation failed:  {e}')
        return "internal database error", 500


    # chatrooms are stored in a base64 encoded str(list)
    if len(data) == 0:
        log(level='error', msg=f'[server/dbhandler/user_get_chatroms/2] user not initialized properly')
        return "internal database error", 500


    # decode and load the data as json
    try:
        data = d(data)
        data = json.loads(data)
    except:
        log(level='error', msg=f'[server/dbhandler/user_get_chatroms/3] failed to process chatrooms data of user {username}\n Data is probably corrupted')


    return data, 200


def delete_chatroom_from_user(username, chatroomId):
    try:
        username = b(username)
        # chatrooms arent encoded individually bc they are encoded as the whole list

    except Exception as e:
        log(level='fail', msg=f'[server/dbhandler/delete_chatroom_from_user/0] could not encode username for deleting chatroom\n Traceback: {e}')
        return "usernme could not be encoded", 500



    # get stored cookies
    try:
        db_connection = sqlite3.connect("storage/main.db")
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"SELECT chatrooms FROM users WHERE username = ?", (username,))
        chatrooms = db_cursor.fetchall()
        db_connection.close()



    # fail on sqlite errors. This usually happens when the server is run without properly set up databases
    except sqlite3.OperationalError as e:
        log(level='fail', msg=f'[server/dbhandler/delete_chatroom_from_user/1] database operation getting chatrooms failed:  {e}')
        return "Internal database error", 500



    # al users should have at least '[]' stored their chatrooms, if they dont then the database is corrupted somehow
    if len(chatrooms) == 0:
        log(level='error', msg=f'[server/dbhandler/user_save_chatroom/2] user does not exists or did not get initialized properly')
        return "Internal database error", 500



    # chatrooms are stored as a serialized list
    try:
        #decode
        chatrooms = d(chatrooms[0][0])

        #remove element
        chatrooms = json.loads(chatrooms)
        chatrooms.remove(chatroomId)
        chatrooms = json.dumps(chatrooms)

        # encode
        chatrooms = b(chatrooms)



    # if the cookies cannot be decoded/encoded than the data is malformed, which is a server issue
    except Exception as e:
        log(level='error', msg=f'[server/dbhandler/delete_chatroom_from_user/3] malformed chatroom data in databse\n Traceback: {e}')
        return "Internal database error: could not remove chatrom", 500



    # update server with new cookes list
    try:
        db_connection = sqlite3.connect("storage/main.db")
        db_cursor = db_connection.cursor()
        db_cursor.execute(f'UPDATE users SET chatrooms = ? WHERE username = ?', (chatrooms, username))
        db_connection.commit()
        db_connection.close()



    # fail on sqlite errors. This usually happens when the server is run without properly set up databases
    except sqlite3.OperationalError as e:
        log(level='fail', msg=f'[server/dbhandler/delete_chatroom_from_user/4] database operation failed while deleting chatroom from user\n Traceback: {e}')
        return "Internal database error", 500


    # everything worked out fine
    return "OK", 200



# ----------------------------------------------------------------------- !users ------------------------------------------------------------
# ----------------------------------------------------------------------- invites ------------------------------------------------------------



def save_invite(chatroomId, inviteId, expr_time, uses):
    if not chatroomId or not inviteId or not expr_time or not uses:
        log(level='error', msg="[server/dbhandler.py/save_invite/0] missing arguments to save_invite function")
        return "internal server error: missing arguments", 500


    # encode data: no sqli pls
    try:
        inviteId   = b(inviteId)
        chatroomId = b(chatroomId)
        # expr_time and uses are not encoded so we can do cool sql statements


    # could not encode the data for some reason
    except:
        return "Internal server error: [dbhanler/save_invite/1] failed to encode data", 500



    # save invite in database
    try:
        db_connection = sqlite3.connect(f'storage/main.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"INSERT INTO invites VALUES (?, ?, ?, ?)", (inviteId, chatroomId, expr_time, uses))
        db_connection.commit()
        db_connection.close()


    # database operation failed
    except Exception as e:
        log(level='error', msg=f'[server/dbhandler.py/save_invite/2] database operation failed: saving invite\n Traceback: {e}')
        return "Internal database error: could not connect to database"


    # ok
    return "OK", 200



def use_invite(inviteId):
    if not inviteId:
        log(level='error', msg="[server/dbhandler.py/use_invite/0] missing arguments to function")
        return "internal server error: missing arguments", 500


    # encode inviteId
    try:
        inviteId = b(inviteId)

    except Exception as e:
        log(level='warning', msg="[server/dbhandler.py/use_invite/1] inviteId could not be encoded\n Traceback: {e}")
        return "inviteID format incorrect", 400


    # get all invites that match the inviteID and are not expired or overused
    try:
        db_connection = sqlite3.connect(f'storage/main.db')
        db_cursor = db_connection.cursor()
        print(inviteId)
        db_cursor.execute(f"SELECT * FROM invites WHERE inviteId = ? ", (inviteId,))
        #db_cursor.execute(f"SELECT * FROM invites WHERE inviteId = ? AND (expr_time > ? OR expr_time = 0)", (inviteId, str(int(time.time()))))
        invite = db_cursor.fetchall()
        print('invite: ',invite , type(invite))
        db_connection.close()


    # database operation failed
    except Exception as e:
        log(level='error', msg=f'[server/dbhandler.py/use_invite/2] database operation failed: saving invite\n Traceback: {e}')
        return "Internal database error: could not connect to database", 500


    # check if there were any valid invites
    if len(invite) == 0:
        return "Invite ID incorrect or expired", 400


    # get data from the invite
    try:
        print('invite: ',invite , type(invite))
        invite = invite[0]
        print('invite: ',invite , type(invite))
        uses = int(invite[3])
        print('uses: ',uses , type(uses))
        chatroomId = d(invite[1])


    # somethings wrong with the database format
    except Exception as e:
        log(level='error', msg=f"[server/dbhandler/use_invite/3] error occured while processing invite database possibly corrupted\nTraceback: {e}")
        return "Internal databse error: could not process data from databse", 500


    # cehck if the invite is overused
    if uses > 0:
        uses = uses - 1
    else:
        return "invite cannot be used as it has exeeded its maximum capacity", 403


    # update the databse with the new value of 'uses'
    try:
        db_connection = sqlite3.connect(f'storage/main.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"UPDATE invites SET uses = ? WHERE inviteId = ?", (str(uses), inviteId))
        db_connection.commit()
        db_connection.close()


    # database operation failed
    except Exception as e:
        log(level='error', msg=f'[server/dbhandler.py/save_invite/2] database operation failed: saving invite\n Traceback: {e}')
        return "Internal database error: could not connect to database"



    # all is well
    return chatroomId, 200



# ----------------------------------------------------------------------- !maindb ------------------------------------------------------------
# ======================================================================= !chatrooms =======================================================













# ======================================================================= messages =======================================================
# ----------------------------------------------------------------------- testing --------------------------------------------------------



# get all messages in a chatroom
def get_all_messages(chatroomId, p=True):
    if not os.path.exists("storage/conv1"):
        return False

    # sanitize chatroom id used for path
    chatroomId_d, status_code = security.sanitize_chatroomId(chatroom_Id) # save non-encoded version for file path
    if status_code != 200:
        return chatroomId_d, status_code


    try:
        db_connection = sqlite3.connect(f'storage/{chatroomId_d}/chatroom.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"SELECT * FROM messages")
    except sqlite3.OperationalError as e:
        log(level='fail', msg=f'[server/dbhandler/get_all_messages/0] database operation failed:  {e}')
        return False

    a = db_cursor.fetchall()

    if p:
        for b in a:
            print(b)

    db_connection.close()

    return True



# ----------------------------------------------------------------------- !testing --------------------------------------------------------
# ----------------------------------------------------------------------- general --------------------------------------------------------



# save a message in the database (both texts and files)
def save_in_db(time=0, messageId=0, username=0, chatroomId=0, message_type=0, message=None, filename=None, extension=None ):
    if time == 0 or messageId == 0 or username == 0 or chatroomId == 0 or message_type == 0: #values marked with 0 are needed while ones marked with None are optional
        # making sure that all values that are needed exist
        log(level='error', msg='[server/dbhandler/save_in_db/0] one or more of the required fields passed to function "save_in_db" are not present [time, username, chatroomId, message_type]')
        return "internal server error", 500


    # sanitize chatroom id used for path
    chatroomId_d, status_code = security.sanitize_chatroomId(chatroomId) # save non-encoded version for file path
    if status_code != 200:
        return chatroomId_d, status_code


    # connect to the database
    try:
        db_connection = sqlite3.connect(f'storage/{chatroomId_d}/chatroom.db') # chatroomId is the folder name that data to do with chatroom resides in
        db_cursor = db_connection.cursor()


    # error: the database does not exists
    except:
        log(level='error', msg=f'[server/dbhandler/save_in_db/1] server could not connect to database')
        return "internal database error", 500


    # encode cumpolsary values
    try:
        username = b(username)
        messageId = b(messageId)
        chatroomId = b(chatroomId)
        message_type = b(message_type)


    # if this fails its bc the user sent bad data
    except:
        return "corrupted data sent to server", 400


    # encode non compulsary values
    if message: message = b(message)
    if filename: filename = b(filename)
    if extension: extension = b(extension)


    # save the new message
    try:
        db_cursor.execute(f"INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (time, messageId, username, chatroomId, message_type, message, filename, extension))
        db_connection.commit()
        db_connection.close()


    # fail on sqlite errors. This usually happens when the server is run without properly set up databases
    except sqlite3.OperationalError as e:
        log(level='fail', msg=f'[server/dbhandler/save_in_db/2] database operation failed:  {e}')
        return "internal database error", 500


    # all is well
    return "OK", 200


# get messages from db
def get_messages_db(last_time=0, chatroomId=''):
    chatroomId_d, status_code = security.sanitize_chatroomId(chatroomId) # sanitize chatroom id used for path
    if status_code != 200:
        return chatroomId_d, status_code


    try: # try connect to the db
        db_connection = sqlite3.connect(f'storage/{chatroomId_d}/chatroom.db') # chatroomId is the folder name that data to do with chatroom resides in
        db_cursor = db_connection.cursor()


    # db doesnt exist
    except:
        log(level='error', msg=f'[server/dbhandler/get_messages/0] server could not connect to database')
        return "internal server error", 500



    # time and chatroomId should not be encoded:
        # time shouldnt because its needed in sql queries with >=
        # chatroomId is just an id, and its not controllable by the client



    # get all messages that had been sent since 'last_time'
    try:
        db_cursor.execute("SELECT * FROM messages WHERE time >= ?", (last_time,))

        data = db_cursor.fetchall()
        db_connection.close()
    except sqlite3.OperationalError as e:
        log(level='fail', msg=f'[server/dbhandler/get_messages/1] database operation failed:  {e}')
        return "internal database error", 500


    # sqlite returns a list of lists, we should convert this back to json
    json_data = []

    # format messages for returning
    try:
        for element in data:
            nickname = get_nickname(d(element[2]))

            # get compulsary data, all but time need to be decoded
            send_time = element[0]
            messageId = d(element[1])
            username = d(element[2])
            chatroom = d(element[3])
            msg_type = d(element[4])

            # get optional data, they may or may not be present
            message = element[5]
            if message: message = d(message)
            filename = element[6]
            if filename: filename = d(filename)
            extension = element[7]
            if extension: extension = d(extension)

            # make return dict
            a = {
                'time': send_time,
                'messageId': messageId,
                'username': username,
                'nickname': nickname,
                'chatroom': chatroom,
                'type': msg_type,
                'message': message,
                'filename': filename,
                'extension': extension
                    }

            # add to list
            json_data.append(a)


    # message format error
    except Exception as e:
    #else:
        log(level='error', msg=f"[server/dbhandler/get_messages/2] some data in the database is corrupted and cannot be decoded\n Traceback: {e}")
        return "internal databse error", 500


    # all is well
    return json_data, 200



# ----------------------------------------------------------------------- !general --------------------------------------------------------
# ======================================================================= messages =======================================================












# ======================================================================= health check =======================================================
def check_databses():
    log(level='log', msg='running system checks')


    # check if storage folder exists
    log(level='log', msg='checking storage folder')

    # check if folder exists, and try to create it if not
    if not os.path.isdir("storage/"):
        try:
            log(level='warning', msg='[health check] creating storage folder')
            os.mkdir("storage")

        except Exception as e:
            return f"could not create storage folder: {e}\n Please make sure you have to correct permissions", 500




    # check main.db
    log(level='log', msg='checking main db')

    # does the main db exist?
    if not os.path.isfile('storage/main.db'):
        log(level='warning', msg=f'[health check] creating main.db')

        response, status_code = init_main_db()
        if status_code != 200:
            return f"failed to create main.db\n Traceback: {response}\n\n Suggest that you delete the 'storage' folder"


    # make sure the database is good by testing all tables
    try:
        db_connection = sqlite3.connect(f'storage/main.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"SELECT * FROM users")
        db_cursor.execute(f"SELECT * FROM chatrooms")
        db_cursor.fetchall()
        db_connection.close()


    # something is wrong with the database
    except Exception as e:
        return f"main database is missing tables or otherwise corrupted\n Traceback: {e}", 500


    log(level='success', msg='[health check] System is healthy :)')
    return "OK", 200






##########################################################################################################################################################################################################################################################################################
############################################################################# new stuff ##################################################################################################################################################################################################
##########################################################################################################################################################################################################################################################################################




#=================================================== init ==================================================



# create and setup chatroom.db
def init_chat(chatroomId):
    log(level='log', msg=f"[dbhandler/init_chat/0] creating chatroom: {chatroomId}")


    # create users table
    #                          |                       auth                          | settings | perms |
    sql = "CREATE TABLE users ('username', 'email', 'nickname', 'password', 'cookies', 'colour', 'admin')"
    data, status_code = database_execute(chatroomId, sql, ())
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/init_chat/1] || {data}")
        return "[dbhandler/init_chat/1] || Failed to create chatroom: Internal datase error", 500


    # create invites table
    sql = "CREATE TABLE invites ('inviteId', 'expr_time', 'uses')"
    data, status_code = database_execute(chatroomId, sql, ())
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/init_chat/2] || {data}")
        return "[dbhandler/init_chat/2] || Internal database error", status_code


    # create messages table
    #                          |                       general                    | type | message |          files         |
    sql = "CREATE TABLE messages ('time', 'messageId', 'username', 'chatroomId', 'type', 'message', 'filename', 'extension')"
    data, status_code = database_execute(chatroomId, sql, ())
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/init_chat/3] || {data}")
        return "[dbhandler/init_chat/3] || Failed to create chatroom: Internal datase error", 500


    # create settings table
    #                             |       setting general       | perms to change |
    sql = "CREATE TABLE settings ('setting_name', 'setting_value', 'need_admin')"
    data, status_code = database_execute(chatroomId, sql, ())
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/init_chat/4] || {data}")
        return "[dbhandler/init_chat/4] || Failed to create chatroom: Internal datase error", 500


    # set use email to false by default
    sql = "INSERT INTO settings VALUES ('?', '?', '?')"
    data, status_code = database_execute(chatroomId, sql, ("require_email", False, True))
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/init_chat/5] || {data}")
        return "[dbhandler/init_chat/5] || Failed to create chatroom: Internal datase error", 500


    return "OK", 200



#=================================================== !init =================================================
#===================================================  auth =================================================



# save details of a new user
#'username', 'email', 'nickname', 'password', 'cookies', 'colour', 'admin'
def save_new_user(username,nickname, password, chatroomId, email=None, admin=False):
    if not username or not nickname or not password or not chatroomId:
        log(level='error', msg=f"[dbhandler/save_new_user/0] || some required data was not passed to the function")
        return "[server/dbhandler/save_new_user/0] || Failed to register user: Internal server error", 500



    # encode data
    try:
        # encode data
        username = b(username)
        nickname = b(nickname)

        # email is not always compulsary
        if email != None:
            email = b(email)

        # hashpw
        password = b(security.hashpw(password))

        # save empty list of user cookies
        cookie = b(json.dumps([]))


        # colour is None by default
        colour = None


    # could not encode data
    except Exception as e:
        log(level='error', msg=f"[server/dbhandler/save_new_user/1] || Failed to encode/hash data\nTraceback: {e}")
        return "[server/dbhandler/save_new_user/1] || Failed to register user: Internal server error", 500



    # save user in database. format = 'username', 'email', 'nickname', 'password', 'cookies', 'colour', 'admin'
    sql = "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)"
    data, status_code = database_execute(chatroomId, sql, (username, email, nickname, password, cookie, colour, admin))
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/save_new_user/2] || Error occured while adding user to database: {data}")
        return "[dbhandler/save_new_user/2] || Failed to register user: Internal datase error", 500


    # everything okay
    return "OK", 200



# check if a username or email already exists (main purpose is to not register the same user 2x)
def check_user_exists(chatroomId, username=None, email=None):
    try:
        if username: username = b(username)
        if email: email = b(email)

    except:
        return "[server/dbhanler/check_user_exitst/0] username or email corrupt", 400


    # run slightly different checks depending on the data supplied
    if username and email:
        sql = "SELECT * FROM users WHERE username = ? OR email = ?"
        variables = (username,email)

    elif username and not email:
        sql = "SELECT * FROM users WHERE username = ? "
        variables = (username,)

    elif not username and email:
        sql = "SELECT * FROM users WHERE email = ?"
        variables = (email,)




    data, status_code = database_execute(chatroomId, sql, variables)
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/check_user_exitst/1] || Database operation failed {data}")
        return "[dbhandler/check_user_exitst/1] || Could not verify user: Internal datase error", 500



    if len(data) > 0:
        return True, 200
    else:
        return False, 200



# check username and password of user
def checkuser(chatroomId, username=None, email=None, password=None):
    if not password:
        return "[server/checkuser/0] || Login failed. no password sent", 400


    # email takes priority over username, so if email is present then use that for login
    if email != None:
        key = b(email)
        using = 'email'


    # if no email then login with username
    else: 
        key = b(username)
        using = 'username'


    # get password
    sql = f"SELECT password FROM users WHERE {using} = ?"
    data, status_code = database_execute(chatroomId, sql, (key,))
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/checkuser/1] || Failed to check user login: {data}")
        return "[dbhandler/checkuser/1] || Checking user failed: Internal database error", 500



    # if the user has a password, unwap it
    if len(data) > 0:
        storedPassword = d(data[0][0])
    else:
        return "[dbhandler/checkuser/2] || Login failed. Unrecognized username. Are you registered?", 401


    # check if the password is correct
    if security.checkpw(password, storedPassword):
        return "OK", 200
    else:
        return "[dbhandler/checkuser/3] || Login failed. Username/email or password is incorrect!", 401



# add a cookie to the users list of cookies
def store_cookie(chatroomId, username=None, email=None, new_cookie=None):
    if new_cookie == None: # check if the function was called without cookies, this should only happen if the sever code is broken
        log(level="error", msg=f'[server/dbhandler/store_cookie/0] function was called without a cookie supplied to it')
        return "[server/dbhandler/store_cookie/0] || Failed to verify user: Internal server error", 500


    # email takes priority over username, so if email is present then use that as the key
    if email != None:
        key = b(email)
        using = 'email'


    # if no email then key is username
    else: 
        key = b(username)
        using = 'username'



    sql = f"SELECT cookies FROM users WHERE {using} = ?"
    data, status_code = database_execute(chatroomId, sql, (key,))
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/store_cookie/1] || Failed to get cookies from database: {data}")
        return "[dbhandler/store_cookie/1] || login failed: Internal database error", 500

    cookies = data



    # al users should have at least '[]' stored as cookes, if they dont then the database is corrupted somehow
    if len(cookies) == 0:
        log(level='error', msg=f'[dbhandler/store_cookie/2] || user does not exists or did not get initialized properly\n (database cookies entry doesnt exist)')
        return "[dbhandler/store_cookie/2] || Login failed: Internal database error", 500


    # add new cookie to cookies list
    ## cookies are being stored as a list that has been converted to string, this makes it easy to add new cookies
    try:
        #decode
        cookies = d(cookies[0][0])

        #append
        cookies = json.loads(cookies)
        cookies.append(new_cookie)
        cookies = json.dumps(cookies)

        # encode
        cookies = b(cookies)


    # if the cookies cannot be decoded/encoded than the data is malformed, which is a server issue
    except:
        log(level='error', msg=f'[dbhandler/store_cookie/3] || malformed cookie data in databse')
        return "[dbhandler/store_cookie/3] || Login failed: Internal database error", 500



    sql = f'UPDATE users SET cookies = ? WHERE {using} = ?'
    data, status_code = database_execute(chatroomId, sql, (cookies, key))
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/store_cookie/3] || Failed update user cookies: {data}")
        return "[dbhandler/store_cookie/1] || login failed: Internal database error", 500


    # everything worked out fine
    return "OK", 200



# return all active cookies of a user
def get_cookies(chatroomId, username):
    try:
        username = b(username)
    except Exception as e:
        return "[dbhandler/get_cookies/0] username could not be encoded", 400


    # get all  stored cookies of the user
    sql = f"SELECT cookies FROM users WHERE username = ?",
    data, status_code = database_execute(chatroomId, sql, (username,))
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/get_cookies/1] || Failed to get cookies from database: {data}")
        return "[dbhandler/get_cookies/1] || Failed to verify user: Internal database error", 500


    # cookies are stored in a base64 encoded str(list)
    if len(data) == 0:
        return False


    # decode and load the data as json
    try:
        data = d(data)
        data = json.loads(data)
    except:
        log(level='error', msg=f'[server/dbhandler/get_cookies/2] failed to process cookie data of user {username}\n Data is probably corrupted')
        return False

    return data



#=================================================== !auth =================================================
#============================================== other user stuff ===========================================


# get the nickname of a user
def get_nickname(chatroomId, username):
    sql = f"SELECT nickname FROM users WHERE username = ?"
    data, status_code = database_execute(chatroomId, sql, (username,))
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/get_nickname/0] || Failed to get nickname: {data}")
        return "ERR: could not get nickname"


    # sqlite3 wraps the username in a tuple inside of a list
    #print(data)
    try:
        nickname = d(data[0][0])
    except:
        nickname = "ERR: could not get nickname"


    return nickname



def check_perms(username, chatroomId, permission="admin"):
    try:
        username   = b(username)


    except Exception as e:
        log(level="warning", msg=f"[dbhandler/check_perms/0] ||  could not encode data sent from user\n Traceback: {e}")
        return "[dbhandler/check_perms/0] || Failed to check permission: Internal server error"


    # the option needs to be in this list to pass, this should avoid arbitrary things bing injected into the sql statement
    userPerms = [ "admin" ] # NOTE this cold be global, idk yet
    if permission not in userPerms:
        log(level='error', msg="[dbhandler.py/check_perms/1] attemted to check invalid permission. Make sure you are only checking things in userPerms list")
        return "Attempted to check invialid permission", 500


    sql = f"SELECT * FROM users WHERE username = ? and {permission} = true"
    data, status_code = database_execute(chatroomId, sql, (username,))
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/check_perms/1] || Databse opertion, getting permission failed: {data}")
        return "[dbhandler/check_perms/1] || Failed to cehck permission: Internal database error", 500


    if len(data) == 0 or not data:
        return False, 200


    return True, 200

















#=========================================================== dont need ====================================================================


# there is not main.db
# create and setup the main db
def init_main_db():
    database = 'main.db'
    # create chatrooms table
    sql = "CREATE TABLE chatrooms ('chatroomId', 'chatroom_name')"
    data, status_code = database_execute(database, sql, ())
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/init_main_db/0] || {data}")
        return "Internal database error", status_code


    # create invites table
    sql = "CREATE TABLE invites ('inviteId', 'chatroomId', 'expr_time', 'uses')"
    data, status_code = database_execute(database, sql, ())
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/init_main_db/0] || {data}")
        return "Internal database error", status_code


    # create users table
    sql = "CREATE TABLE users ('username', 'email', 'nickname', 'password', cookies, chatrooms)"
    data, status_code = database_execute(database, sql, ())
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/init_main_db/0] || {data}")
        return "Internal database error", status_code


    return "OK", 200


# we may need this but it would be very different
# get all registered users
def get_all_users(p=True):
    database = "main.db"
    # does database exist
    if not os.path.isfile(database):
        return False


    # fetch all users
    sql = "SELECT * FROM users"
    data, status_code = database_execute(database, sql, ())
    if status_code != 200:
        log(level='error', msg=f"[dbhandler/get_all_users/0] || {data}")
        return False


    # print them if p=True
    try:
        if p:
            for i in data:
                print(i)

    except Exception as e:
        log(level='error', msg=f"[dbhandler/get_all_users/1] || {e}")
        return False


    return True


# we dont need this bc checkuser already does everything that this is good for
# check if chatroom exists && user has access to it
def check_access(username, chatroomId):
    chatroomId_d, status_code = security.sanitize_chatroomId(chatroomId)# sanitize chatroom id used for path
    if status_code != 200:
        return chatroomId_d, status_code


    if not os.path.isdir(f'storage/{chatroomId_d}'): # NOTE check same thing in database
        return "chatroom does not exist", 400

    return "OK", 200

# get all registered users
def get_all_invites(p=True):
    if not os.path.isfile('storage/main.db'):
        return False
    try:
        db_connection = sqlite3.connect(f'storage/main.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"SELECT * FROM invites")
        a = db_cursor.fetchall()
        db_connection.close()

        if p:
            for i in a:
                print(i)

        return True
    except:
        return False

# add a user to a chatroom
def add_user_to_chatroom(username, chatroomId, admin=False, colour=None):
    chatroomId_d, status_code = security.sanitize_chatroomId(chatroomId)# sanitize chatroom id used for path
    if status_code != 200:
        return chatroomId_d, status_code



    try:
        username   = b(username)
        chatroomId = b(chatroomId)
        if colour != None:
            colour = b(colour)


    except Exception as e:
        log(level="warning", msg=f"[server/dbhandler.py/add_user_to_chatroom/0] could not encode data sent from user\n Traceback: {e}")


    try:
        db_connection = sqlite3.connect(f'storage/{chatroomId_d}/chatroom.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"INSERT INTO users VALUES (?, ?, ?)", (username, admin, colour))
        db_connection.commit()
        db_connection.close()


    except sqlite3.OperationalError as e:
        log(level='error', msg=f'[server/dbhandler/add_user_to_chatroom/1] database operation failed:  {e}')
        return "internal database error: could not conenct to database", 500


    return "OK", 200



# merge up
def remove_user_from_chatroom(username, chatroomId):
    chatroomId_d, status_code = security.sanitize_chatroomId(chatroomId)# sanitize chatroom id used for path
    if status_code != 200:
        return chatroomId_d, status_code



    try:
        username   = b(username)
        chatroomId = b(chatroomId)


    except Exception as e:
        log(level="warning", msg=f"[server/dbhandler.py/add_user_to_chatroom/0] could not encode data sent from user\n Traceback: {e}")


    try:
        db_connection = sqlite3.connect(f'storage/{chatroomId_d}/chatroom.db')
        db_cursor = db_connection.cursor()
        db_cursor.execute(f"DELETE FROM users WHERE username = ?", (username,))
        db_connection.commit()
        db_connection.close()


    except sqlite3.OperationalError as e:
        log(level='error', msg=f'[server/dbhandler/add_user_to_chatroom/1] database operation failed:  {e}')
        return "internal database error: could not conenct to database", 500


    return "OK", 200
#
## check if email is required in chatroom
#sql = "SELECT setting_value FROM settings WHERE setting_name = require_email"
#data, status_code = database_execute(chatroomId, sql, ())
#if status_code != 200:
#    log(level='error', msg=f"[dbhandler/save_new_user/1] || Failed to execute sql query: {data}")
#    return "[dbhandler/save_new_user/1] Failed to save user: Internal databse error", 500
#
#
#try:
#    print('Not sure how deeply nested this is:\nrequire_email: ', data , type(data))
#    require_email = data[0][0]
#
#except Exception as e:
#    log(level='error', msg=f"[dbhandler/save_new_user/2] || failed to unpack setting: {data}")
#    return "[dbhandler/save_new_user/2] Failed to save user: Internal databse error", 500
