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
   python cli.py localhost 1234 /
   python cli.py ecs.fullerton.edu 1234

Supported Commands
- ls -> List files on the server
- get <filename> -> Download a file from the server
- put <filename> -> Upload a file to the server
- quit -> Close the connection

Directory Structure
This implementation uses separate directories for client and server fiels to prevent overwrite conflicts:
- Client files are stored in:
  client_files/
- Server files are stored in:
  server_files/

How It Works
- put <filename> -> Uploads a file from `client_files/` to `server_files/`
- get <filename> -> Downloads a file from `server_files/` to `client_files/`
- ls -> Displays contents of `server_files/`

File Safety Features
To prevent accidental overwrites and improve security:
- The client will not overwrite existing local files during `get`
- The server will not overwrite remote files during `put`
- Invalid filenames and directory traversal attemps (e.g., `../file.txt`) are rejected

Connection Design
This program uses two TCP connections:
1. Control Connection
   - Persistent connection for commands (`ls`, `get`, `put`, `quit`)
   - Remains open for the duration of the session
2. Data Connection
   - Created separately for each `ls`, `get`, and `put` command
   - The client:
        - Opens an ephemeral port
        - Sends the port number to the server using the `PORT` command
   - The server:
        - Connects back to the client on that port
        - Transfers data (file contents or directory listing)
    
Implementation Notes
- Uses helper functions to ensure reliable transmission:
    - `send_all()` ensures all bytes are sent
    - `recv_exact()` ensures exact number of bytes are received
- File transfers unclude:
    - Sending the file size first
    - Then sending the file data
- Partial transfers are handled safely:
    - Incomplete files are deleted if an error occuers during transfer

Submission Notes
- Submit all files inside on uniquely named directory as required
- Ensure both `server.py` and `client.py` are included
- Ensure `client_files/` and `server_files/` are created automatically when running the programs


---
