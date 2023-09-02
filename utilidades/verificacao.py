from . import json_util
import requests, json

def salvar_dados(matricula, nome, discord_id):
	"""Recebe número de matrícula, nome e id do discord, e salva para o arquivo de registro. Não retorna nada."""
	registro = json_util.read_json("registro")
	registro[discord_id] = {}
	registro[discord_id]["matricula"] = matricula
	registro[discord_id]["nome"] = nome
	json_util.write_json(registro, "registro") # Salvando as informações


def verificar(matricula, data_nascimento, discord_id):
	"""Recebe número de matrícula, a data de nascimento, e o id do usuário no discord. Então, faz login no portal do totvs e verifica se o usuário está matriculado. Caso tudo ocorra bem, retorna o ID do cargo do curso e da área em forma de lista (ex: [1146561893893427310, 1146558902729703464]) para que o usuário possa receber automaticamente no Discord. Caso não, retorna uma mensagem de erro (string)."""
	url = "https://unibra.rm.cloudtotvs.com.br/Corpore.Net//Source/EDU-EDUCACIONAL/Public/EduPortalAlunoLogin.aspx?AutoLoginType=ExternalLogin&undefined" # Url para fazer login no painel
	headers = {
		"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0",
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
		"Content-Type": "application/x-www-form-urlencoded",
		"Referer": "https://unibra.rm.cloudtotvs.com.br/FrameHTML/web/app/edu/PortalEducacional/login/",
		"Host": "unibra.rm.cloudtotvs.com.br"
	} # Headers para emular navegador
	cookies = {
		"EduContextoAlunoResponsavelAPI": ""
	} # Cookie padrão do sistema
	data = {
		"User": matricula,
		"Pass": data_nascimento,
		"Alias": "CorporeRM"
	} # Dados fornecidos pelo usuário 

	login_request = requests.post(url, headers=headers, data=data, cookies=cookies, allow_redirects=False)
	if login_request.status_code != 302: # Caso seja não 302 (redirecionamento), significa que os dados estão incorretos.
		return "Houve um erro na verificação. Verifique os dados fornecidos e tente novamente. Caso seja recorrente, entre em contato com alguém da <@&1146813158992924832>"

	try:
		auth_cookies = dict(login_request.cookies) # Armazena os cookies de autenticação
		key = login_request.headers["Location"].split("?key=")[1] # Key fornecida para o usuário (parte de como o totvs funciona)
		get_info_url = f"https://unibra.rm.cloudtotvs.com.br/FrameHTML/RM/API/user/AutoLoginPortal?key={key}"
		get_info_request = requests.get(get_info_url, cookies=auth_cookies)
		info_cookies = dict(get_info_request.cookies)
		info_cookies.update(auth_cookies)
		
		contexto_url = "https://unibra.rm.cloudtotvs.com.br/FrameHTML/RM/API/TOTVSEducacional/Contexto"
		contexto_request = requests.get(contexto_url, cookies=info_cookies)
		contexto_formatado = json.loads(contexto_request.content)

		curso = contexto_formatado["data"][0]["NOMECURSO"]
		nome = contexto_formatado["data"][0]["NOMEALUNO"]
		tipo_do_curso = contexto_formatado["data"][0]["NOMETIPOCURSO"]

		if contexto_formatado["data"][0]["SITMATHABILITACAO"] != "Matriculado":
			return "Parece que você atualmente não está matriculado(a). O grupo é direcionado para aqueles que estão matriculados, portanto, converse com alguém da <@&1146813158992924832> caso queira fazer parte do grupo. Podemos abrir excessões para ex-alunos."
	except Exception as err:
		print(err)
		return "Houve um erro ao executar a verificação. Tente novamente mais tarde, ou entre em contato com alguém da <@&1146813158992924832>."
	salvar_dados(matricula, nome, discord_id)
	return curso_para_cargo(curso)

def curso_para_cargo(curso_do_usuario):
	"""Recebe o nome do curso do usuário e devolve os ids relacionados no grupo do Discord, em forma de lista de inteiros."""
	mapeamento_de_cursos = {
		"1146557615598485607": { # A chave do dicionário é o id do cargo @Saúde no discord
			"Biomedicina": "1146558955577946173", # Valores são ids de cargos, relacionado ao curso listado na sua chave
			"Biológicas": "1146559070275375215",
			"Educação Física": "1146559135178035383",
			"Enfermagem": "1146559188663812177",
			"Estética": "1146559505828691998",
			"Farmácia": "1146559604650676379",
			"Fisioterapia": "1146559694517829713",
			"Veterinária": "1146559875757899806",
			"Nutrição": "1146559931768651918",
			"Odontologia": "1146559993605271572",
			"Psicologia": "1146560053306998864"
		},
		"1146558902729703464": { # Exatas
			"Análise e Desenvolvimento": "1146561893893427310",
			"Arquitetura": "1146561984641388634",
			"Ciências Contábeis": "1146562178539860009",
			"Engenharia Civil": "1146562246512746648",
			"Engenharia de Produção": "1146562499311841351",
			"Redes de Computadores": "1146562590080761947"
		},
		"1146558670637908058": { # Humanas
			"Administração": "1146560732910071878",
			"Artes Cênicas": "1146560836530343937",
			"Direito": "1146560901789528186",
			"Gastronomia": "1146560969242320966",
			"História": "1146561090336063538",
			"Logística": "1146561129271787650",
			"Marketing": "1146561210297368616",
			"Pedagogia": "1146561264819118132",
			"Processos Gerenciais": "1146561439411216566",
			"Produção Publicitária": "1146561533602705408",
			"Recursos Humanos": "1146561614057832612"
		}
	}
	for id_da_area in mapeamento_de_cursos.keys():
		for nome_do_curso, id_do_curso in mapeamento_de_cursos[id_da_area].items():
			if nome_do_curso.lower() in curso_do_usuario.lower(): # Compara o nome do curso com o nome do curso do usuário
				return [int(id_da_area), int(id_do_curso)] # Retorna o id do cargo da área do usuário e o id do curso
	return None # Caso não retorne acima, então retorna None.