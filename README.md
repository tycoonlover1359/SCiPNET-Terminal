# SCiPNET Terminal
SCiPNET Terminal is a custom, interactive terminal based around the SCP Foundation and its lore. Unfortunately, the terminal does not automatically scrape from the official SCP wiki, requiring articles to be manually created (or, more accurately, formatted).

This project was created to serve as a simple roleplay "toy" (for lack of a better word) for my friends and I, hence the lack of an ability for the front end to make "accounts."

# Status
The SCiPNET Terminal is marked as inactive, meaning that whilst not necessarily abandoned, updates of any kind are unlikely (unless doing so to rectify security issues).

# How It Works
The heart of the SCiPNET Terminal's client is the [jQuery Terminal](https://terminal.jcubic.pl/) by jcubic. When a command is run (assuming it is recognized by the terminal), it executes each command's designated function.

The terminal supports logging in to specific users with specific access levels; accounts on the terminal are not necessarily meant to be created automatically, and are currently only able to creted manually. Passwords are somewhat secure (as in, not stored in plaintext), but also do not utilize a more mature library such as bcrypt. The login process is as follows:
1. The user submits their username and password via the `login` function in the terminal. Before sending anything to the server, the function is hashed using one round of SHA-256. Then the username and password hash is sent to the back end.
2. Based on the provided username, the back end retrieves the user object from the database. If a user with the given username doesn't exist, it returns a `User Not Found` error.
3. If the user was found, the server computes the hash payload by concatenating, in order, the user's unique ID, their username, a unique password salt, and finally their hashed password received from the front end.
4. The server hashes the previously mentioned hash payload and compares it to the password hash stored in the database. If these do not match, then the server returns an `Invalid Credentials` error to the front end.
5. If the hashed hash payload and the password hash match, the server computes a JSON Web Token payload containing the user's unique ID and their username, then signs the JSON Web Token and returns it to the user along with another copy of their username, their access level, their site name (i.e., `Site-76` or `Area-02`), and their title (i.e., "Site Director"). The latter four returned items are not used for authentication; they are merely for showing to the user when they login so that they don't need to be requested from the server.

All other commands don't need a complicated process like for the `login` command; most other commands simply send the arguments (and the authentication JWT) back to the server, which handles most of the heavy lifting. Some commands, such as `help` or `credits` don't even need the server, as they simply print text out to the terminal.

# Services Utilized
- Amazon Simple Storage Service
- [jQuery Terminal](https://terminal.jcubic.pl/) by jcubic
- MySQL Database (via webhost)