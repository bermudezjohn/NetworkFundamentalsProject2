High-Level Approach

The project consists of a Python FTP client on the command line. The script is written to be useful in connecting to an FTP server, authenticate a user, and carry out different file and directory actions as defined by the command-line arguments.

I attempted to have the program organized rationally:
Argument Parsing The script then evaluates the command-line options of the script using sys.argv to identify the operation requested (e.g. ls, cp), the target URL, and local file paths. Urllib.parse library is employed to decompose the FTP URL and extract the components (host, user, password and path).

Connection to Control Control: One of the main TCP sockets is the control channel that is connected with the FTP server. Every packet of commands and responses of the server is received and transmitted via this channel. The process script manages the welcomeing message on the first server and login process (USER/PASS).

Connection Data: In operations involving data transfer (ls, cp, mv), the script goes into passive mode by sending the PASV command. It then decodes the response of the server to obtain a new IP and port and opens a second TCP socket, the "data channel," to transfer the contents of files or listing of the directory.

Operation Execution: Relying on the operation that has been analyzed, the script transmits the appropriate FTP command (LIST, STOR, RETR, etc.), on the control channel and considers the data transfer over the data channel when required.

Cleanup: This is the last step in the script, which closes the connection by sending the QUIT command.

Challenges

This was the primary problem of handling two-socket architecture demanded by FTP protocol. Specifically:
 Parsing of the PASV Response: The data channel IP and port in a special format (h1,h2,h3,h4,p1,p2) are delivered by the response to the PASV command. These six numbers were a little bit tricky to properly decipher and form the ultimate 16-bit port number in the form of the following formula: port = (p1 256) + p2.

Synchronizing Sockets: It was important that the control channel and data channel were used in a proper manner. To illustrate, the script needed to wait until the first 150 response was received before beginning to read the data channel and wait until the last 226 response received in the control channel when the data-transfer was complete.

Testing

I probed the client as much as possible with the available ftp://ftp.4700.network server. I tested each of the features in the following way:
Use my script, my 4700ftp.py (e.g. mkdir, cp a file).
Trace the FTP command/response conversation of the low-level protocol using the -verbose flag and make sure the protocol was being adhered to properly.
Connect with a different, standard FTP-based client (such as the ftp utility on the command line) to confirm the outcome. In the case of mkdir, I would then test whether the directory was created upon running of the command. In the case of cp, I would first have to check whether the file was present in the server and then download it to check on the contents.
This was done in all the operations that were needed: ls, mkdir, rmdir, rm, cp (upload and download), and mv (upload and download).