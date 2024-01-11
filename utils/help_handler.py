class HelpMenuHandler():
    def __init__(self) -> None:
        self._commands = {}

    def add(self, command, explanation: str = "n/a", usage: str = "n/a", notes: str = None, owner_only: bool = False):
        self._commands[command] = { 'name': command, 'explanation' : explanation, 'usage' : usage, 
                                    'notes' : notes, 'owner_only' : owner_only}

    def get_message(self, command: str) -> str:
        if command in self._commands.keys():
            cmd = self._commands[command]
            if cmd['notes'] is None:
                return f"**?{cmd['name']}**\n{cmd['explanation']}\n**Usage**\n{cmd['usage']}"
            else:
                return f"**?{cmd['name']}**\n{cmd['explanation']}\n**Usage**\n{cmd['usage']}\n**Notes**\n{cmd['notes']}"
        else:
            return f"Sorry, command '{command}' was not found."

    def get_all(self) -> list[str]:
        member_cmds = [cmd for cmd in self._commands.values() if not cmd['owner_only']]
        owner_cmds = [cmd for cmd in self._commands.values() if cmd['owner_only']]
        ret_str = "**Member Commands**\n"
        for cmd in member_cmds:
            ret_str += f"`?{cmd['name']}` : {cmd['explanation']}\n"
        ret_str += "**Owner Commands**\n"
        for cmd in owner_cmds:
            ret_str += f"`?{cmd['name']}` : {cmd['explanation']}\n"
        return ret_str