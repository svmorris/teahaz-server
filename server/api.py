import uuid
import time
import json
import base64
from os.path import isfile as os_isfile

import dbhandler
import security_th as security
import filesystem_th as filehander
import users_th as users
from logging_th import logger as log 





def create_chatroom(json_data):
    username      = json_data.get('username')
    email         = json_data.get('email')
    nickname      = json_data.get('nickname')
    password      = json_data.get('password')
    chatroom_name = json_data.get('chatroom_name')
    chatroomId    = str(uuid.uuid1())


    # make sure client sent all needed data
    if not username or not email or not nickname or not password or not chatroom_name:
        return '[api/create_chatroom/0] || One or more of the required arguments are not supplied. required = [username, email, nickname, password, chatroom_name]', 400



    # create folders needed for chatroom
    response, status_code = filehander.create_chatroom_folders(chatroomId)
    if status_code != 200:
        log(level='error', msg=f'[api/create_chatroom/2] || could not create chatroom')
        return response, 500



    # create chatroom.db inside chatroom the chatrom folder
    response, status_code = dbhandler.init_chat(chatroomId, chatroom_name)
    if status_code != 200:
        log(level='error', msg=f'[api/create_chatroom/3] || could not create chatroom database\n Traceback: {response}')

        # remove chatroom
        filehander.remove_chatroom(chatroomId)

        return response, status_code



    response, status_code = users.add_user(username, email, nickname, password, chatroomId)
    if status_code != 200:
        log(level='error', msg="[api/create_chatroom/4] || Failed to add chatroom admin")

        # remove chatroom
        filehander.remove_chatroom(chatroomId)

        return response, status_code


    response, status_code = dbhandler.check_settings(chatroomId, "chatroom_name")
    if status_code != 200:
        return response, status_code



    # format chat object
    try:
        chat_obj = {
                "name": response,
                "chatroom": chatroomId
                }
    except Exception as e:
        log(level='error', msg=f"[api/create_chatroom/5] || Formattng chat_obj failed: {e}")
        return "[api/create_chatroom/5] || Internal server errror while formatting chat object", 500


    # run set_cookie for autolong, and chatobj for returning at the end
    return chat_obj, 200



def create_invite(json_data, chatroomId):
    username   = json_data.get('username')
    expr_time  = json_data.get('expr-time')
    uses       = json_data.get('uses')
    inviteId   = str(uuid.uuid1())


    # make sure we got all the data
    if not username or not chatroomId or not uses or not expr_time:
        return f"[api/create_invite/0] || One or more of the required arguments were not supplied. Required=[username, expr_time, uses]. Supplied=[{username}, {uses}, {expr_time}]", 400


    # make sure the format is good on time and uses
    try:
        expr_time = float(expr_time)
        uses = int(uses)


    # no
    except:
        return "[api/create_invite/1] || Invalid format: expr_time has to be type: FLOAT AND uses has to by type: INT", 400


    # invites can only be created if you are admin
    has_permission, status_code = dbhandler.check_perms(username, chatroomId, permission="admin")
    if status_code != 200:
        return has_permission, status_code


    if has_permission != True:
        return "[api/create_invite/2] || Permission denied: your user does not have permission to perform this action", 403


    # save this invite in the database
    response, status_code = dbhandler.save_invite(chatroomId, inviteId, expr_time, uses)
    if status_code != 200:
        return response, status_code


    # ok
    return inviteId, 200



def message_send(json_data, chatroomId):
    messageId = str(uuid.uuid1())
    replyId = json_data.get('replyId')
    message = json_data.get('message')
    username = json_data.get('username')
    message_type = json_data.get('type')



    # make sure all of the needed data is present and is not 'None'
    if not username or not message or not message_type or not chatroomId:
        return '[api/message_send/0] || one or more of the required arguments are not supplied, needed=[username, message, type, chatroomId]', 400


    # check message type
    if message_type != "text":
        return "[api/message_send/1] || posting non-'text' type to /message is forbidden", 405


    # store message that got sent
    #NOTE
    response , status_code = dbhandler.save_in_db(
                                time         = time.time(),
                                messageId    = messageId,
                                replyId      = replyId,
                                username     = username,
                                chatroomId   = chatroomId,
                                message_type = 'text',
                                message      = message
                                )


    # make sure saving worked without any errors
    if status_code != 200:
        return response, status_code

    # all is well
    return "OK", 200



def message_get(headers, chatroomId):
    last_time = headers.get('time')
    username = headers.get('username')


    # make sure the client sent everything
    if not last_time or not username or not chatroomId:
        return '[api/message_get/0] || one or more of the required arguments are not supplied. Required=[time, username, chatroomId]', 400


    # time needs to be converted to a number
    try:
        last_time = float(last_time)


    # please supply a valid time
    except:
        return 'value for time is not a number', 400


    # get messages since last_time
    return_data, status_code = dbhandler.get_messages_db(chatroomId, last_time=last_time)


    # if gettting messages failed
    if status_code != 200:
        log(level='error', msg=f'[server/api/message_get/3] server error while getting messages\n Traceback  {return_data}')
        return return_data, status_code


    # all is well
    return return_data, 200



def upload_file(json_data, chatroomId):
    username      = json_data.get('username')
    filename      = json_data.get('filename')
    fileId        = json_data.get('fileId')
    message_type  = json_data.get('type')
    part          = json_data.get('part')
    data          = json_data.get('data')
    messageId     = str(uuid.uuid1())

    if not username:
        return "nouname", 400

    if not message_type:
        return "nomessagetype", 400

    if not data:
        return data, 400

    if not filename:
        return "nofilename", 400

    # make sure client sent all needed data
    if not username or not message_type or not data or not filename:
        return f'[api/upload_file/0] || one or more of the required arguments are not supplied. Required=[username, type, data, filename]  Supplied=[{username}, {message_type}, (type(data)){type(data)}, {filename})]', 400



    # message type has to be file
    if not message_type == "file":
        return "[api/upload_file/1] || posting non-'file' type to /file is forbidden", 400



    # NOTE: this should be a global setting
    max_chunk_size = 1048576 # one megabyte

    # check if the 
    if len(data) > max_chunk_size:
        return f'[api/upload_file/2] || data field exeeded the maximum chunk-size permitted by the server. Maximum={max_chunk_size}', 400



    # if a fileId is sent then the file is a part that should be appended to the already existing file
    # elif the fileId is not sent then generate a random one
    if not fileId:
        fileId = str(uuid.uuid1())


    # save file that user sent
    response, status_code = filehander.save_file_chunk(data, chatroomId, fileId, fileId, username)
    if status_code != 200:
        log(level='error', msg=f'[api/upload_file/2] failed to save file: {fileId}')
        return response, status_code




    # if the file is small or its the last part: save a reference to the file in the chatroom database
    if not part:
        response, status_code = dbhandler.save_in_db(
                time          = time.time(),
                messageId     = messageId,
                username      = username,
                chatroomId    = chatroomId,
                message_type  = message_type,
                fileId        = fileId,
                filename      = filename
                )


        # failed to save reference to file
        if status_code != 200:
            log(level='warning', msg=f'[api/upload_file/3] || failed to save file: {fileId}, in database \n attempting to remove')

            # delete file because it could not be indexed
            _response, status_code = filehander.remove_file(chatroomId, fileId)
            if status_code != 200:
                log(level='error', msg=f'[api/upload_file/4] || failed to delete corrupt file: {fileId}')

            # return error
            return response, status_code


    # all is well
    return fileId, 200



def download_file(headers, chatroomId):
    username     = headers.get('username')
    section      = headers.get('section')
    fileId       = headers.get('fileId')


    # make sure client sent all data
    if not username or not fileId  or not section:
        return '[api/download_file/0] || one or more of the required arguments are not supplied. Required = [username, filename, section]. Supplied=[{username}, {filename}, {section}]', 400


    # make sure section is int
    try:
        section = int(section)
    except Exception as e:
        return f'[api/download_file/1] || invalid data sent for section filed. Type has to be INT. Traceback: {e}'



    # sanitization is healthy
    response, status_code = security.check_uuid(fileId)
    if status_code != 200:
        return response, status_code



    # check for the files existance. os_isfile is an alias to os.path.isfile, i dont really want to import os to minimize security issues
    if not os_isfile(f'storage/chatrooms/{chatroomId}/uploads/{fileId}'):
        return "[api/download_file/1] || The requested file doesnt exist", 404



    # read file requested by user
    data, status_code = filehander.read_file_chunk(chatroomId, fileId, section)
    if status_code != 200:
        log(level='error', msg=f'[server/api/download_file/0] error while reading file: {fileId}')
        return data, status_code



    # all is well
    return data, 200

























































#def get_chatrooms(headers):
#    username = headers.get('username')
#
#
#    # make sure we got all needed data
#    if not username:
#        return "username not supplied", 400
#
#
#    # get a list of chatroom IDs that the user has access to
#    response, status_code = dbhandler.user_get_chatrooms(username)
#
#    # if error
#    if status_code != 200:
#        log(level='error', msg=f'[server/api/get_chatrooms/3] could not get chatroom data from main.db')
#        return response, status_code
#
#
#    # if not error
#    else:
#        # if there are non then respond with 204
#        if len(response) == 0:
#            return "", 204
#
#        # create json with chatname and chat ID in it
#        resp_list = []
#        for chatroomId in response:
#
#            # get name corresponding to  chatroomId
#            chatname, status_code = dbhandler.get_chatname(chatroomId)
#            if status_code != 200:
#                return chatname, status_code
#
#
#            chat_obj = {
#                    'name': chatname,
#                    'chatroom': chatroomId
#                    }
#
#
#            resp_list.append(chat_obj)
#        response = resp_list
#
#    # all is well
#    return response, status_code


#
#
#
#
#
