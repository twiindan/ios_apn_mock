iOS APN mock
============

Implementation of iOS APN (Apple push notification server) mock


## HOW TO RUN THE iOS APN MOCK

    Copy your .crt and .key files in the folder.

    pyhton ios_mock.py --port {apn_port}

    The apn_port by default is 8091

    The application is started opening 2 sockets and one REST API.

    - In the first socket the APN mock is started. The port used is the {apn_port}
    - In the second socket the APN feedback is started. The port used is the {apn_port} + 1
    - The web service allow a easy mock configuration using REST API. The API is started in the localhost:{apn_port}+2

    Example:

    pyhton ios_mock.py --port 8090

    APN server is started in localhost port 8090
    APN feedback is started in localhost port 8091
    REST API is started in localhost port 8092

    Important!!! All the data should be coded as APN standards:
    https://developer.apple.com/library/ios/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/Chapters/CommunicatingWIthAPS.html


## USAGE

### APN Basic Usage

    The mock emulates the iOS APN behaviour. To obtain a response emulating the APN send a request using the socket opened.

    If there aren't errors saved the mock not returns nothing indicating all is OK.

    If there are some error saved before, the response served to the client is the error saved.

    The behaviour of the iOS APN Mock follow the following logic:

    if error saved:
        return error saved
    else:
        no response

    All the data received on the socket is decoded and saved in memory to be accessed after.

### Feedback Basic Usage

    The mock emulates the iOS Feedback behaviour. To obtain a response emulating the Feedback send a request using the socket opened.

    If there aren't errors saved the mock returns void string indicating all is OK.

    If there are some error saved before, the response served to the client is the error saved.

    The behaviour of the iOS Feedback Mock follow the following logic:

    if error saved:
        return error saved
    else:
        void string

    All the data received on the socket is decoded and saved in memory to be accessed after.

### Configuration API

    Is possible configure the mock to obtain errors simulating APN or Feedback errors.

    To configure APN errors should send a request to:

    POST http://localhost:{APN_PORT+2}/apn_error

    In the request body the error code (Defined in the APN standards) should be included.

    To configure Feedback errors should send a request to:

    POST http://localhost:{APN_PORT+2}/feedback_error

    with the following body:

      {"num_token": (integer), "token": [token_list]}

### Reset configuration

    To remove all the APN and Feedback errors:

    GET http://localhost:{APN_PORT+2}/reset_errors

    All errors are deleted from the mock.

### Statistics

    Is possible obtain all the statistics about APN requests and Feedback requests received

    To obtain all the APN requests received by the mock send a request to:

    GET http://localhost:{APN_PORT+2}/apn_stats

    All the requests received in the APN socket are included in the response body as JSON

    To obtain all the Feedback requests received by the mock send a request to:

    GET http://localhost:{APN_PORT+2}/feedback_stats

    All the requests received in the Feedback socket are included in the response body as JSON


### Reset statistics

    To remove all the APN and Feedback statistics:

    GET http://localhost:{APN_PORT+2}/reset_stats

    All stats are deleted from the mock.





