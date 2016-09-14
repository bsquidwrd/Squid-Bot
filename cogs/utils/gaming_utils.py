class GamingUtils:
    def __init__(self, bot, gaming):
        self.bot = bot
        self.gaming = gaming
        self.gaming.data.execute_query("create table if not exists User (userID integer primary key, name text, discriminator text, createdDate datetime default current_timestamp)")
        self.gaming.data.execute_query("create table if not exists Game (gameID integer primary key, name text not null, url text)")
        self.gaming.data.execute_query("""
        create table if not exists Search (
            searchID integer primary key,
            userID integer,
            gameID integer,
            canceled integer default 0,
            createdDate datetime default current_timestamp,
            expireDate datetime default (datetime('now', '+30 minutes')),
            foreign key(userID) references User(userID),
            foreign key(gameID) references Game(gameID)
        )""")


    ##################
    # Game Utilities #
    ##################
    async def game_add(self, game):
        return self.gaming.data.execute_query("""
        insert into Game (name, url)
        select ?, ?
        where not exists(select name from Game where name = ?)
        """, (game.name, game.url, game.name))

    async def game_get_all(self):
        return self.gaming.data.execute_query(query="select * from Game")

    async def game_beautify(self, games):
        formatted_message = '**No games are currently in the database!\nStart playing some games to make the database better**'
        try:
            if len(games) >= 1:
                formatted_message = '\n**Available games**\n'
                for game in games:
                    formatted_message += '`{0}:` {1}\n'.format(game['gameID'], game['name'])
        except:
            pass
        return formatted_message

    async def game_find_by_id(self, gameID):
        return self.gaming.data.execute_query(query="select * from Game where gameID = ?", parameters=(gameID,))

    async def game_find_by_name(self, name):
        return self.gaming.data.execute_query(query="select * from Game where name like ?", parameters=('%{}%'.format(name),))


    ####################
    # Search Utilities #
    ####################
    async def search_get_users_all(self, formatted=True):
        users = await self.user_get_all()
        if formatted is False:
            return users

        if len(users) >= 1:
            formatted_message = '**The following users are looking for games:**\n'
            for user in users:
                u = discord.User(id=user)
                formatted_message += '{}\n'.format(u.mention)
        else:
            formatted_message = '**There are currently no users looking for games**'
        return formatted_message

    async def search_user(self, user):
        query = """
        select *
        from Search
        where userID = ?
        and cancelled = 0
        and expireDate < datetime('now')
        """

    async def search_remove_user(self, user, game):
        query = """
        update Search
        set cancelled=1
        where userID = ?
        and gameID = ?
        and cancelled = 0
        and expireDate < datetime('now')
        """
        return self.gaming.data.execute_query(query=query, parameters=(user.id, game['gameID']))

    async def search_remove_user_all(self, user):



    ##################
    # User Utilities #
    ##################
    async def user_get_all(self):
        return self.gaming.data.execute_query(query="select * from User")

    async def user_add(self, user):
        return self.gaming.data.execute_query("""
        insert into User (userID, name)
        select ?, ?
        where not exists(select userID from User where userID = ?)
        """, (user.id, user.name, user.id))

    async def user_remove(self, user):
        return self.gaming.data.execute_query("""
        delete from User
        where userID = ?
        """, (user.id,))
