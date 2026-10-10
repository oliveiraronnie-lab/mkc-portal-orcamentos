# MKC Engenharia — Portal Simples de Orçamentos

Portal Flask responsivo para solicitar orçamento de regularização e alvará do Corpo de Bombeiros de Mato Grosso.

## Rodar localmente (Windows)

1. Instale Python 3.11 ou superior.
2. Abra o terminal nesta pasta.
3. Execute `py -m venv .venv`.
4. Execute `.venv\Scripts\activate`.
5. Execute `pip install -r requirements.txt`.
6. Configure variáveis: `set SECRET_KEY=uma-chave-aleatoria-longa` e `set ADMIN_PASSWORD=uma-senha-forte` (no Prompt de Comando do Windows).
7. Execute `python app.py`.
8. Acesse `http://localhost:5000` e a área MKC em `/admin`.

## Publicação no Render

1. Crie um repositório privado no GitHub e envie os arquivos (não envie `.env`, `.db` ou senhas).
2. No Render, crie um **Web Service** conectado ao repositório ou use o arquivo `render.yaml` (Blueprint).
3. Build Command: `pip install -r requirements.txt`.
4. Start Command: `gunicorn app:app`.
5. Configure `SECRET_KEY` (valor aleatório longo) e `ADMIN_PASSWORD` (senha forte).
6. Configure, opcionalmente, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `NOTIFY_EMAIL` para notificações de novas solicitações por e-mail. Utilize senha de aplicativo ou credencial SMTP apropriada.

**IMPORTANTE SOBRE PERSISTÊNCIA:** o SQLite local é indicado para desenvolvimento e testes. No Render, sistemas de arquivos efêmeros podem apagar os dados a cada deploy/reinício. Para operar em produção, configure `DATABASE_PATH` apontando para um disco persistente em plano compatível, ou migre para PostgreSQL (não incluído nesta versão). O plano gratuito do Render não oferece disco persistente. Não receba solicitações reais antes de garantir armazenamento durável e backup.

## Segurança e operação

- Defina `ADMIN_PASSWORD` antes de publicar. Sem ela o login administrativo permanece bloqueado.
- O formulário exige consentimento de contato, usa token CSRF e validações básicas; não envia anexos.
- O administrador visualiza as solicitações, atualiza situação e exporta CSV.
- Configure aviso de privacidade completo, política de retenção, contatos de titular e controles adicionais antes do uso comercial em produção (LGPD).
- Use HTTPS (fornecido pelo Render) e senhas fortes; limite acesso administrativo conforme necessidade.
- O e-mail é opcional: se SMTP não estiver configurado, os pedidos são armazenados mas nenhum aviso será enviado.

## Atualização de campos
Máscaras de CPF/CNPJ, telefone, área m² e letras maiúsculas. CPF/CNPJ validados no navegador e servidor. Contato: (65) 99695-2144.

Envie os arquivos da pasta `mkc-portal-simples` para a raiz do repositório GitHub (ou defina Root Directory no Render como `mkc-portal-simples`). Não envie o ZIP diretamente para o repositório.
