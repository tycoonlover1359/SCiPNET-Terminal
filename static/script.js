jQuery(function($, undefined) {
    $('body').terminal({
        login: function() {
            if (localStorage.getItem("scipnet_auth_token")) {
                this.error("You are already logged in.")
            } else {
                let password_hash = "";
                this.read("Username: ").then(username_input => {
                    this.set_mask("*").read("Password: ").then(password_input => {
                        this.pause()
                        this.set_mask(false);
                        const hashObj = new jsSHA("SHA-256", "TEXT");
                        hashObj.update(password_input.toString())
                        password_hash = hashObj.getHash("HEX");
                        fetch("auth", {
                            method: "POST",
                            body: JSON.stringify({
                                username: username_input,
                                password_hash: password_hash
                            }),
                            headers: {"Content-Type": "application/json"}
                        }).then(response => {
                            response.json().then(result => {
                                if (result["success"]) {
                                    localStorage.setItem("scipnet_auth_token", result["auth_token"]);
                                    localStorage.setItem("scipnet_username", result["username"]);
                                    localStorage.setItem("scipnet_access_level", result["access_level"]);
                                    this.clear()
                                    this.echo("Welcome " + result["username"] + ", " + result["title"] + ", " + result["site"]);
                                    this.echo("Security Clearance: Level " + result["access_level"]);
                                    this.echo("")
                                    this.set_prompt(result["username"] + "@SCiPNET --> ");
                                } else {
                                    this.error("Login failed: " + result["error"])
                                };
                                this.resume()
                            });
                        });
                    });
                });
            };
        },
        logout: function() {
            if (localStorage.getItem("scipnet_auth_token")) {
                localStorage.removeItem("scipnet_auth_token");
                localStorage.removeItem("scipnet_username");
                localStorage.removeItem("scipnet_access_level");
                this.clear()
                this.set_prompt("guest@SCiPNET --> ")
                this.echo("You've been logged out.\n");
            } else {
                this.error("You are not logged in.");
            };
        },
        access: function(doc_type, doc_id) {
            if (localStorage.getItem("scipnet_auth_token")) {
                this.pause()
                const id = doc_id.toString().padStart(3, "0");
                this.echo("Document Request Sent. Please Wait...")
                fetch("document", {
                    method: "POST",
                    body: JSON.stringify({
                        "auth_token": `${localStorage.getItem("scipnet_auth_token")}`,
                        "doc_type": `${doc_type}`,
                        "doc_id": `${id}`
                    }),
                    headers: {"Content-Type": "application/json"}
                }).then(response => {
                    response.json().then(result => {
                        if (result["success"]) {
                            const document = result["document"];
                            this.clear();
                            this.echo("[[;magenta;]━━━━━━━━ BEGIN DOCUMENT ━━━━━━━━]");
                            this.echo(document, {flush: true, raw: true});
                            this.echo("[[;magenta;]━━━━━━━━━ END DOCUMENT ━━━━━━━━━]");
                        } else {
                            this.error(result["error"]);
                        };
                    });
                });
                this.resume()
            } else {
                this.error("You are not logged in.");
            };
        },
        credits: function() {
            this.echo(" ");
            this.echo("Made by [[!;;;;https://tycoonlover1359.omg.lol/]Tycoonlover1359]");
            this.echo("Built on top of [[i;;]jcubic]'s [[!;;;;https://terminal.jcubic.pl/]jQuery Terminal] JavaScript 'plugin'");
            this.echo("Hosted on [[!;;;;https://heliohost.org/]HelioHost]");
            this.echo("Augmented with [[!;;;;https://aws.amazon.com/]Amazon Web Services]")
            this.echo(" ");
        },
        help: function() {
            this.echo(" ")
            this.echo("access <type> <id> | Access the document that matches the given parameters. Only works while logged in.");
            this.echo("clear              | Clear the screen.")
            this.echo("credits            | See the credits for this 'app'.")
            this.echo("help               | Access this help prompt.");
            this.echo("login              | Activates the login prompt. Only works while not logged in.");
            this.echo("logout             | Logouts the current user. Only works while logged in.");
            this.echo(" ")
        }
    }, {
        greetings: function() {
            if (localStorage.getItem("scipnet_username")) {
                const username = localStorage.getItem("scipnet_username");
                const access_level = localStorage.getItem("scipnet_access_level");
                return `╔════════════════════════════════╗\n║ SCiPNET DIRECT ACCESS TERMINAL ║\n╚════════════════════════════════╝\n\nWelcome, ${username}\nSecurity Clearance: Level ${access_level}\n`;
            } else {
                return "╔════════════════════════════════╗\n║ SCiPNET DIRECT ACCESS TERMINAL ║\n╚════════════════════════════════╝\n\nAuthentication Required\n";
            };
        },
        prompt: function() {
            if (localStorage.getItem("scipnet_username")) {
                return localStorage.getItem("scipnet_username") + "@SCiPNET --> ";
            } else {
                return "guest@SCiPNET --> ";
            };
        },
        memory: true,
    });
});