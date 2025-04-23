import sqlite3
from datetime import datetime
import discord
from discord.ext import commands

class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect("DataBase.db")
        self.cursor = self.conn.cursor()
        self._setup_database()
        
    def _setup_database(self):
        """Initialize database tables if they don't exist."""
        # User Database
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, join_date TEXT)")
        
        # Message Database
        self.cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT, timestamp TEXT)")
        
        self.conn.commit()

    def add_user(self, user_id, username, join_date):
        """Add a new user to the database."""
        try:
            self.cursor.execute("INSERT OR IGNORE INTO users (user_id, username, join_date) VALUES (?, ?, ?)", 
                             (user_id, username, join_date))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error when adding user: {e}")
            return False

    def log_message(self, username, message, timestamp):
        """Add a message to the database."""
        try:
            self.cursor.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)", 
                             (username, message, timestamp))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error when logging message: {e}")
            return False

    def get_all_messages(self, limit=20):
        """Get recent messages from the database."""
        try:
            self.cursor.execute("SELECT username, message FROM messages ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = self.cursor.fetchall()
            # Reverse to get recent messages
            rows.reverse()
            return [f"{username}: {message}" for username, message in rows]
        except sqlite3.Error as e:
            print(f"Database error when retrieving messages: {e}")
            return []

    def cog_unload(self):
        """Close database connection when the cog is unloaded."""
        if self.conn:
            self.conn.close()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Add a new member to the database when they join."""
        self.add_user(member.id, str(member), member.joined_at.strftime("%Y-%m-%d %H:%M:%S"))

    @commands.Cog.listener()
    async def on_message(self, message):
        """Add messages to the database."""
        if not message.author.bot:
            self.log_message(message.author.display_name, message.content, 
                          datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

async def setup(bot):
    await bot.add_cog(Database(bot))
