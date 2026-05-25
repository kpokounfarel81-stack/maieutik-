import os
from flask import Flask, request, redirect, url_for, session, flash, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'une-cle-tres-secrete')

# Configuration Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase = None
if url and key:
    try:
        supabase: Client = create_client(url, key)
    except Exception as e:
        print(f"Erreur d'initialisation Supabase : {e}")

def get_flash_messages():
    """Récupère les messages flash pour les afficher dans le HTML simple."""
    # Flask stocke les messages flash dans la session sous '_flashes'
    messages = session.get('_flashes', [])
    if not messages:
        return ""
    # On vide les messages après lecture
    session.pop('_flashes', None)
    return "".join([f'<div style="padding:10px;margin:10px 0;background:#ffeeee;border:1px solid red;color:red">{m[1]}</div>' for m in messages])

@app.route('/')
def index():
    if 'user_id' in session:
        return f"""
        <h1>Tableau de bord</h1>
        <div style="margin: 10px 0; padding: 10px; border-radius: 5px; background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0;">
        {get_flash_messages()}
        </div>
        <p>Connecté en tant que : <strong>{session.get('username')}</strong></p>
        <a href='/logout'>Se déconnecter</a>
        """
    return """
    <h1>Bienvenue</h1>
    <p style="color:green">Application configurée avec succès.</p>
    <p><a href='/login'>Connexion</a> ou <a href='/register'>Inscription</a></p>
    """

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not supabase:
            flash("Erreur : Supabase n'est pas configuré.", "error")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        try:
            # Vérifier si l'utilisateur existe déjà pour éviter une erreur brute
            user_check = supabase.table("profiles").select("id").or_(f"username.eq.\"{username}\",email.eq.\"{email}\"").execute()
            if user_check.data:
                flash("Ce nom d'utilisateur est déjà utilisé.", "error")
                return redirect(url_for('register'))

            supabase.table("profiles").insert({
                "username": username,
                "email": email,
                "password": hashed_pw
            }).execute()
            flash("Compte créé avec succès ! Connectez-vous.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Erreur lors de l'inscription : {str(e)}", "error")
            return redirect(url_for('register'))
            
    return f'''
    <h1>Inscription</h1>
    {get_flash_messages()}
    <form method="post">
        Nom d'utilisateur: <input name="username" required><br>
        Email: <input name="email" type="email" required><br>
        Mot de passe: <input type="password" name="password" required><br>
        <button type="submit">S'inscrire</button>
    </form>
    <p><a href="/login">Déjà un compte ? Connectez-vous</a></p>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not supabase:
            flash("Erreur : Supabase n'est pas configuré.", "error")
            return redirect(url_for('login'))

        response = supabase.table("profiles").select("*").eq("username", username).execute()
        user_data = response.data

        if user_data and check_password_hash(user_data[0]['password'], password):
            session.clear()
            session['user_id'] = user_data[0]['id']
            session['username'] = user_data[0]['username']
            return redirect(url_for('index'))
        
        flash("Nom d'utilisateur ou mot de passe incorrect.", "error")
        return redirect(url_for('login'))

    return f'''
    <h1>Connexion</h1>
    {get_flash_messages()}
    <form method="post">
        Nom d'utilisateur: <input name="username" required><br>
        Mot de passe: <input type="password" name="password" required><br>
        <button type="submit">Se connecter</button>
    </form>
    <p><a href="/register">Pas de compte ? Inscrivez-vous</a></p>
    '''

@app.route('/logout')
def logout():
    session.clear()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)