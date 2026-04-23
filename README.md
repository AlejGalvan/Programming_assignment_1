# CPSC-471---Programming_assignment_1

---

## Team Information

| Team Member Names | Email |
|---|---|
| Alejandro Galvan | alejandrogalvan@csu.fullerton.edu |
|Mohammad Ali Khan|malikhan2597@csu.fullerton.edu|
|Vinh Tran|vtran112@csu.fullerton.edu|
|Nathan Chamorro|nathanchamorro@csu.fullerton.edu|




Programming Language: Python

Instructions:
 
How to Execute the Program

1. Start the server:
   python serv.py <PORTNUMBER>

   Example:
   python serv.py 1234

2. Start the client:
   python cli.py <server machine> <server port>

   Examples:
   python cli.py localhost 1234
   python cli.py ecs.fullerton.edu 1234

Supported Commands
- ls
- get <filename>
- put <filename>
- quit

Submission Notes
- This program uses two TCP connections:
  1. A control connection that stays open for the full FTP session.
  2. A separate data connection created for each ls, get, and put command.
- The client opens an ephemeral port for the data connection and informs the server of the port number.
- The server connects back to the client on that port for each transfer.
- The server and client use helper functions to ensure all bytes are sent and received correctly.
- Files should be submitted inside one uniquely named directory as required by the assignment.
Note: When testing the program locally, running both the client and server in the same directory may cause file overwrite conflicts during `get` and `put` operations. This happens because both programs access the same file paths. To properly test file transfers, it is recommended to run the client and server from separate working directories.


---
