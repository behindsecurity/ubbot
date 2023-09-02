import discord, os, asyncio, time, datetime, random, requests
from discord import app_commands, utils
from discord.ext import commands, tasks
from dotenv import load_dotenv
from utilidades import json_util, verificacao

global guild_id, footer_text
guild_id = 1137749496294543440 # ID do grupo da UB
footer_text = "© Estudantes da Unibra. Nenhuma relação oficial com a instituição."
load_dotenv()



###						Classes relacionadas ao sistema de ticket						####


class main(discord.ui.View):
	def __init__(self) -> None:
		super().__init__(timeout = None)
	
	@discord.ui.button(label = "Fechar", style = discord.ButtonStyle.red, custom_id = "close", emoji="🔒")
	async def close(self, interaction, button):
		"""Botão de fechar o ticket, que manda o embed e puxa o botão de confirmação (view = confirm())"""
		embed = discord.Embed(title = "Tem certeza que você deseja fechar o ticket?", description="Essa decisão é definitiva, o ticket não poderá mais ser aberto!", color = discord.Colour.blurple())
		embed.set_footer(text=footer_text)
		await interaction.response.send_message(embed = embed, view = confirm(), ephemeral = True)

	@discord.ui.button(label = "Transcrição", style = discord.ButtonStyle.blurple, custom_id = "transcript", emoji="📄")
	async def transcript(self, interaction, button):
		await interaction.response.defer()
		if os.path.exists(f"{interaction.channel.id}.md"):
			return await interaction.followup.send(f"Uma transcrição do ticket já está sendo gerada!", ephemeral = True)
		with open(f"{interaction.channel.id}.md", 'a', encoding="utf-8") as f:
			f.write(f"# Transcrição de {interaction.channel.name}:\n\n")
			async for message in interaction.channel.history(limit = None, oldest_first = True):
				created = datetime.datetime.strftime(message.created_at, "%m/%d/%Y às %H:%M:%S")
				if message.edited_at:
					edited = datetime.datetime.strftime(message.edited_at, "%m/%d/%Y ás %H:%M:%S")
					f.write(f"{message.author} em {created}: {message.clean_content} (Editado em {edited})\n")
				else:
					f.write(f"{message.author} em {created}: {message.clean_content}\n")
			gerado_em = datetime.datetime.now().strftime("%m/%d/%Y às %H:%M:%S")
			f.write(f"\n*Gerado em {gerado_em} por {client.user}*\n*Formatação de data: MM/DD/AA*\n*Fuso horário: UTC*")
		with open(f"{interaction.channel.id}.md", 'rb') as f:
			await interaction.followup.send(file = discord.File(f, f"{interaction.channel.name}.md"))
		await asyncio.sleep(2)
		os.remove(f"{interaction.channel.id}.md")

class ticket_launcher(discord.ui.View):
	"""View que fica permanente no canal de suporte"""
	def __init__(self) -> None:
		super().__init__(timeout = None)
		self.cooldown = commands.CooldownMapping.from_cooldown(1, 600, commands.BucketType.member)
	
	@discord.ui.button(label = "Abrir um ticket", style = discord.ButtonStyle.blurple, custom_id = "ticket_button", emoji="📥")
	async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
		interaction.message.author = interaction.user
		retry = self.cooldown.get_bucket(interaction.message).update_rate_limit()
		if retry: return await interaction.response.send_message(f"Devagar! Tente novamente em {round(retry, 1)} segundos!", ephemeral = True)
		ticket = utils.get(interaction.guild.text_channels, name = f"ticket-{interaction.user.name.lower().replace(' ', '-')}-{interaction.user.discriminator}")
		if ticket is not None: await interaction.response.send_message(f"Você já tem um ticket aberto em {ticket.mention}!", ephemeral = True)
		else:
			if type(client.ticket_mod) is not discord.Role: 
				client.ticket_mod = interaction.guild.get_role(1147549138704138363) # ID do cargo de suporte do grupo
			overwrites = { # Configurando as permisses do canal
				interaction.guild.default_role: discord.PermissionOverwrite(view_channel = False),
				interaction.user: discord.PermissionOverwrite(view_channel = True, read_message_history = True, send_messages = True, attach_files = True, embed_links = True),
				interaction.guild.me: discord.PermissionOverwrite(view_channel = True, send_messages = True, read_message_history = True), 
				client.ticket_mod: discord.PermissionOverwrite(view_channel = True, read_message_history = True, send_messages = True, attach_files = True, embed_links = True),
			}
			categoria_de_tickets = utils.get(interaction.guild.categories, name="「 📩 」Tickets") # Categoria que os staffs possuem acesso para visualizar os tickets
			try: channel = await interaction.guild.create_text_channel(name = f"ticket-{interaction.user.name}-{interaction.user.discriminator}", overwrites = overwrites, reason = f"Ticket para {interaction.user}", category = categoria_de_tickets)
			except: return await interaction.response.send_message("Não houve êxito em criar o ticket! Garanta que eu possua a permissão `manage_channels`.", ephemeral = True)
			ticket_embed = discord.Embed(title="📥 Ticket", description=f"Olá, {interaction.user.display_name}! A staff entrará em contato em breve.", color=discord.Colour.green())
			ticket_embed.set_footer(text=footer_text)
			await channel.send(f"||{client.ticket_mod.mention}||\n\n{interaction.user.mention}", view = main(), embed=ticket_embed)
			await interaction.response.send_message(f"Eu abri um ticket para você em {channel.mention}!", ephemeral = True)

	@discord.ui.button(label="Dúvida", style=discord.ButtonStyle.grey, custom_id="doubt_button", emoji="❓")
	async def duvida(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message("Você pode retirar <#1147542904701722664> no canal específico para isso! Não há necessidade de abrir um ticket.", ephemeral = True)

	@discord.ui.button(label="Denúncia", style=discord.ButtonStyle.red, custom_id="report_button", emoji="🚨")
	async def denuncia(self, interaction: discord.Interaction, button: discord.ui.Button):
		interaction.message.author = interaction.user
		retry = self.cooldown.get_bucket(interaction.message).update_rate_limit()
		if retry: return await interaction.response.send_message(f"Devagar! Tente novamente em {round(retry, 1)} segundos!", ephemeral = True)
		await interaction.response.defer(ephemeral=True)
		sequencia_numerica = ""
		for _ in range(5):
			sequencia_numerica += str(random.randint(0,9))
		categoria_de_tickets = utils.get(interaction.guild.categories, name="「 📩 」Tickets")
		everyone = utils.get(ubguild.roles, name="@everyone")
		staffs = utils.get(ubguild.roles, name="⚖️ Moderação")
		canal = await interaction.guild.create_text_channel(name=f"denuncia-{sequencia_numerica}", category=categoria_de_tickets)
		await canal.set_permissions(everyone, view_channel=False)
		await canal.set_permissions(interaction.user, view_channel=True)
		await asyncio.sleep(1.5)
		await canal.set_permissions(staffs, view_channel=True)
		embed = discord.Embed(title="🚨 Denúncia", description=f"Olá {interaction.user.display_name}. Não se preocupe, entraremos em contato por aqui em breve.", color=discord.Colour.red())
		embed.add_field(name="❓ Informações", value="1. A denúncia precisa de provas, portanto, especifique testemunhas, imagens e/ou vídeos.\n2. Caso seja descoberto que a denúncia é falsa/forjada, o usuário que a fez poderá ser banido temporariamente ou permanentemente, dependendo do grau da situação.\n3. A criação de denúncias sem provas acarreta em um aviso (warn) perante a organização do grupo.\n4. A decisão final sobre a denúncia é de responsabilidade somente da equipe de staffs e organizadores.")
		embed.set_footer(text=f"{footer_text} // ID da denúncia: #{sequencia_numerica}")
		await canal.send(f"||{staffs.mention}||\n\n||{interaction.user.mention}||", embed=embed, view=main())
		await interaction.followup.send(f"Criei um canal de denúncia para você em: {canal.mention}.", ephemeral=True)

class confirm(discord.ui.View):
	def __init__(self) -> None:
		super().__init__(timeout = 15)
	
	@discord.ui.button(label = "Confirmar", style = discord.ButtonStyle.red, custom_id = "confirm")
	async def confirm_button(self, interaction, button):
		if "ticket-" in interaction.channel.name or "denuncia-" in interaction.channel.name:
			try:
				await interaction.channel.delete()
			except:
				await interaction.response.send_message("Não houve êxito em apagar o canal! Garanta que eu tenho a permissão `manage_channels`!", ephemeral = True)



###						Modal de Verificação						####

class modal_de_verificacao(discord.ui.Modal, title="Verificação"):
	matricula = discord.ui.TextInput(label="Qual é o seu número de matrícula?", style=discord.TextStyle.short, placeholder="2023...", required=True, max_length=10, min_length=10)
	data_nascimento = discord.ui.TextInput(label="Qual a sua data de nascimento?", style=discord.TextStyle.short, placeholder="31/08/2003", required=True, max_length=10, min_length=10)
	
	async def on_submit(self, interaction: discord.Interaction):
		try:
			matricula = int(self.matricula.value) # Sanitizando
			data_nascimento = int(self.data_nascimento.value.replace("/", "")) # Sanitizando
		except Exception as err:
			print(err)
			return await interaction.response.send_message("Houve um erro ao processar as suas informações. Verifique se está correto, e tente novamente.", ephemeral=True, delete_after=10)
		user_id = str(interaction.user.id)
		registro = json_util.read_json("registro")
		for user in registro: # Verificando se algum usuário já está associado ao mesmo número de matrícula
			if registro[user]["matricula"] == matricula:
				return await interaction.response.send_message("Este número de matrícula já está associado a um usuário. Entre em contato com a <@&1146813158992924832> do grupo caso você ache que seja um erro.", ephemeral=True, delete_after=10)
		await interaction.response.defer(ephemeral=True)
		verificado = verificacao.verificar(matricula, data_nascimento, user_id)
		if type(verificado) == str:
			return await interaction.followup.send(verificado, ephemeral=True)
		else:
			await asyncio.sleep(1)
			await interaction.user.add_roles(utils.get(ubguild.roles, id=verificado[0])) # Ficou feio, mas é pra evitar levar flag na API do Discord (pelo menos eu acho que ajuda!!!). Basicamente, pega a variavel 'verificado' (que é uma lista de inteiros, o index 0 é o id do cargo da área, e o index 1 é o id do cargo do curso, usa a biblioteca de utilidades do discord pra pegar o cargo na guilda e já seta no usuário)
			await interaction.user.add_roles(utils.get(ubguild.roles, id=verificado[1]))
			await asyncio.sleep(1)
			await interaction.user.add_roles(cargo_de_matriculado)
			embed = discord.Embed(title=f"Sucesso!", description="Você foi verificado(a) no grupo com sucesso.", color=discord.Colour.green())
			embed.add_field(name="Área", value=f"<@&{verificado[0]}>", inline=True)
			embed.add_field(name="Curso", value=f"<@&{verificado[1]}>", inline=True)
			embed.set_footer(text=footer_text)

			return await interaction.followup.send(interaction.user.mention, embed=embed, ephemeral=True)



###						Botões da parte de verificação						####

class botoes_de_verificacao(discord.ui.View):
	def __init__(self) -> None:
		super().__init__(timeout = None)
		self.cooldown = commands.CooldownMapping.from_cooldown(1, 15, commands.BucketType.member)
	
	@discord.ui.button(label = "Verifique-se", style = discord.ButtonStyle.blurple, custom_id = "botao_verificacao", emoji="✅")
	async def verifique_se(self, interaction: discord.Interaction, button: discord.ui.Button):
		interaction.message.author = interaction.user
		retry = self.cooldown.get_bucket(interaction.message).update_rate_limit()
		if retry: return await interaction.response.send_message(f"Devagar! Tente novamente em {round(retry, 1)} segundos!", ephemeral = True)
		if cargo_de_matriculado in interaction.user.roles:
			return await interaction.response.send_message("Você já está verificado(a).", ephemeral=True, delete_after=10)
		else:
			return await interaction.response.send_modal(modal_de_verificacao())
	
	@discord.ui.button(label="Privacidade", style=discord.ButtonStyle.green, custom_id="botao_privacidade", emoji="👀")
	async def privacidade(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message("Nós valorizamos profundamente a privacidade e o respeito mútuo entre os membros do grupo. Veja mais informações sobre privacidade no grupo em <#1146885215344676944>", ephemeral = True)

	@discord.ui.button(label="Ajuda", style=discord.ButtonStyle.grey, custom_id="botao_ajuda", emoji="❓")
	async def ajuda(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message("Precisa de ajuda no processo? Entre em contato diretamente com alguém da <@&1146813158992924832>.", ephemeral = True)



###						Cliente						####

class aclient(discord.Client):
	def __init__(self):
		intents = discord.Intents.default()
		intents.message_content = True
		intents.members = True
		super().__init__(intents = intents)
		self.synced = False # Usamos isso para o bot não sincronizar os comandos mais de uma vez
		self.added = False
		self.ticket_mod = 1147549138704138363 # ID do cargo de suporte do grupo (que é o moderador de tickets)

	async def on_ready(self):
		await self.wait_until_ready()
		if not self.synced: # Checa se os "slash commands" foram sincronizados
			await tree.sync(guild = discord.Object(id = guild_id)) # Específico do grupo: deixar vazio caso seja global (registro global pode levar de 1-24 horas)
			await wait_ready.start() # Tarefa que inicializa algumas variáveis e muda presença do bot
			self.synced = True
		if not self.added:
			# Adiciona a view permanente, que fica mesmo quando o bot reinicia
			self.add_view(ticket_launcher())
			self.add_view(botoes_de_verificacao())
			self.add_view(main())
			self.added = True
		print(f"[+] Tudo pronto, login efetuado como {self.user}.")

client = aclient()
tree = app_commands.CommandTree(client)



### 					Tarefas 					####

@tasks.loop(count=1)
async def wait_ready():
	global ubguild, cargo_de_matriculado
	bot_start_time = time.time() # Fins de debug
	ubguild = await client.fetch_guild(guild_id) # Objeto da 'guilda' para poder trabalhar com cargos, canais e categorias do grupo
	#punishments_channel = client.get_channel(987721757320441916) #change
	cargo_de_matriculado = utils.get(ubguild.roles, id=1146881140603494512)
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="/ajuda")) # Mudando a atividade do bot no discord



###						Comandos do sistema de verificação						#####

@tree.command(guild = discord.Object(id=guild_id), name = 'ativar_verificacao', description='Efetiva o sistema de verificação') #guild specific slash command
@app_commands.default_permissions(administrator = True)
@app_commands.checks.cooldown(3, 60, key = lambda i: (i.guild_id))
async def ativar_verificacao(interaction: discord.Interaction):
	embed = discord.Embed(title="👋 Olá!", description="Seja bem vindo(a) ao grupo de estudantes da Unibra!", color=discord.Colour.blue())
	embed.add_field(name="Informações", value="Para garantir uma experiência segura e produtiva para todos, somente pessoas matriculadas na Unibra podem participar do grupo.\nClique nos botões abaixo para saber mais.")
	embed.set_footer(text=footer_text)
	await interaction.channel.send(embed = embed, view = botoes_de_verificacao())
	await interaction.response.send_message("Sistema de verificação foi ativo!", ephemeral = True)



###						Comandos do sistema de ticket 					####

@tree.command(guild = discord.Object(id=guild_id), name = 'ticket', description='Efetiva o sistema de tickets')
@app_commands.default_permissions(manage_guild = True)
@app_commands.checks.cooldown(3, 60, key = lambda i: (i.guild_id))
@app_commands.checks.bot_has_permissions(manage_channels = True)
async def ticketing(interaction: discord.Interaction):
	embed = discord.Embed(title="📩 Suporte", description="Precisa de ajuda? Abra um ticket ou faça uma denúncia.", color=discord.Colour.blue())
	embed.add_field(name="Informações", value="Você tem duas opções para obter ajuda ou relatar problemas:\n1. **Abrir um Ticket de Suporte:** Clique no botão \"Abrir Ticket\" abaixo para criar um ticket de suporte privado. Um membro da equipe irá atendê-lo assim que possível. Certifique-se de fornecer informações detalhadas sobre o seu problema ou pergunta para uma assistência mais eficaz.\n\n2. **Fazer uma Denúncia:** Se você precisa relatar um comportamento inadequado, clique no botão \"Denúncia\". Isso abrirá um canal privado com a equipe de moderação, garantindo que sua denúncia seja tratada com alta prioridade e discrição.\n\nPor favor, escolha a opção que melhor se adequa à sua situação. Estamos aqui para ajudar e garantir que nosso grupo seja um lugar seguro e acolhedor para todos os membros.")
	embed.set_footer(text=footer_text)
	await interaction.channel.send(embed = embed, view = ticket_launcher())
	await interaction.response.send_message("Sistema de ticket ativado!", ephemeral = True)

@tree.command(guild = discord.Object(id=guild_id), name = 'fechar_ticket', description='Fecha o ticket')
@app_commands.checks.has_role("👤 Members")
@app_commands.checks.bot_has_permissions(manage_channels = True)
async def close(interaction: discord.Interaction):
	if "ticket-" in interaction.channel.name or "denuncia-" in interaction.channel.name:
		embed = discord.Embed(title = "Tem certeza que você quer fechar o ticket?", color = discord.Colour.blurple())
		await interaction.response.send_message(embed = embed, view = confirm(), ephemeral = True)
	else: await interaction.response.send_message("Isso não é um ticket!", ephemeral = True)

@tree.command(guild = discord.Object(id=guild_id), name = 'adicionar_ao_ticket', description='Adiciona um usuário no ticket')
@app_commands.describe(user = "O usuário que você quer adicionar ao ticket")
@app_commands.default_permissions(manage_channels = True)
@app_commands.checks.cooldown(3, 20, key = lambda i: (i.guild_id, i.user.id))
@app_commands.checks.bot_has_permissions(manage_channels = True)
async def add(interaction: discord.Interaction, user: discord.Member):
	if "ticket-" in interaction.channel.name or "denuncia-" in interaction.channel.name:
		await interaction.channel.set_permissions(user, view_channel = True, send_messages = True, attach_files = True, embed_links = True)
		await interaction.response.send_message(f"{user.mention} foi adicionado(a) no ticket por {interaction.user.mention}!")
	else: await interaction.response.send_message("Isso não é um ticket!", ephemeral = True)


@tree.command(guild = discord.Object(id=guild_id), name = 'remover_do_ticket', description='Remove um usuário do ticket')
@app_commands.describe(user = "O usuário que você quer remover do ticket")
@app_commands.default_permissions(manage_channels = True)
@app_commands.checks.cooldown(3, 20, key = lambda i: (i.guild_id, i.user.id))
@app_commands.checks.bot_has_permissions(manage_channels = True)
async def remove(interaction: discord.Interaction, user: discord.Member):
	if "ticket-" in interaction.channel.name or "denuncia-" in interaction.channel.name:
		if type(client.ticket_mod) is not discord.Role: client.ticket_mod = interaction.guild.get_role(983535584465268736)
		if client.ticket_mod not in interaction.user.roles:
			return await interaction.response.send_message("Você não tem autorização para fazer isso!", ephemeral = True)
		if client.ticket_mod not in user.roles:
			await interaction.channel.set_permissions(user, overwrite = None)
			await interaction.response.send_message(f"{user.mention} foi removido(a) do ticket por {interaction.user.mention}!", ephemeral = True)
		else: await interaction.response.send_message(f"{user.mention} é um staff!", ephemeral = True)
	else: await interaction.response.send_message("Isso não é um ticket!", ephemeral = True)

@tree.command(guild = discord.Object(id=guild_id), name = 'transcrever_ticket', description='Gera uma transcrição do ticket') #guild specific slash command
@app_commands.default_permissions(manage_messages = True)
async def transcript(interaction: discord.Interaction):
	if "ticket-" in interaction.channel.name or "denuncia-" in interaction.channel.name:
		await interaction.response.defer()
		if os.path.exists(f"{interaction.channel.id}.md"):
			return await interaction.followup.send(f"Uma transcrição já está sendo gerada!", ephemeral = True)
		with open(f"{interaction.channel.id}.md", 'a') as f:
			f.write(f"# Transcrição de {interaction.channel.name}:\n\n")
			async for message in interaction.channel.history(limit = None, oldest_first = True):
				created = datetime.datetime.strftime(message.created_at, "%m/%d/%Y ás %H:%M:%S")
				if message.edited_at:
					edited = datetime.datetime.strftime(message.edited_at, "%m/%d/%Y ás %H:%M:%S")
					f.write(f"{message.author} em {created}: {message.clean_content} (Editado em {edited})\n")
				else:
					f.write(f"{message.author} em {created}: {message.clean_content}\n")
			generated = datetime.datetime.now().strftime("%m/%d/%Y ás %H:%M:%S")
			f.write(f"\n*Gerado em {generated} por {client.user}*\n*Formatação de data: MM/DD/YY*\n*Fuso horário: UTC*")
		with open(f"{interaction.channel.id}.md", 'rb') as f:
			await interaction.followup.send(file = discord.File(f, f"{interaction.channel.name}.md"))
		os.remove(f"{interaction.channel.id}.md")
	else: await interaction.response.send_message("Isso não é um ticket!", ephemeral = True)

@tree.context_menu(name = "Abrir um ticket", guild = discord.Object(id=guild_id))
@app_commands.default_permissions(manage_guild = True)
@app_commands.checks.cooldown(3, 20, key = lambda i: (i.guild_id, i.user.id))
@app_commands.checks.bot_has_permissions(manage_channels = True)
async def open_ticket_context_menu(interaction: discord.Interaction, user: discord.Member):
	await interaction.response.defer(ephemeral = True)
	ticket = utils.get(interaction.guild.text_channels, name = f"ticket-{user.name.lower().replace(' ', '-')}-{user.discriminator}")
	if ticket is not None: await interaction.followup.send(f"{user.mention} já tem um ticket aberto em {ticket.mention}!", ephemeral = True)
	else:
		if type(client.ticket_mod) is not discord.Role:
			client.ticket_mod = interaction.guild.get_role(987526928980402176) #change
		overwrites = {
			interaction.guild.default_role: discord.PermissionOverwrite(view_channel = False),
			user: discord.PermissionOverwrite(view_channel = True, read_message_history = True, send_messages = True, attach_files = True, embed_links = True),
			interaction.guild.me: discord.PermissionOverwrite(view_channel = True, send_messages = True, read_message_history = True),
			client.ticket_mod: discord.PermissionOverwrite(view_channel = True, read_message_history = True, send_messages = True, attach_files = True, embed_links = True),
		}
		ticket_category = utils.get(interaction.guild.categories, name="「 📩 」Tickets")
		try: channel = await interaction.guild.create_text_channel(name = f"ticket-{user.name}-{user.discriminator}", overwrites = overwrites, reason = f"Ticket para {user}, gerado por {interaction.user}", category=ticket_category)
		except: return await interaction.followup.send("Não houve êxito em criar o ticket! Garanta que possuo a permissão `manage_channels`!", ephemeral = True)
		await channel.send(f"{interaction.user.mention} criou um ticket para {user.mention}!", view = main())
		await interaction.followup.send(f"Eu abri um ticket para {user.mention} em {channel.mention}!", ephemeral = True)



###						Rodando					####

try:
	client.run(os.environ["TOKEN"])
except:
	r = requests.head(url="https://discord.com/api/v1")
	retry_after = int(r.headers['Retry-After'])
	print(f"[-] Bloqueado pela API do Discord.\n\nRate limit: {round(retry_after / 60)} minutos restantes.")