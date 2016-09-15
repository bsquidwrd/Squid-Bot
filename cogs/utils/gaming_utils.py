import discord

DISCORD_MSG_CHAR_LIMIT = 2000

class GamingUtils:
    def __init__(self, bot, gaming):
        self.bot = bot
        self.gaming = gaming
        # Create the User database
        self.gaming.data.execute_query("""
        create table if not exists User (
            userID integer primary key,
            name text,
            discriminator text,
            deleted integer default 0,
            createdDate datetime default current_timestamp
        )""")
        # Create the Game database
        self.gaming.data.execute_query("""
        create table if not exists Game (
            gameID integer primary key,
            name text not null,
            url text
        )""")
        # Create the Search database
        self.gaming.data.execute_query("""
        create table if not exists Search (
            searchID integer primary key,
            userID integer,
            gameID integer,
            cancelled integer default 0,
            createdDate datetime default current_timestamp,
            expireDate datetime default (datetime('now', '+30 minutes')),
            foreign key(userID) references User(userID),
            foreign key(gameID) references Game(gameID)
        )""")


    ##################
    # Game Utilities #
    ##################
    async def game_add(self, game):
        """
        Add a game to the database
        """
        query = """
        insert into Game (name, url)
        select ?, ?
        where not exists(select name from Game where name = ?)
        """
        search_parameters = (game.name, game.url, game.name)
        return self.gaming.data.execute_query(query, search_parameters)

    async def game_get_all(self):
        """
        Get all the games
        """
        query = """
        select *
        from Game
        """
        return self.gaming.data.execute_query(query)

    async def game_beautify(self, games, reserve=0):
        """
        Return a message of all games ready for displaying all pretty like
        """
        formatted_message = '**No games are currently in the database!\nStart playing some games to make the database better**'
        try:
            if len(games) == 0:
                games = await self.game_get_all()

            formatted_message = '\n**Available games**\n'
            for game in games:
                formatted_message += '`{0}:` {1}\n'.format(game['gameID'], game['name'])
        except:
            pass
        return self.paginate(formatted_message, reserve=reserve)[0]

    async def game_find(self, game_search_key):
        """
        Get games that match the search key
        """
        games = await self.game_get_all()
        try:
            game_search_key = int(game_search_key)
            games = await self.game_find_by_id(game_search_key)
        except:
            games = await self.game_find_by_name(game_search_key)
        return games

    async def game_find_by_id(self, gameID):
        """
        Get all the games matching the given ID
        """
        query = """
        select *
        from Game
        where gameID = ?
        """
        return self.gaming.data.execute_query(query=query, parameters=(gameID,))

    async def game_find_by_name(self, name):
        """
        Get all the games matching a name
        """
        query = """
        select *
        from Game
        where name like ?
        """
        return self.gaming.data.execute_query(query=query, parameters=('%{}%'.format(name),))


    ####################
    # Search Utilities #
    ####################
    async def search_beautify(self, users, game, reserve=0):
        """
        Return a message of all user searches ready for displaying all pretty like
        """
        if users:
            users = await self.search_user(users)
        elif games:
            users = await self.search_game(games)

        if formatted is False:
            return users

        if len(users) >= 1:
            formatted_message = '' #'**The following users are looking for games:**\n'
            for user in users:
                if isinstance(user, discord.User):
                    u = user
                else:
                    u = discord.User(id=user['userID'], name=user['name'])
                formatted_message += '{}\n'.format(u.name)
        else:
            formatted_message = '**There are currently no users looking for games**'
        return self.paginate(formatted_message, reserve=reserve)[0]

    async def search_all(self):
        """
        Return a list of all searches for a specific user
        """
        query = """
        select *
        from Search
        where cancelled = 0
        and expireDate >= datetime('now')
        """
        return self.gaming.data.execute_query(query)

    async def search_game(self, game):
        """
        Return a list of all users currently searching for a specific game
        """
        query = """
        select *
        from Search
        where gameID = ?
        and cancelled = 0
        and expireDate >= datetime('now')
        """
        if isinstance(game, list):
            result = []
            for g in game:
                search_parameters = (g['gameID'],)
                result.append(self.gaming.data.execute_query(query, search_parameters))
        else:
            search_parameters = (game['gameID'],)
            result = self.gaming.data.execute_query(query, search_parameters)
        return result

    async def search_user(self, user):
        """
        Return a list of all searches for a specific user
        """
        query = """
        select *
        from Search
        where userID = ?
        and cancelled = 0
        and expireDate >= datetime('now')
        """
        if isinstance(user, list):
            result = []
            for u in user:
                if isinstance(u, discord.User):
                    search_parameters = (u.id,)
                else:
                    search_parameters = (u['userID'],)
                result.append(self.gaming.data.execute_query(query, search_parameters))
        else:
            if isinstance(user, discord.User):
                search_parameters = (user.id,)
            else:
                search_parameters = (user['userID'],)
            result = self.gaming.data.execute_query(query, search_parameters)
        return result

    async def search_remove_user(self, user, game):
        """
        Remove a user searching for a specific game
        """
        query = """
        update Search
        set cancelled=1
        where userID = ?
        and gameID = ?
        and cancelled = 0
        and expireDate >= datetime('now')
        """
        if isinstance(user, list):
            result = []
            for u in user:
                if isinstance(u, discord.User):
                    search_parameters = (u.id,)
                else:
                    search_parameters = (u['userID'],)
                result.append(self.gaming.data.execute_query(query, search_parameters))
        else:
            if isinstance(user, discord.User):
                search_parameters = (user.id,)
            else:
                search_parameters = (user['userID'],)
            result = self.gaming.data.execute_query(query, search_parameters)
        return result

    async def search_remove_user_all(self, user):
        """
        Deletes all of a users searches that are set to expire in the future
        """
        query = """
        update Search
        set cancelled=1
        where userID = ?
        and cancelled = 0
        and expireDate >= datetime('now')
        """
        if isinstance(user, list):
            search_parameters = [(u['userID'],) for u in user]
        else:
            search_parameters = (user['userID'],)
        return self.gaming.data.execute_query(query, search_parameters)

    async def search_user_add(self, user, game):
        """
        Adds a user searching for a game to the database
        """
        query = """
        insert into Search (userID, gameID)
        select ?, ?
        where not exists(select userID from Search where userID = ?
        and gameID = ?
        and cancelled = 0
        and expireDate >= datetime('now'))
        """
        search_parameters = (user.id, game['gameID'], user.id, game['gameID'])
        return self.gaming.data.execute_query(query, search_parameters)

    async def search_clear_all(self):
        """
        Clears all current game searches
        """
        query = """
        update Search
        set cancelled=1
        where cancelled = 0
        and expireDate >= datetime('now')
        """
        return self.gaming.data.execute_query(query)


    ##################
    # User Utilities #
    ##################
    async def user_get_all(self):
        """
        Get a list of all users
        """
        query = """
        select *
        from User
        where deleted = 0
        """
        return self.gaming.data.execute_query(query=query)

    async def user_add(self, user):
        """
        Add a user to the database
        """
        query = """
        insert or replace into User (userID, name, deleted)
        values (?, ?, 0)
        """
        search_parameters = (user.id, user.name)
        return self.gaming.data.execute_query(query, search_parameters)

    async def user_remove(self, user):
        """
        Mark a user as 'deleted'
        """
        query = """
        update User
        set deleted=1
        where userID = ?
        """
        search_parameters = (user.id,)
        return self.gaming.data.execute_query(query, search_parameters)

    ##################
    # Misc Utilities #
    ##################
    def paginate(self, content, *, length=DISCORD_MSG_CHAR_LIMIT, reserve=0):
        """
        Split up a large string or list of strings into chunks for sending to discord.
        """
        if type(content) == str:
            contentlist = content.split('\n')
        elif type(content) == list:
            contentlist = content
        else:
            raise ValueError("Content must be str or list, not %s" % type(content))

        chunks = []
        currentchunk = ''

        for line in contentlist:
            if len(currentchunk) + len(line) < length - reserve:
                currentchunk += line + '\n'
            else:
                chunks.append(currentchunk)
                currentchunk = ''

        if currentchunk:
            chunks.append(currentchunk)

        return chunks
