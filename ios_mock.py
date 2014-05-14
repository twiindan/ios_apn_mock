# -*- coding: utf-8 -*-
from binascii import a2b_hex
from struct import pack, unpack
import os
from optparse import OptionParser
from gevent import monkey; monkey.patch_all()
from gevent.server import StreamServer
from gevent import socket
from collections import deque, namedtuple
from bottle import run, post, route, request
import ujson
import struct
import os

responses_saved = deque()
feedback_saved = deque()
requests_handled = deque()
feedback_handled = deque()

cert = os.path.join(os.path.dirname(__file__), 'server.crt')
key = os.path.join(os.path.dirname(__file__), 'server.key')


def unpack_received_data(received_data):

    request_list = []
    len_received_data = len(received_data)
    Notification = namedtuple("Notification", ["id", "token", "expiry", "payload", "error"])

    while received_data:
        offset = 0
        top_level_fmt = ">BI"
        top_level_offset = struct.calcsize(top_level_fmt)
        _, frame_length = struct.unpack_from(top_level_fmt, received_data, offset)
        offset += top_level_offset
        items = {}

        while offset - top_level_offset < frame_length:
            item_header_fmt = ">BH"
            item_num, item_length = struct.unpack_from(item_header_fmt, received_data, offset)
            offset += struct.calcsize(item_header_fmt)
            item_payload_fmt = ">{}s".format(item_length)
            item_data, = struct.unpack_from(item_payload_fmt, received_data, offset)
            offset += struct.calcsize(item_payload_fmt)

            # Store item
            items[item_num] = item_data

        # Process incoming new notification
        received_data = received_data[offset:]
        new_notification = Notification(struct.unpack(">I", items[3])[0],
                                        items[1].encode("hex"),
                                        struct.unpack(">I", items[4])[0],
                                        ujson.loads(items[2]),
                                        None)

        request = {"token": new_notification.token, "expiry": new_notification.expiry,
                   "payload": new_notification.payload}
        request_list.append(request)

    requests_handled.append(request_list)


def handle_APN(socket, address):

    print 'New APN connection from %s:%s' % address
    received_data = socket.recv()
    unpack_received_data(received_data)

    if not responses_saved:
        socket.settimeout(1)
        try:
            socket.recv(64)
        except:
            pass
    else:
        response = responses_saved.popleft()
        socket.sendall(response)

    #TODO: Mechanism to close the socket connection to force connection error.
    #TODO: Mechanism to tell that some token or the last one is wrong (not only first)


def handle_feedback(socket, address):
    print 'New FEEDBACK connection from %s:%s' % address
    feedback_handled.append("")
    if not feedback_saved:
        socket.recv(1)
        socket.sendall("")
    else:
        response = feedback_saved.popleft()
        for x in response:
            print ">>> FEEDBACK SENT TO DISPATCHER: " + repr(x)
            socket.sendall(x)
            socket.recv(1)


@post("/feedback_error")
def feedback_error():

    data = request.body.read()
    body_received = ujson.loads(data)
    tokens_to_be_send = int(body_received['num_token'])
    tokens_feedback = []

    if tokens_to_be_send == 1:
        token_bin = a2b_hex(body_received['token'])
        token_length_bin = struct.pack('>H', (len(token_bin)))
        date = struct.pack('>I', 1261440000)
        body_to_send = date + token_length_bin + token_bin
        tokens_feedback.append(body_to_send)
    else:
        for i in range(tokens_to_be_send):

            token_bin = a2b_hex(body_received['token'][i])
            token_length_bin = struct.pack('>H', (len(token_bin)))
            date = struct.pack('>I', 1261440000)
            body_to_send = date + token_length_bin + token_bin
            tokens_feedback.append(body_to_send)

    feedback_saved.appendleft(tokens_feedback)
    return 'Feedback SAVED'


@post("/apn_error")
def save_error():

    data = request.body.read()
    body_received = ujson.loads(data)
    command = struct.pack('>B', 8)
    received_data = struct.pack('>B', int(body_received['code_error']))
    last_message_ok = struct.pack('>I', 0)
    body_to_send = command + received_data + last_message_ok
    responses_saved.append(body_to_send)
    return 'Response SAVED'


@route("/reset_stats")
def reset_stats():

    requests_handled.clear()
    feedback_handled.clear()
    return 'stats reset'


@route("/reset_errors")
def reset_responses():

    responses_saved.clear()
    feedback_saved.clear()
    return 'responses deleted'


@route("/apn_stats")
def stats():

    body = {'num_requests': len(requests_handled),
            'requests': list(requests_handled)}
    return ujson.dumps(body)


@route("/feedback_stats")
def feedback_stats():
    body = {'num_feedback_requests': len(feedback_handled)}
    return ujson.dumps(body)


def main():
    parser = OptionParser()
    parser.add_option(
        "-p", "--port",
        dest="port",
        help="Server port [%default]",
        type="int",
        default=8090)

    parser.add_option(
        "-b", "--bind_address",
        dest="bind",
        help="Bind addreess [%default]",
        default="0.0.0.0")

    (options, args) = parser.parse_args()

    print "Starting APN server on %s:%s" % (options.bind, int(options.port))
    StreamServer((options.bind, int(options.port)), handle_APN, keyfile=key, certfile=cert).start()

    print "Starting FEEDBACK server on %s:%s" % (options.bind, options.port+1)
    StreamServer((options.bind, options.port+1), handle_feedback, keyfile=key, certfile=cert).start()

    run(host=options.bind, port=options.port+2, debug=True)


if __name__ == "__main__":
    main()
