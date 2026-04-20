import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import json
import os

# Configuración del bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# Archivo para almacenar warnings
WARNINGS_FILE = "warnings.json"

# Cargar warnings existentes
def load_warnings():
    if os.path.exists(WARNINGS_FILE):
        with open(WARNINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_warnings(warnings):
    with open(WARNINGS_FILE, "w") as f:
        json.dump(warnings, f, indent=4)

warnings_data = load_warnings()

@bot.event
async def on_ready():
    # Sincronizar comandos slash
    await bot.tree.sync()
    print(f"✅ Bot conectado como {bot.user}")
    
    # Estado personalizado con streaming
    await bot.change_presence(activity=discord.Streaming(
        name="Aqirax On Top",
        url="https://www.twitch.tv/xentury_oficial"
    ))

# Verificar permisos de moderación
def is_moderator():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.manage_messages or interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

# Comando /clear
@bot.tree.command(name="clear", description="Elimina una cantidad específica de mensajes")
@app_commands.describe(cantidad="Número de mensajes a eliminar (1-100)")
@is_moderator()
async def clear(interaction: discord.Interaction, cantidad: int):
    if cantidad < 1 or cantidad > 100:
        await interaction.response.send_message("❌ La cantidad debe ser entre 1 y 100.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    purged = await interaction.channel.purge(limit=cantidad)
    await interaction.followup.send(f"✅ Se eliminaron {len(purged)} mensajes.", ephemeral=True)

# Comando /ban
@bot.tree.command(name="ban", description="Banea a un usuario del servidor")
@app_commands.describe(usuario="Usuario a banear", razon="Razón del baneo")
@is_moderator()
async def ban(interaction: discord.Interaction, usuario: discord.Member, razon: str = "No especificada"):
    if usuario == interaction.user:
        await interaction.response.send_message("❌ No puedes banearte a ti mismo.", ephemeral=True)
        return
    
    if usuario.guild_permissions.administrator:
        await interaction.response.send_message("❌ No puedes banear a un administrador.", ephemeral=True)
        return
    
    try:
        await usuario.ban(reason=razon)
        await interaction.response.send_message(f"✅ {usuario.mention} ha sido baneado.\n📝 Razón: {razon}")
        
        # Enviar DM al usuario baneado
        try:
            await usuario.send(f"🔨 Has sido baneado de {interaction.guild.name}\n📝 Razón: {razon}")
        except:
            pass
    except:
        await interaction.response.send_message("❌ No se pudo banear al usuario.", ephemeral=True)

# Comando /unban
@bot.tree.command(name="unban", description="Desbanea a un usuario")
@app_commands.describe(usuario="Nombre#Tag del usuario a desbanear")
@is_moderator()
async def unban(interaction: discord.Interaction, usuario: str):
    banned_users = [entry async for entry in interaction.guild.bans()]
    
    for ban_entry in banned_users:
        user = ban_entry.user
        if str(user) == usuario:
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✅ {user.mention} ha sido desbaneado.")
            return
    
    await interaction.response.send_message(f"❌ Usuario {usuario} no encontrado en la lista de baneados.", ephemeral=True)

# Comando /kick
@bot.tree.command(name="kick", description="Expulsa a un usuario del servidor")
@app_commands.describe(usuario="Usuario a expulsar", razon="Razón de la expulsión")
@is_moderator()
async def kick(interaction: discord.Interaction, usuario: discord.Member, razon: str = "No especificada"):
    if usuario == interaction.user:
        await interaction.response.send_message("❌ No puedes expulsarte a ti mismo.", ephemeral=True)
        return
    
    if usuario.guild_permissions.administrator:
        await interaction.response.send_message("❌ No puedes expulsar a un administrador.", ephemeral=True)
        return
    
    try:
        await usuario.kick(reason=razon)
        await interaction.response.send_message(f"✅ {usuario.mention} ha sido expulsado.\n📝 Razón: {razon}")
        
        try:
            await usuario.send(f"👢 Has sido expulsado de {interaction.guild.name}\n📝 Razón: {razon}")
        except:
            pass
    except:
        await interaction.response.send_message("❌ No se pudo expulsar al usuario.", ephemeral=True)

# Comando /timeout
@bot.tree.command(name="timeout", description="Aplica timeout a un usuario")
@app_commands.describe(usuario="Usuario para aplicar timeout", tiempo="Tiempo (ej: 1m, 1h, 1d)")
@is_moderator()
async def timeout(interaction: discord.Interaction, usuario: discord.Member, tiempo: str):
    if usuario == interaction.user:
        await interaction.response.send_message("❌ No puedes aplicarte timeout a ti mismo.", ephemeral=True)
        return
    
    # Convertir tiempo a segundos
    tiempo_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    try:
        valor = int(tiempo[:-1])
        unidad = tiempo[-1].lower()
        if unidad not in tiempo_map:
            raise ValueError
        segundos = valor * tiempo_map[unidad]
        if segundos > 2419200:  # 28 días máximo
            await interaction.response.send_message("❌ El timeout no puede ser mayor a 28 días.", ephemeral=True)
            return
    except:
        await interaction.response.send_message("❌ Formato inválido. Usa ej: 30s, 5m, 2h, 1d", ephemeral=True)
        return
    
    try:
        until = discord.utils.utcnow() + timedelta(seconds=segundos)
        await usuario.timeout(until, reason=f"Timeout aplicado por {interaction.user}")
        await interaction.response.send_message(f"✅ {usuario.mention} ha recibido timeout por {tiempo}.")
        
        try:
            await usuario.send(f"⏰ Has recibido timeout en {interaction.guild.name} por {tiempo}")
        except:
            pass
    except:
        await interaction.response.send_message("❌ No se pudo aplicar el timeout.", ephemeral=True)

# Comando /warn
@bot.tree.command(name="warn", description="Advierte a un usuario")
@app_commands.describe(usuario="Usuario a advertir", razon="Razón de la advertencia")
@is_moderator()
async def warn(interaction: discord.Interaction, usuario: discord.Member, razon: str = "No especificada"):
    if usuario == interaction.user:
        await interaction.response.send_message("❌ No puedes advertirte a ti mismo.", ephemeral=True)
        return
    
    user_id = str(usuario.id)
    if user_id not in warnings_data:
        warnings_data[user_id] = []
    
    warning = {
        "reason": razon,
        "moderator": str(interaction.user),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    warnings_data[user_id].append(warning)
    save_warnings(warnings_data)
    
    await interaction.response.send_message(f"⚠️ {usuario.mention} ha sido advertido.\n📝 Razón: {razon}\n📊 Total de warns: {len(warnings_data[user_id])}")
    
    # Enviar DM al usuario
    try:
        await usuario.send(f"⚠️ Has recibido una advertencia en {interaction.guild.name}\n📝 Razón: {razon}")
    except:
        pass

# Comando /warnings
@bot.tree.command(name="warnings", description="Muestra las advertencias de un usuario")
@app_commands.describe(usuario="Usuario para ver sus advertencias")
@is_moderator()
async def warnings(interaction: discord.Interaction, usuario: discord.Member):
    user_id = str(usuario.id)
    
    if user_id not in warnings_data or not warnings_data[user_id]:
        await interaction.response.send_message(f"✅ {usuario.mention} no tiene advertencias.")
        return
    
    embed = discord.Embed(
        title=f"Advertencias de {usuario.name}",
        color=discord.Color.orange()
    )
    
    for i, warning in enumerate(warnings_data[user_id], 1):
        embed.add_field(
            name=f"Advertencia #{i}",
            value=f"📝 Razón: {warning['reason']}\n👮 Moderador: {warning['moderator']}\n📅 Fecha: {warning['date']}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

# Comando /clear_warn
@bot.tree.command(name="clear_warn", description="Elimina una advertencia específica de un usuario")
@app_commands.describe(usuario="Usuario", numero="Número de advertencia a eliminar")
@is_moderator()
async def clear_warn(interaction: discord.Interaction, usuario: discord.Member, numero: int):
    user_id = str(usuario.id)
    
    if user_id not in warnings_data or not warnings_data[user_id]:
        await interaction.response.send_message(f"❌ {usuario.mention} no tiene advertencias.", ephemeral=True)
        return
    
    if numero < 1 or numero > len(warnings_data[user_id]):
        await interaction.response.send_message(f"❌ Número inválido. El usuario tiene {len(warnings_data[user_id])} advertencia(s).", ephemeral=True)
        return
    
    removed = warnings_data[user_id].pop(numero - 1)
    save_warnings(warnings_data)
    
    await interaction.response.send_message(f"✅ Se eliminó la advertencia #{numero} de {usuario.mention}\n📝 Razón eliminada: {removed['reason']}")

# Comando /clear_warns
@bot.tree.command(name="clear_warns", description="Elimina TODAS las advertencias de un usuario")
@app_commands.describe(usuario="Usuario")
@is_moderator()
async def clear_warns(interaction: discord.Interaction, usuario: discord.Member):
    user_id = str(usuario.id)
    
    if user_id not in warnings_data or not warnings_data[user_id]:
        await interaction.response.send_message(f"❌ {usuario.mention} no tiene advertencias.", ephemeral=True)
        return
    
    count = len(warnings_data[user_id])
    warnings_data[user_id] = []
    save_warnings(warnings_data)
    
    await interaction.response.send_message(f"✅ Se eliminaron {count} advertencia(s) de {usuario.mention}")

# Comando /lock_channel
@bot.tree.command(name="lock_channel", description="Bloquea el canal actual")
@app_commands.describe(razon="Razón del bloqueo")
@is_moderator()
async def lock_channel(interaction: discord.Interaction, razon: str = "No especificada"):
    try:
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(f"🔒 Canal bloqueado.\n📝 Razón: {razon}")
    except:
        await interaction.response.send_message("❌ No se pudo bloquear el canal.", ephemeral=True)

# Comando /unlock_channel
@bot.tree.command(name="unlock_channel", description="Desbloquea el canal actual")
@is_moderator()
async def unlock_channel(interaction: discord.Interaction):
    try:
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = None
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔓 Canal desbloqueado.")
    except:
        await interaction.response.send_message("❌ No se pudo desbloquear el canal.", ephemeral=True)

# Comando /slowmode
@bot.tree.command(name="slowmode", description="Establece el modo lento en el canal")
@app_commands.describe(tiempo="Tiempo en segundos (0 para desactivar)")
@is_moderator()
async def slowmode(interaction: discord.Interaction, tiempo: int):
    if tiempo < 0 or tiempo > 21600:
        await interaction.response.send_message("❌ El tiempo debe estar entre 0 y 21600 segundos (6 horas).", ephemeral=True)
        return
    
    try:
        await interaction.channel.edit(slowmode_delay=tiempo)
        if tiempo == 0:
            await interaction.response.send_message("✅ Modo lento desactivado.")
        else:
            await interaction.response.send_message(f"✅ Modo lento establecido a {tiempo} segundo(s).")
    except:
        await interaction.response.send_message("❌ No se pudo establecer el modo lento.", ephemeral=True)

# Comando /help
@bot.tree.command(name="help", description="Muestra todos los comandos disponibles")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛠️ Comandos de Moderación",
        description="Lista de todos los comandos disponibles",
        color=discord.Color.blue()
    )
    
    comandos = {
        "clear": "Elimina mensajes (1-100)",
        "ban": "Banea a un usuario",
        "unban": "Desbanea a un usuario",
        "kick": "Expulsa a un usuario",
        "timeout": "Aplica timeout a un usuario",
        "mute": "Alias de timeout",
        "warn": "Advierte a un usuario",
        "warnings": "Ver advertencias de un usuario",
        "clear_warn": "Elimina una advertencia específica",
        "clear_warns": "Elimina todas las advertencias",
        "lock_channel": "Bloquea el canal",
        "unlock_channel": "Desbloquea el canal",
        "slowmode": "Establece modo lento",
        "help": "Muestra este mensaje"
    }
    
    for comando, descripcion in comandos.items():
        embed.add_field(name=f"/{comando}", value=descripcion, inline=False)
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="mute", description="Aplica mute a un usuario (usa timeout)")
@app_commands.describe(usuario="Usuario a mutear", tiempo="Tiempo (ej: 1m, 1h, 1d)")
@is_moderator()
async def mute(interaction: discord.Interaction, usuario: discord.Member, tiempo: str):
    # Reutilizar la lógica de timeout
    await timeout(interaction, usuario, tiempo)

# Ejecutar el bot
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    bot.run(TOKEN)


