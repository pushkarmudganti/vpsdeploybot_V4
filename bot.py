import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import subprocess
import json
import os
import time
import random
import re
import psutil
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import signal
import sys

# ==================== CONFIGURATION ====================
TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your bot token
PREFIX = "/"  # Using / for slash commands
MAIN_ADMIN_ID = 1372237657207345183  # Your Discord ID (Main Admin)
BOT_NAME = "VantaNodes"
RAM_LIMIT = "2g"
SERVER_LIMIT = 12
LOGS_CHANNEL_ID = 123456789  # CHANGE THIS TO YOUR LOGS CHANNEL ID

database_file = 'database.txt'
admins_file = 'admins.json'

# Modern Color Scheme
EMBED_COLOR = 0x9B59B6  # Purple
SUCCESS_COLOR = 0x00FF00  # Green
ERROR_COLOR = 0xFF0000  # Red
WARNING_COLOR = 0xFFA500  # Orange
INFO_COLOR = 0x3498DB  # Blue

# Modern Emojis
EMOJI = {
    'cpu': '🖥️', 'ram': '💾', 'disk': '💽', 'network': '🌐',
    'online': '🟢', 'offline': '🔴', 'pending': '🟡',
    'start': '▶️', 'stop': '⏹️', 'restart': '🔄',
    'terminal': '💻', 'stats': '📊', 'time': '⏰',
    'check': '✅', 'cross': '❌', 'warning': '⚠️',
    'info': 'ℹ️', 'settings': '⚙️', 'database': '🗄️',
    'server': '🖥️', 'vps': '🚀', 'admin': '👑',
    'user': '👤', 'node': '🌐', 'location': '📍',
    'power': '⚡', 'delete': '🗑️', 'edit': '✏️',
    'list': '📋', 'help': '❓', 'about': 'ℹ️',
    'ping': '📡', 'uptime': '⏱️', 'success': '✅',
    'error': '❌', 'loading': '⏳', 'arrow': '➡️',
    'folder': '📁', 'package': '📦', 'tool': '🛠️',
    'shield': '🛡️', 'lock': '🔒', 'unlock': '🔓',
    'search': '🔍', 'chart': '📈', 'bell': '🔔',
    'star': '⭐', 'sparkle': '✨', 'fire': '🔥',
    'heart': '❤️', 'reinstall': '🔄', 'ssh': '🔑',
    'ip': '🌍', 'docker': '🐳', 'container': '📦',
    'memory': '🧠', 'clock': '🕐', 'tmate': '🔌',
    'globe': '🌎', 'id': '🆔', 'role': '🔰'
}

# OS Options with fancy emojis and descriptions
OS_OPTIONS = {
    "ubuntu": {
        "image": "ubuntu-vps", 
        "name": "Ubuntu 22.04", 
        "emoji": "🐧",
        "description": "Stable and widely-used Linux distribution"
    },
    "debian": {
        "image": "debian-vps", 
        "name": "Debian 12", 
        "emoji": "🦕",
        "description": "Rock-solid stability with large software repository"
    },
    "alpine": {
        "image": "alpine-vps", 
        "name": "Alpine Linux", 
        "emoji": "⛰️",
        "description": "Lightweight and security-focused"
    },
    "arch": {
        "image": "arch-vps", 
        "name": "Arch Linux", 
        "emoji": "🎯",
        "description": "Rolling release with bleeding-edge software"
    },
    "kali": {
        "image": "kali-vps", 
        "name": "Kali Linux", 
        "emoji": "💣",
        "description": "Penetration testing and security auditing"
    },
    "fedora": {
        "image": "fedora-vps", 
        "name": "Fedora", 
        "emoji": "🎩",
        "description": "Innovative features with Red Hat backing"
    }
}

# Animation frames for different states
LOADING_ANIMATION = ["🔄", "⚡", "✨", "🌀", "🌪️", "🌈"]
SUCCESS_ANIMATION = ["✅", "🎉", "✨", "🌟", "💫", "🔥"]
ERROR_ANIMATION = ["❌", "💥", "⚠️", "🚨", "🔴", "🛑"]
DEPLOY_ANIMATION = ["🚀", "🛰️", "🌌", "🔭", "👨‍🚀", "🪐"]

# ==================== BOT SETUP ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class AdminBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or(PREFIX), intents=intents)
        self.start_time = datetime.now()
        self.main_admin_id = MAIN_ADMIN_ID
        self.admins = set([MAIN_ADMIN_ID])
        self.bot_name = BOT_NAME
        
        # Load admins from file
        self.load_admins()
    
    def load_admins(self):
        """Load admins from JSON file"""
        try:
            if os.path.exists(admins_file):
                with open(admins_file, 'r') as f:
                    data = json.load(f)
                    self.admins = set(data.get('admins', [MAIN_ADMIN_ID]))
                    print(f"✅ Loaded {len(self.admins)} admins")
        except Exception as e:
            print(f"⚠️ Error loading admins: {e}")
    
    def save_admins(self):
        """Save admins to JSON file"""
        try:
            data = {'admins': list(self.admins)}
            with open(admins_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"✅ Saved {len(self.admins)} admins")
        except Exception as e:
            print(f"⚠️ Error saving admins: {e}")

bot = AdminBot()

# ==================== HELPER FUNCTIONS ====================

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in bot.admins or user_id == bot.main_admin_id

def is_main_admin(user_id: int) -> bool:
    """Check if user is main admin"""
    return user_id == bot.main_admin_id

def create_embed(title, description=None, color=EMBED_COLOR, fields=None, footer=None, thumbnail=None):
    """Create a formatted embed"""
    embed = discord.Embed(
        title=f"{EMOJI['vps']} {title}",
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    
    embed.set_author(name=bot.bot_name)
    
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    
    if footer:
        embed.set_footer(text=footer)
    else:
        embed.set_footer(text=f"{bot.bot_name} • Admin Managed")
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    return embed

def generate_random_port():
    return random.randint(1025, 65535)

def add_to_database(user, container_name, ssh_command):
    with open(database_file, 'a') as f:
        f.write(f"{user}|{container_name}|{ssh_command}\n")

def remove_from_database(ssh_command):
    if not os.path.exists(database_file):
        return
    with open(database_file, 'r') as f:
        lines = f.readlines()
    with open(database_file, 'w') as f:
        for line in lines:
            if ssh_command not in line:
                f.write(line)

def remove_container_from_database_by_id(container_id):
    if not os.path.exists(database_file):
        return
    with open(database_file, 'r') as f:
        lines = f.readlines()
    with open(database_file, 'w') as f:
        for line in lines:
            parts = line.strip().split('|')
            if len(parts) < 2 or parts[1] != container_id:
                f.write(line)

def get_container_info_by_id(container_id):
    if not os.path.exists(database_file):
        return None, None, None
    with open(database_file, 'r') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 3 and parts[1].startswith(container_id):
                return parts[0], parts[1], parts[2]
    return None, None, None

def get_user_servers(user):
    if not os.path.exists(database_file):
        return []
    servers = []
    with open(database_file, 'r') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 3 and parts[0] == user:
                servers.append(line.strip())
    return servers

def get_all_servers():
    if not os.path.exists(database_file):
        return []
    servers = []
    with open(database_file, 'r') as f:
        for line in f:
            servers.append(line.strip())
    return servers

def count_user_servers(user):
    return len(get_user_servers(user))

async def capture_ssh_session_line(process):
    while True:
        output = await process.stdout.readline()
        if not output:
            break
        output = output.decode('utf-8').strip()
        if "ssh session:" in output:
            return output.split("ssh session:")[1].strip()
    return None

def get_system_resources():
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        mem_total = mem.total / (1024 ** 3)
        mem_used = mem.used / (1024 ** 3)
        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024 ** 3)
        disk_used = disk.used / (1024 ** 3)
        
        return {
            'cpu': cpu_percent,
            'memory': {'total': round(mem_total, 2), 'used': round(mem_used, 2), 'percent': mem.percent},
            'disk': {'total': round(disk_total, 2), 'used': round(disk_used, 2), 'percent': disk.percent}
        }
    except Exception:
        return {
            'cpu': 0,
            'memory': {'total': 0, 'used': 0, 'percent': 0},
            'disk': {'total': 0, 'used': 0, 'percent': 0}
        }

def get_container_stats():
    """Get CPU and memory usage for all running containers."""
    try:
        stats_raw = subprocess.check_output(
            ["docker", "stats", "--no-stream", "--format", "{{.ID}}|{{.CPUPerc}}|{{.MemUsage}}"],
            text=True
        ).strip().split('\n')
        
        stats = {}
        for line in stats_raw:
            parts = line.split('|')
            if len(parts) >= 3:
                container_id = parts[0]
                cpu_percent = parts[1].strip()
                mem_usage_raw = parts[2].strip()

                mem_match = re.match(r"(\d+(\.\d+)?\w+)\s+/\s+(\d+(\.\d+)?\w+)", mem_usage_raw)
                
                mem_used = 'N/A'
                mem_limit = 'N/A'
                
                if mem_match:
                    mem_used = mem_match.group(1)
                    mem_limit = mem_match.group(3)
                else:
                    mem_used = '0B'
                    mem_limit = '0B'

                stats[container_id] = {
                    'cpu': cpu_percent,
                    'mem_used': mem_used,
                    'mem_limit': mem_limit
                }
        return stats
    except Exception as e:
        print(f"Error getting container stats: {e}")
        return {}

async def send_to_logs(message):
    try:
        channel = bot.get_channel(LOGS_CHANNEL_ID)
        if channel:
            perms = channel.permissions_for(channel.guild.me)
            if perms.send_messages:
                timestamp = datetime.now().strftime("%H:%M:%S")
                await channel.send(f"`[{timestamp}]` {message}")
    except Exception as e:
        print(f"Failed to send logs: {e}")

# ==================== ADMIN MANAGEMENT ====================

class AdminView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
    
    @discord.ui.button(label="Add Admin", style=discord.ButtonStyle.success, emoji="👑", custom_id="add_admin")
    async def add_admin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_main_admin(interaction.user.id):
            await interaction.response.send_message(f"{EMOJI['error']} Only the main admin can use this!", ephemeral=True)
            return
        
        modal = AdminAddModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Remove Admin", style=discord.ButtonStyle.danger, emoji="👤", custom_id="remove_admin")
    async def remove_admin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_main_admin(interaction.user.id):
            await interaction.response.send_message(f"{EMOJI['error']} Only the main admin can use this!", ephemeral=True)
            return
        
        modal = AdminRemoveModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="List Admins", style=discord.ButtonStyle.primary, emoji="📋", custom_id="list_admins")
    async def list_admins_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user.id):
            await interaction.response.send_message(f"{EMOJI['error']} You are not an admin!", ephemeral=True)
            return
        
        admin_list = []
        for admin_id in bot.admins:
            user = await bot.fetch_user(admin_id)
            if user:
                admin_list.append(f"{EMOJI['admin']} {user.mention} (`{admin_id}`)")
        
        main_admin = await bot.fetch_user(bot.main_admin_id)
        
        embed = create_embed(
            "👑 Admin List",
            color=EMBED_COLOR,
            fields=[
                (f"{EMOJI['star']} **Main Admin**", f"{main_admin.mention} (`{bot.main_admin_id}`)", False),
                (f"{EMOJI['admin']} **Admins ({len(admin_list)})**", "\n".join(admin_list) if admin_list else "No additional admins", False)
            ]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AdminAddModal(discord.ui.Modal, title="Add Admin"):
    user_id = discord.ui.TextInput(
        label="User ID",
        placeholder="Enter the Discord user ID...",
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id.value)
            user = await bot.fetch_user(user_id)
            
            if user_id in bot.admins:
                await interaction.response.send_message(f"{EMOJI['warning']} User is already an admin!", ephemeral=True)
                return
            
            bot.admins.add(user_id)
            bot.save_admins()
            
            embed = create_embed(
                "✅ Admin Added",
                f"{EMOJI['admin']} {user.mention} has been added as an admin.",
                color=SUCCESS_COLOR
            )
            await interaction.response.send_message(embed=embed)
            await send_to_logs(f"👑 {interaction.user.mention} added {user.mention} as admin")
            
        except ValueError:
            await interaction.response.send_message(f"{EMOJI['error']} Invalid user ID!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"{EMOJI['error']} Error: {str(e)}", ephemeral=True)

class AdminRemoveModal(discord.ui.Modal, title="Remove Admin"):
    user_id = discord.ui.TextInput(
        label="User ID",
        placeholder="Enter the Discord user ID...",
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id.value)
            
            if user_id == bot.main_admin_id:
                await interaction.response.send_message(f"{EMOJI['error']} Cannot remove the main admin!", ephemeral=True)
                return
            
            if user_id not in bot.admins:
                await interaction.response.send_message(f"{EMOJI['warning']} User is not an admin!", ephemeral=True)
                return
            
            user = await bot.fetch_user(user_id)
            bot.admins.remove(user_id)
            bot.save_admins()
            
            embed = create_embed(
                "✅ Admin Removed",
                f"{EMOJI['user']} {user.mention} has been removed from admins.",
                color=SUCCESS_COLOR
            )
            await interaction.response.send_message(embed=embed)
            await send_to_logs(f"👤 {interaction.user.mention} removed {user.mention} from admins")
            
        except ValueError:
            await interaction.response.send_message(f"{EMOJI['error']} Invalid user ID!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"{EMOJI['error']} Error: {str(e)}", ephemeral=True)

# ==================== COMMANDS ====================

@bot.tree.command(name="admin", description="👑 Admin management panel")
async def admin_command(interaction: discord.Interaction):
    """Open admin management panel"""
    if not is_admin(interaction.user.id):
        embed = create_embed(
            "🚫 Permission Denied",
            f"{EMOJI['warning']} You are not an admin!",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    embed = create_embed(
        "👑 Admin Management",
        "Use the buttons below to manage administrators.",
        color=EMBED_COLOR
    )
    await interaction.response.send_message(embed=embed, view=AdminView(), ephemeral=True)

@bot.tree.command(name="admins", description="📋 List all admins")
async def list_admins_command(interaction: discord.Interaction):
    """List all admins"""
    admin_list = []
    for admin_id in bot.admins:
        user = await bot.fetch_user(admin_id)
        if user:
            admin_list.append(f"{EMOJI['admin']} {user.mention} (`{admin_id}`)")
    
    main_admin = await bot.fetch_user(bot.main_admin_id)
    
    embed = create_embed(
        "👑 Admin List",
        color=EMBED_COLOR,
        fields=[
            (f"{EMOJI['star']} **Main Admin**", f"{main_admin.mention} (`{bot.main_admin_id}`)", False),
            (f"{EMOJI['admin']} **Admins ({len(admin_list)})**", "\n".join(admin_list) if admin_list else "No additional admins", False)
        ]
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="deploy", description="🚀 [ADMIN] Create a new cloud instance for a user")
@app_commands.describe(
    user="The user to deploy for",
    os="The OS to deploy (ubuntu, debian, alpine, arch, kali, fedora)"
)
async def deploy(interaction: discord.Interaction, user: discord.User, os: str):
    """Deploy a new VPS (Admin only)"""
    if not is_admin(interaction.user.id):
        embed = create_embed(
            "🚫 Permission Denied",
            f"{EMOJI['warning']} This command is restricted to administrators only.",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    os = os.lower()
    if os not in OS_OPTIONS:
        valid_oses = "\n".join([f"{OS_OPTIONS[os_id]['emoji']} **{os_id}** - {OS_OPTIONS[os_id]['description']}" 
                               for os_id in OS_OPTIONS.keys()])
        embed = create_embed(
            "❌ Invalid OS Selection",
            f"**Available OS options:**\n{valid_oses}",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    os_data = OS_OPTIONS[os]
    
    # Check server limit
    if count_user_servers(str(user)) >= SERVER_LIMIT:
        embed = create_embed(
            "❌ Server Limit Reached",
            f"{EMOJI['warning']} User already has {SERVER_LIMIT} servers!",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Initial response
    embed = create_embed(
        f"🚀 Deploying {os_data['emoji']} {os_data['name']}",
        f"Creating instance for {user.mention}...\n"
        f"```RAM: {RAM_LIMIT}\nAuto-Delete: 4h Inactivity```",
        color=EMBED_COLOR,
        footer="This may take 1-2 minutes..."
    )
    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()

    try:
        # Create container
        embed.description = "```diff\n+ Pulling container image from repository...\n```"
        await msg.edit(embed=embed)
        
        container_id = subprocess.check_output(
            ["docker", "run", "-itd", "--privileged", os_data["image"]]
        ).strip().decode('utf-8')
        
        await send_to_logs(f"🔧 {interaction.user.mention} deployed {os_data['emoji']} {os_data['name']} for {user.mention} (ID: `{container_id[:12]}`)")
        
        # Setup SSH
        embed.description = "```diff\n+ Configuring SSH access and security...\n```"
        await msg.edit(embed=embed)

        exec_cmd = await asyncio.create_subprocess_exec(
            "docker", "exec", container_id, "tmate", "-F",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        ssh_session_line = await capture_ssh_session_line(exec_cmd)
        
        if ssh_session_line:
            # Success - send to admin and user
            admin_embed = create_embed(
                f"🎉 {os_data['emoji']} {os_data['name']} Instance Ready!",
                f"**Successfully deployed for {user.mention}**\n\n"
                f"**🔑 SSH Command:**\n```{ssh_session_line}```",
                color=SUCCESS_COLOR,
                fields=[
                    ("📦 Container Info", f"```ID: {container_id[:12]}\nOS: {os_data['name']}\nStatus: Running```", False)
                ],
                footer="💎 This instance will auto-delete after 4 hours of inactivity"
            )
            await interaction.followup.send(embed=admin_embed, ephemeral=True)
            
            try:
                user_embed = create_embed(
                    f"✨ Your {os_data['name']} Instance is Ready!",
                    f"**SSH Access Details:**\n```{ssh_session_line}```\n\nDeployed by: {interaction.user.mention}",
                    color=EMBED_COLOR,
                    fields=[
                        ("💡 Getting Started", "```Connect using any SSH client\nUsername: root\nNo password required```", False)
                    ],
                    footer="💎 This instance will auto-delete after 4 hours of inactivity"
                )
                await user.send(embed=user_embed)
            except discord.Forbidden:
                pass
            
            add_to_database(str(user), container_id, ssh_session_line)
            
            # Final success message
            embed = create_embed(
                f"✅ Deployment Complete! {random.choice(SUCCESS_ANIMATION)}",
                f"**{os_data['emoji']} {os_data['name']}** instance created for {user.mention}!",
                color=SUCCESS_COLOR
            )
            await msg.edit(embed=embed)
        else:
            embed = create_embed(
                f"⚠️ Timeout {random.choice(ERROR_ANIMATION)}",
                "```diff\n- SSH configuration timed out...\n- Rolling back deployment\n```",
                color=WARNING_COLOR
            )
            await msg.edit(embed=embed)
            subprocess.run(["docker", "kill", container_id], stderr=subprocess.DEVNULL)
            subprocess.run(["docker", "rm", container_id], stderr=subprocess.DEVNULL)
            
    except subprocess.CalledProcessError as e:
        embed = create_embed(
            f"❌ Deployment Failed {random.choice(ERROR_ANIMATION)}",
            f"```diff\n- Error during deployment:\n{e}\n```",
            color=ERROR_COLOR
        )
        await msg.edit(embed=embed)
        await send_to_logs(f"💥 Deployment failed for {user.mention} by {interaction.user.mention}: {e}")
        
    except Exception as e:
        print(f"Error in deploy command: {e}")
        embed = create_embed(
            "💥 Critical Error",
            "```diff\n- An unexpected error occurred\n- Please try again later\n```",
            color=ERROR_COLOR
        )
        await msg.edit(embed=embed)

@bot.tree.command(name="start", description="🟢 Start your cloud instance")
@app_commands.describe(container_id="Your instance ID (first 4+ characters)")
async def start_server(interaction: discord.Interaction, container_id: str):
    """Start a VPS"""
    try:
        user = str(interaction.user)
        container_info = None
        ssh_command = None
        
        if not os.path.exists(database_file):
            embed = create_embed(
                "📭 No Instances Found",
                "You don't have any active instances!",
                color=INFO_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        with open(database_file, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 3 and user == parts[0] and container_id in parts[1]:
                    container_info = parts[1]
                    ssh_command = parts[2]
                    break

        if not container_info:
            embed = create_embed(
                "🔍 Instance Not Found",
                "No instance found with that ID that belongs to you!",
                color=INFO_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = create_embed(
            f"🔌 Starting Instance {container_info[:12]}",
            "```diff\n+ Powering up your cloud instance...\n```",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        try:
            check_cmd = subprocess.run(
                ["docker", "inspect", "--format='{{.State.Status}}'", container_info],
                capture_output=True, text=True
            )
            
            if check_cmd.returncode != 0:
                embed = create_embed(
                    "❌ Container Not Found",
                    f"Container `{container_info[:12]}` doesn't exist in Docker!",
                    color=ERROR_COLOR
                )
                await msg.edit(embed=embed)
                remove_from_database(ssh_command)
                return
            
            subprocess.run(["docker", "start", container_info], check=True)
            
            try:
                embed.description = "```diff\n+ Generating new SSH connection...\n```"
                await msg.edit(embed=embed)
                
                exec_cmd = await asyncio.create_subprocess_exec(
                    "docker", "exec", container_info, "tmate", "-F",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                ssh_session_line = await capture_ssh_session_line(exec_cmd)
                
                if ssh_session_line:
                    remove_from_database(ssh_command)
                    add_to_database(user, container_info, ssh_session_line)
                    
                    try:
                        dm_embed = create_embed(
                            f"🟢 Instance Started {random.choice(SUCCESS_ANIMATION)}",
                            f"**Your instance is now running!**\n\n**🔑 New SSH Command:**\n```{ssh_session_line}```",
                            color=SUCCESS_COLOR,
                            fields=[("💡 Note", "The old SSH connection is no longer valid", False)]
                        )
                        await interaction.user.send(embed=dm_embed)
                    except discord.Forbidden:
                        pass
                    
                    embed = create_embed(
                        f"🟢 Instance Started {random.choice(SUCCESS_ANIMATION)}",
                        f"Instance `{container_info[:12]}` is now running!\n📩 Check your DMs for new connection details.",
                        color=SUCCESS_COLOR
                    )
                else:
                    embed = create_embed(
                        "⚠️ SSH Refresh Failed",
                        f"Instance `{container_info[:12]}` started but couldn't get new SSH details.",
                        color=WARNING_COLOR
                    )
            except Exception as e:
                print(f"Error getting new SSH session: {e}")
                embed = create_embed(
                    "🟢 Instance Started",
                    f"Instance `{container_info[:12]}` is running!\n⚠️ Could not refresh SSH details.",
                    color=WARNING_COLOR
                )
            
            await msg.edit(embed=embed)
            await send_to_logs(f"🟢 {interaction.user.mention} started instance `{container_info[:12]}`")
            
        except subprocess.CalledProcessError as e:
            embed = create_embed(
                f"❌ Startup Failed {random.choice(ERROR_ANIMATION)}",
                f"```diff\n- Error starting container:\n{e.stderr if e.stderr else e.stdout}\n```",
                color=ERROR_COLOR
            )
            await msg.edit(embed=embed)
            
    except Exception as e:
        print(f"Error in start_server: {e}")
        try:
            await interaction.followup.send(
                embed=create_embed("❌ Error", "An error occurred while processing your request.", color=ERROR_COLOR),
                ephemeral=True
            )
        except:
            pass

@bot.tree.command(name="stop", description="🛑 Stop your cloud instance")
@app_commands.describe(container_id="Your instance ID (first 4+ characters)")
async def stop_server(interaction: discord.Interaction, container_id: str):
    """Stop a VPS"""
    try:
        user = str(interaction.user)
        container_info = None
        
        if not os.path.exists(database_file):
            embed = create_embed(
                "📭 No Instances Found",
                "You don't have any active instances!",
                color=INFO_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        with open(database_file, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 3 and user == parts[0] and container_id in parts[1]:
                    container_info = parts[1]
                    break

        if not container_info:
            embed = create_embed(
                "🔍 Instance Not Found",
                "No instance found with that ID that belongs to you!",
                color=INFO_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = create_embed(
            f"⏳ Stopping Instance {container_info[:12]}",
            "```diff\n+ Shutting down your cloud instance...\n```",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        try:
            check_cmd = subprocess.run(
                ["docker", "inspect", container_info],
                capture_output=True, text=True
            )
            
            if check_cmd.returncode != 0:
                embed = create_embed(
                    "❌ Container Not Found",
                    f"Container `{container_info[:12]}` doesn't exist in Docker!",
                    color=ERROR_COLOR
                )
                await msg.edit(embed=embed)
                remove_from_database(container_info)
                return
            
            subprocess.run(["docker", "stop", container_info], check=True)
            
            embed = create_embed(
                f"🛑 Instance Stopped {random.choice(SUCCESS_ANIMATION)}",
                f"Instance `{container_info[:12]}` has been successfully stopped!",
                color=SUCCESS_COLOR
            )
            await msg.edit(embed=embed)
            await send_to_logs(f"🛑 {interaction.user.mention} stopped instance `{container_info[:12]}`")
            
        except subprocess.CalledProcessError as e:
            embed = create_embed(
                f"❌ Stop Failed {random.choice(ERROR_ANIMATION)}",
                f"```diff\n- Error stopping container:\n{e.stderr if e.stderr else e.stdout}\n```",
                color=ERROR_COLOR
            )
            await msg.edit(embed=embed)
            
    except Exception as e:
        print(f"Error in stop_server: {e}")
        try:
            await interaction.followup.send(
                embed=create_embed("❌ Error", "An error occurred while processing your request.", color=ERROR_COLOR),
                ephemeral=True
            )
        except:
            pass

@bot.tree.command(name="restart", description="🔄 Restart your cloud instance")
@app_commands.describe(container_id="Your instance ID (first 4+ characters)")
async def restart_server(interaction: discord.Interaction, container_id: str):
    """Restart a VPS"""
    try:
        user = str(interaction.user)
        container_info = None
        ssh_command = None
        
        if not os.path.exists(database_file):
            embed = create_embed(
                "📭 No Instances Found",
                "You don't have any active instances!",
                color=INFO_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        with open(database_file, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 3 and user == parts[0] and container_id in parts[1]:
                    container_info = parts[1]
                    ssh_command = parts[2]
                    break

        if not container_info:
            embed = create_embed(
                "🔍 Instance Not Found",
                "No instance found with that ID that belongs to you!",
                color=INFO_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = create_embed(
            f"🔄 Restarting Instance {container_info[:12]}",
            "```diff\n+ Rebooting your cloud instance...\n```",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        try:
            check_cmd = subprocess.run(
                ["docker", "inspect", container_info],
                capture_output=True, text=True
            )
            
            if check_cmd.returncode != 0:
                embed = create_embed(
                    "❌ Container Not Found",
                    f"Container `{container_info[:12]}` doesn't exist in Docker!",
                    color=ERROR_COLOR
                )
                await msg.edit(embed=embed)
                remove_from_database(ssh_command)
                return
            
            subprocess.run(["docker", "restart", container_info], check=True)
            
            embed.description = "```diff\n+ Generating new SSH connection...\n```"
            await msg.edit(embed=embed)
            
            try:
                exec_cmd = await asyncio.create_subprocess_exec(
                    "docker", "exec", container_info, "tmate", "-F",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                ssh_session_line = await capture_ssh_session_line(exec_cmd)
                
                if ssh_session_line:
                    remove_from_database(ssh_command)
                    add_to_database(user, container_info, ssh_session_line)
                    
                    try:
                        dm_embed = create_embed(
                            f"🔄 Instance Restarted {random.choice(SUCCESS_ANIMATION)}",
                            f"**Your instance has been restarted!**\n\n**🔑 New SSH Command:**\n```{ssh_session_line}```",
                            color=SUCCESS_COLOR,
                            fields=[("💡 Note", "The old SSH connection is no longer valid", False)]
                        )
                        await interaction.user.send(embed=dm_embed)
                    except discord.Forbidden:
                        pass
                    
                    embed = create_embed(
                        f"🔄 Instance Restarted {random.choice(SUCCESS_ANIMATION)}",
                        f"Instance `{container_info[:12]}` has been restarted!\n📩 Check your DMs for new connection details.",
                        color=SUCCESS_COLOR
                    )
                else:
                    embed = create_embed(
                        "⚠️ SSH Refresh Failed",
                        f"Instance `{container_info[:12]}` restarted but couldn't get new SSH details.",
                        color=WARNING_COLOR
                    )
            except Exception as e:
                print(f"Error getting new SSH session: {e}")
                embed = create_embed(
                    "🔄 Instance Restarted",
                    f"Instance `{container_info[:12]}` has been restarted!\n⚠️ Could not refresh SSH details.",
                    color=WARNING_COLOR
                )
            
            await msg.edit(embed=embed)
            await send_to_logs(f"🔄 {interaction.user.mention} restarted instance `{container_info[:12]}`")
            
        except subprocess.CalledProcessError as e:
            embed = create_embed(
                f"❌ Restart Failed {random.choice(ERROR_ANIMATION)}",
                f"```diff\n- Error restarting container:\n{e.stderr if e.stderr else e.stdout}\n```",
                color=ERROR_COLOR
            )
            await msg.edit(embed=embed)
            
    except Exception as e:
        print(f"Error in restart_server: {e}")
        try:
            await interaction.followup.send(
                embed=create_embed("❌ Error", "An error occurred while processing your request.", color=ERROR_COLOR),
                ephemeral=True
            )
        except:
            pass

@bot.tree.command(name="remove", description="❌ Permanently delete your cloud instance")
@app_commands.describe(container_id="Your instance ID (first 4+ characters)")
async def remove_server(interaction: discord.Interaction, container_id: str):
    """Remove a VPS"""
    try:
        user = str(interaction.user)
        container_info = None
        ssh_command = None
        
        if not os.path.exists(database_file):
            embed = create_embed(
                "📭 No Instances Found",
                "You don't have any active instances!",
                color=INFO_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        with open(database_file, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 3 and user == parts[0] and container_id in parts[1]:
                    container_info = parts[1]
                    ssh_command = parts[2]
                    break

        if not container_info:
            embed = create_embed(
                "🔍 Instance Not Found",
                "No instance found with that ID that belongs to you!",
                color=INFO_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.value = None
            
            @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()
                
                await interaction.response.defer()
                
                try:
                    check_cmd = subprocess.run(
                        ["docker", "inspect", container_info],
                        capture_output=True, text=True
                    )
                    
                    if check_cmd.returncode != 0:
                        embed = create_embed(
                            "❌ Container Not Found",
                            f"Container `{container_info[:12]}` doesn't exist in Docker!",
                            color=ERROR_COLOR
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        remove_from_database(ssh_command)
                        return
                    
                    subprocess.run(["docker", "stop", container_info], check=True)
                    subprocess.run(["docker", "rm", container_info], check=True)
                    
                    remove_from_database(ssh_command)
                    
                    embed = create_embed(
                        f"🗑️ Instance Deleted {random.choice(SUCCESS_ANIMATION)}",
                        f"Instance `{container_info[:12]}` has been permanently deleted!",
                        color=SUCCESS_COLOR
                    )
                    await interaction.followup.send(embed=embed)
                    await send_to_logs(f"❌ {interaction.user.mention} deleted instance `{container_info[:12]}`")
                    
                except subprocess.CalledProcessError as e:
                    embed = create_embed(
                        f"❌ Deletion Failed {random.choice(ERROR_ANIMATION)}",
                        f"```diff\n- Error deleting container:\n{e.stderr if e.stderr else e.stdout}\n```",
                        color=ERROR_COLOR
                    )
                    await interaction.followup.send(embed=embed)
            
            @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()
                embed = create_embed(
                    "Deletion Cancelled",
                    f"Instance `{container_info[:12]}` was not deleted.",
                    color=INFO_COLOR
                )
                await interaction.response.edit_message(embed=embed, view=None)
        
        embed = create_embed(
            "⚠️ Confirm Deletion",
            f"Are you sure you want to **permanently delete** instance `{container_info[:12]}`?",
            color=WARNING_COLOR,
            footer="This action cannot be undone!"
        )
        
        view = ConfirmView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
    except Exception as e:
        print(f"Error in remove_server: {e}")
        try:
            await interaction.followup.send(
                embed=create_embed("❌ Error", "An error occurred while processing your request.", color=ERROR_COLOR),
                ephemeral=True
            )
        except:
            pass

@bot.tree.command(name="regen-ssh", description="🔄 Regenerate SSH connection for your instance")
@app_commands.describe(container_id="Your instance ID (first 4+ characters)")
async def regen_ssh(interaction: discord.Interaction, container_id: str):
    """Regenerate SSH for a VPS"""
    try:
        user = str(interaction.user)
        container_info = None
        old_ssh_command = None
        
        if not os.path.exists(database_file):
            embed = create_embed(
                "📭 No Instances Found",
                "You don't have any active instances!",
                color=INFO_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        with open(database_file, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 3 and user == parts[0] and container_id in parts[1]:
                    container_info = parts[1]
                    old_ssh_command = parts[2]
                    break

        if not container_info:
            embed = create_embed(
                "🔍 Instance Not Found",
                "No instance found with that ID that belongs to you!",
                color=INFO_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            check_cmd = subprocess.run(
                ["docker", "inspect", "--format='{{.State.Status}}'", container_info],
                capture_output=True, text=True
            )
            
            if check_cmd.returncode != 0:
                embed = create_embed(
                    "❌ Container Not Found",
                    f"Container `{container_info[:12]}` doesn't exist in Docker!",
                    color=ERROR_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                remove_from_database(old_ssh_command)
                return
            
            container_status = check_cmd.stdout.strip().strip("'")
            if container_status != "running":
                embed = create_embed(
                    "⚠️ Instance Not Running",
                    f"Container `{container_info[:12]}` is not running. Start it first with `/start`.",
                    color=WARNING_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = create_embed(
                "⚙️ Regenerating SSH Connection",
                f"```diff\n+ Generating new SSH details for {container_info[:12]}...\n```",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed)
            msg = await interaction.original_response()

            try:
                subprocess.run(
                    ["docker", "exec", container_info, "pkill", "tmate"],
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
                )
                
                exec_cmd = await asyncio.create_subprocess_exec(
                    "docker", "exec", container_info, "tmate", "-F",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                ssh_session_line = await capture_ssh_session_line(exec_cmd)
                
                if ssh_session_line:
                    remove_from_database(old_ssh_command)
                    add_to_database(user, container_info, ssh_session_line)
                    
                    try:
                        dm_embed = create_embed(
                            f"🔄 SSH Regenerated {random.choice(SUCCESS_ANIMATION)}",
                            f"**New SSH Connection Details:**\n```{ssh_session_line}```",
                            color=SUCCESS_COLOR,
                            fields=[("⚠️ Important", "The old SSH connection is no longer valid", False)]
                        )
                        await interaction.user.send(embed=dm_embed)
                    except discord.Forbidden:
                        pass
                    
                    embed = create_embed(
                        f"✅ SSH Regenerated {random.choice(SUCCESS_ANIMATION)}",
                        f"New SSH details generated for `{container_info[:12]}`!\n📩 Check your DMs for the new connection.",
                        color=SUCCESS_COLOR
                    )
                else:
                    embed = create_embed(
                        "⚠️ SSH Regeneration Failed",
                        f"Could not generate new SSH details for `{container_info[:12]}`.\nTry again later.",
                        color=WARNING_COLOR
                    )
            except Exception as e:
                print(f"Error regenerating SSH: {e}")
                embed = create_embed(
                    "❌ SSH Regeneration Failed",
                    f"An error occurred while regenerating SSH for `{container_info[:12]}`.",
                    color=ERROR_COLOR
                )
            
            await msg.edit(embed=embed)
            
            if ssh_session_line:
                await send_to_logs(f"🔄 {interaction.user.mention} regenerated SSH for instance `{container_info[:12]}`")
            
        except subprocess.CalledProcessError as e:
            embed = create_embed(
                "❌ Error Regenerating SSH",
                f"```diff\n- Error:\n{e.stderr if e.stderr else e.stdout}\n```",
                color=ERROR_COLOR
            )
            try:
                await msg.edit(embed=embed)
            except:
                pass
            
    except Exception as e:
        print(f"Error in regen_ssh: {e}")
        try:
            await interaction.followup.send(
                embed=create_embed("❌ Error", "An error occurred while processing your request.", color=ERROR_COLOR),
                ephemeral=True
            )
        except:
            pass

@bot.tree.command(name="list", description="📜 List your cloud instances")
async def list_servers(interaction: discord.Interaction):
    """List user's VPS"""
    try:
        user = str(interaction.user)
        servers = get_user_servers(user)
        
        if not servers:
            embed = create_embed(
                "📭 No Instances Found",
                "You don't have any active instances.",
                color=INFO_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = create_embed(
            f"📋 Your Cloud Instances ({len(servers)}/{SERVER_LIMIT})",
            color=EMBED_COLOR
        )
        
        for server in servers:
            parts = server.split('|')
            if len(parts) < 3:
                continue
                
            container_id = parts[1]
            os_type = "Unknown"
            
            for os_id, os_data in OS_OPTIONS.items():
                if os_id in parts[2].lower():
                    os_type = f"{os_data['emoji']} {os_data['name']}"
                    break
                    
            try:
                status = subprocess.check_output(
                    ["docker", "inspect", "--format='{{.State.Status}}'", container_id],
                    stderr=subprocess.DEVNULL
                ).decode('utf-8').strip().strip("'")
                
                status_emoji = "🟢" if status == "running" else "🔴"
                status_text = f"{status_emoji} {status.capitalize()}"
            except:
                status_text = "🔴 Unknown"
                    
            embed.add_field(
                name=f"🖥️ Instance `{container_id[:12]}`",
                value=(
                    f"▫️ **OS**: {os_type}\n"
                    f"▫️ **Status**: {status_text}\n"
                    f"▫️ **ID**: `{container_id[:12]}`"
                ),
                inline=False
            )
        
        embed.set_footer(text="Use /start, /stop, or /remove with the instance ID")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"Error in list_servers: {e}")
        try:
            await interaction.followup.send(
                embed=create_embed("❌ Error", "An error occurred while processing your request.", color=ERROR_COLOR),
                ephemeral=True
            )
        except:
            pass

@bot.tree.command(name="list-all", description="📜 [ADMIN] List all deployed instances")
async def list_all_servers(interaction: discord.Interaction):
    """List all VPS (Admin only)"""
    if not is_admin(interaction.user.id):
        embed = create_embed(
            "🚫 Permission Denied",
            f"{EMOJI['warning']} This command is restricted to administrators only.",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        await interaction.response.defer()

        servers = get_all_servers()
        container_stats = get_container_stats()
        host_stats = get_system_resources()
        
        embed = create_embed(
            f"📊 System Overview - All Instances ({len(servers)} total)",
            color=EMBED_COLOR
        )

        cpu_emoji = "🟢" if host_stats['cpu'] < 70 else "🟡" if host_stats['cpu'] < 90 else "🔴"
        mem_emoji = "🟢" if host_stats['memory']['percent'] < 70 else "🟡" if host_stats['memory']['percent'] < 90 else "🔴"
        disk_emoji = "🟢" if host_stats['disk']['percent'] < 70 else "🟡" if host_stats['disk']['percent'] < 90 else "🔴"
        
        embed.add_field(
            name="🖥️ Host System Resources",
            value=(
                f"{cpu_emoji} **CPU Usage**: {host_stats['cpu']}%\n"
                f"{mem_emoji} **Memory**: {host_stats['memory']['used']}GB / {host_stats['memory']['total']}GB ({host_stats['memory']['percent']}%)\n"
                f"{disk_emoji} **Disk**: {host_stats['disk']['used']}GB / {host_stats['disk']['total']}GB ({host_stats['disk']['percent']}%)"
            ),
            inline=False
        )
        embed.add_field(name="\u200b", value="\u200b", inline=False)

        if not servers:
            embed.add_field(
                name="📭 No Instances Found",
                value="There are no active instances.",
                inline=False
            )
            await interaction.followup.send(embed=embed)
            return

        for server in servers:
            parts = server.split('|')
            if len(parts) < 3:
                continue
                
            user_owner = parts[0]
            container_id = parts[1]
            os_type = "Unknown"
            
            for os_id, os_data in OS_OPTIONS.items():
                if os_id in parts[2].lower():
                    os_type = f"{os_data['emoji']} {os_data['name']}"
                    break

            stats = container_stats.get(container_id, {'cpu': '0.00%', 'mem_used': '0B', 'mem_limit': '0B'})
            
            try:
                status = subprocess.check_output(
                    ["docker", "inspect", "--format='{{.State.Status}}'", container_id],
                    stderr=subprocess.DEVNULL
                ).decode('utf-8').strip().strip("'")
                
                status_emoji = "🟢" if status == "running" else "🔴"
                status_text = f"{status_emoji} {status.capitalize()}"
            except:
                status_text = "🔴 Unknown"
            
            embed.add_field(
                name=f"🖥️ Instance `{container_id[:12]}`",
                value=(
                    f"▫️ **Owner**: `{user_owner}`\n"
                    f"▫️ **OS**: {os_type}\n"
                    f"▫️ **Status**: {status_text}\n"
                    f"▫️ **CPU**: {stats['cpu']}\n"
                    f"▫️ **RAM**: {stats['mem_used']} / {stats['mem_limit']}"
                ),
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"Error in list_all_servers: {e}")
        try:
            await interaction.followup.send(
                embed=create_embed("❌ Error", "An error occurred while processing your request.", color=ERROR_COLOR),
                ephemeral=True
            )
        except:
            pass

@bot.tree.command(name="delete-container", description="❌ [ADMIN] Delete any container by ID")
@app_commands.describe(container_id="The ID of the container to delete")
async def delete_user_container(interaction: discord.Interaction, container_id: str):
    """Delete any container (Admin only)"""
    if not is_admin(interaction.user.id):
        embed = create_embed(
            "🚫 Permission Denied",
            f"{EMOJI['warning']} This command is restricted to administrators only.",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        user_owner, container_info, ssh_command = get_container_info_by_id(container_id)
        
        if not container_info:
            embed = create_embed(
                "❌ Container Not Found",
                f"Could not find a container with the ID `{container_id[:12]}`.",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Confirmation view
        class AdminConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.value = None
            
            @discord.ui.button(label="☠️ Force Delete", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()
                
                await interaction.response.defer()
                
                try:
                    subprocess.run(["docker", "stop", container_info], check=True)
                    subprocess.run(["docker", "rm", container_info], check=True)
                    remove_container_from_database_by_id(container_info)
                    
                    embed = create_embed(
                        f"☠️ Container Force Deleted {random.choice(SUCCESS_ANIMATION)}",
                        f"Successfully deleted container `{container_info[:12]}`\n**Owner**: {user_owner}",
                        color=SUCCESS_COLOR
                    )
                    await interaction.followup.send(embed=embed)
                    await send_to_logs(f"💥 {interaction.user.mention} force-deleted container `{container_info[:12]}` owned by `{user_owner}`")

                except subprocess.CalledProcessError as e:
                    embed = create_embed(
                        f"❌ Deletion Failed {random.choice(ERROR_ANIMATION)}",
                        f"```diff\n- Error:\n{e.stderr if e.stderr else e.stdout}\n```",
                        color=ERROR_COLOR
                    )
                    await interaction.followup.send(embed=embed)
            
            @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()
                embed = create_embed(
                    "Deletion Cancelled",
                    f"Container `{container_info[:12]}` was not deleted.",
                    color=INFO_COLOR
                )
                await interaction.response.edit_message(embed=embed, view=None)
        
        embed = create_embed(
            "⚠️ Confirm Force Deletion",
            f"You are about to **force delete** container `{container_info[:12]}`\n"
            f"**Owner**: {user_owner}\n\n"
            "This action is irreversible!",
            color=WARNING_COLOR
        )
        
        view = AdminConfirmView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
    except Exception as e:
        print(f"Error in delete_user_container: {e}")
        try:
            await interaction.followup.send(
                embed=create_embed("❌ Error", "An error occurred while processing your request.", color=ERROR_COLOR),
                ephemeral=True
            )
        except:
            pass

@bot.tree.command(name="resources", description="📊 Show host system resources")
async def resources_command(interaction: discord.Interaction):
    """Show system resources"""
    try:
        resources = get_system_resources()
        
        cpu_emoji = "🟢" if resources['cpu'] < 70 else "🟡" if resources['cpu'] < 90 else "🔴"
        mem_emoji = "🟢" if resources['memory']['percent'] < 70 else "🟡" if resources['memory']['percent'] < 90 else "🔴"
        disk_emoji = "🟢" if resources['disk']['percent'] < 70 else "🟡" if resources['disk']['percent'] < 90 else "🔴"
        
        embed = create_embed(
            "📊 Host System Resources",
            color=EMBED_COLOR,
            fields=[
                (f"{cpu_emoji} CPU Usage", f"```{resources['cpu']}%```", True),
                (f"{mem_emoji} Memory", f"```{resources['memory']['used']}GB / {resources['memory']['total']}GB\n({resources['memory']['percent']}%)```", True),
                (f"{disk_emoji} Disk Space", f"```{resources['disk']['used']}GB / {resources['disk']['total']}GB\n({resources['disk']['percent']}%)```", True)
            ]
        )
        
        health_score = (100 - resources['cpu']) * 0.3 + (100 - resources['memory']['percent']) * 0.4 + (100 - resources['disk']['percent']) * 0.3
        if health_score > 80:
            health_msg = "🌟 Excellent system health!"
        elif health_score > 60:
            health_msg = "👍 Good system performance"
        elif health_score > 40:
            health_msg = "⚠️ System under moderate load"
        else:
            health_msg = "🚨 Critical system load!"
            
        embed.add_field(name="System Health", value=health_msg, inline=False)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"Error in resources_command: {e}")
        await interaction.response.send_message(
            embed=create_embed("❌ Error", "An error occurred while processing your request.", color=ERROR_COLOR),
            ephemeral=True
        )

@bot.tree.command(name="ping", description="🏓 Check bot latency")
async def ping_command(interaction: discord.Interaction):
    """Check bot latency"""
    try:
        latency = round(bot.latency * 1000)
        
        if latency < 100:
            emoji = "⚡"
            status = "Excellent"
        elif latency < 300:
            emoji = "🏓"
            status = "Good"
        elif latency < 500:
            emoji = "🐢"
            status = "Slow"
        else:
            emoji = "🐌"
            status = "Laggy"
            
        embed = create_embed(
            f"{emoji} Pong!",
            f"**Bot Latency**: {latency}ms\n**Status**: {status}",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"Error in ping_command: {e}")
        await interaction.response.send_message(
            embed=create_embed("❌ Error", "An error occurred while processing your request.", color=ERROR_COLOR),
            ephemeral=True
        )

@bot.tree.command(name="uptime", description="⏱️ Show bot uptime")
async def uptime_command(interaction: discord.Interaction):
    """Show bot uptime"""
    uptime = datetime.now() - bot.start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    
    embed = create_embed(
        "⏱️ Bot Uptime",
        f"**Online for:** `{uptime_str}`\n**Started:** <t:{int(bot.start_time.timestamp())}:R>",
        color=EMBED_COLOR
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="about", description="ℹ️ About the bot")
async def about_command(interaction: discord.Interaction):
    """About the bot"""
    total_servers = len(get_all_servers())
    total_users = len(set([s.split('|')[0] for s in get_all_servers()]))
    
    embed = create_embed(
        f"About {bot.bot_name}",
        f"{EMOJI['vps']} **Modern VPS Management Bot**",
        color=EMBED_COLOR,
        fields=[
            ("👑 **Main Admin**", f"<@{bot.main_admin_id}>", True),
            ("👥 **Admins**", f"{len(bot.admins)}", True),
            ("🚀 **Total VPS**", f"{total_servers}", True),
            ("👤 **Users**", f"{total_users}", True),
            ("📊 **Server Limit**", f"{SERVER_LIMIT} per user", True)
        ],
        footer="Created with 💖"
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="❓ Show help message")
async def help_command(interaction: discord.Interaction):
    """Show help"""
    embed = create_embed(
        "✨ VPS Bot Help",
        "Here are all available commands:",
        color=EMBED_COLOR
    )

    commands_list = [
        ("📜 `/list`", "List your instances"),
        ("📜 `/list-all`", "[ADMIN] List all instances"),
        ("🟢 `/start <id>`", "Start your instance"),
        ("🛑 `/stop <id>`", "Stop your instance"),
        ("🔄 `/restart <id>`", "Restart your instance"),
        ("🔄 `/regen-ssh <id>`", "Regenerate SSH"),
        ("🗑️ `/remove <id>`", "Delete an instance"),
        ("📊 `/resources`", "Show system resources"),
        ("🏓 `/ping`", "Check latency"),
        ("⏱️ `/uptime`", "Bot uptime"),
        ("ℹ️ `/about`", "About the bot"),
        ("👑 `/admin`", "[ADMIN] Manage admins"),
        ("👑 `/admins`", "List admins"),
        ("❌ `/delete-container <id>`", "[ADMIN] Force delete container")
    ]
    
    # Add deploy command for admins
    if is_admin(interaction.user.id):
        commands_list.insert(0, ("🚀 `/deploy @user <os>`", "[ADMIN] Deploy VPS"))
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    # Add OS information
    os_info = "\n".join([f"{os_data['emoji']} **{os_id}** - {os_data['description']}" 
                        for os_id, os_data in OS_OPTIONS.items()])
    embed.add_field(name="🖥️ Available Operating Systems", value=os_info, inline=False)
    
    await interaction.response.send_message(embed=embed)

# ==================== EVENTS ====================

@bot.event
async def on_ready():
    """Called when bot is ready"""
    print(f"✅ {bot.bot_name} is online!")
    print(f"📊 Bot ID: {bot.user.id}")
    print(f"👑 Main Admin: {bot.main_admin_id}")
    print(f"👥 Admins: {len(bot.admins)}")
    print(f"📁 Database: {os.path.exists(database_file)}")
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")
    
    change_status.start()

@tasks.loop(seconds=5)
async def change_status():
    """Change bot status periodically"""
    try:
        instance_count = len(open(database_file).readlines()) if os.path.exists(database_file) else 0
        statuses = [
            f"🌠 Managing {instance_count} Instances",
            f"⚡ Powering {instance_count} Servers",
            f"🔮 Watching {instance_count} VMs",
            f"🚀 Hosting {instance_count} VPS",
            f"💻 Serving {instance_count} Terminals",
            f"🌐 Running {instance_count} Nodes"
        ]
        await bot.change_presence(activity=discord.Game(name=random.choice(statuses)))
    except Exception as e:
        print(f"💥 Failed to update status: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Error: {error}")

# ==================== START BOT ====================
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        bot.save_admins()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        bot.save_admins()
