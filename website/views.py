from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .models import User, Team, Player
from . import db
from .auth import is_email
from .vars import COUNTRIES, NAMES
import random

views = Blueprint('views', __name__)


def generate_players(team_id: int):
    player_pos = [
        'goalkeeper', 'goalkeeper', 'goalkeeper', 'defender', 'defender',
        'defender', 'defender', 'defender', 'defender', 'midfielder',
        'midfielder', 'midfielder', 'midfielder', 'midfielder', 'midfielder',
        'attacker', 'attacker', 'attacker', 'attacker', 'attacker'
    ]
    for i in range(20):
        new_player = Player(
            first_name=random.choice(NAMES),
            last_name=random.choice(NAMES),
            country=random.choice(COUNTRIES),
            age=random.randint(18, 40),
            position=player_pos[i],
            market_value=1000000,
            is_on_sale=False,
            selling_price=0,
            team_id=team_id
        )
        db.session.add(new_player)
        db.session.commit()


@views.route('/', methods=['GET', 'POST'])
@login_required  # show the home page only when a user is logged in
def home():
    if request.method == "POST":
        # add new team
        team_name = request.form.get('teamName')
        team_country = request.form.get('teamCountry')

        # make the team name unique
        existing_team = Team.query.filter_by(name=team_name).first()
        if existing_team:
            flash('Team name is taken', category="error")
            return render_template("home.html", user=current_user, country_list=COUNTRIES)
        new_team = Team(
            name=team_name,
            country=team_country,
            cash_available=5000000,
            user_id=current_user.id
        )
        db.session.add(new_team)
        db.session.commit()
        generate_players(new_team.id)
        flash('Dream team created!', category="success")
    if current_user.team:
        team = current_user.team[0]
        team_value = sum(i.market_value for i in team.players)
        return render_template("home.html", user=current_user, country_list=COUNTRIES,
                               team=team, team_value=team_value)
    else:
        return render_template("home.html", user=current_user, country_list=COUNTRIES)


@views.route('/edit/team', methods=['GET', 'POST'])
@login_required
def edit_team():
    if request.method == "POST":
        team_name = request.form.get('teamName')
        team_country = request.form.get('teamCountry')

        team = current_user.team[0]
        # disable updating db if no changes were made
        if team.name == team_name and team.country == team_country:
            flash(f'No changes were made.', category="error")
        else:
            team.name = team_name
            team.country = team_country
            db.session.commit()
            flash(f'Team updated successfully.', category="success")
        return redirect(url_for('views.home'))
    team = current_user.team[0]
    return render_template("edit.html", mode="team", user=current_user, country_list=COUNTRIES, team=team)


@views.route('/edit/player/<int:player_id>', methods=['GET', 'POST'])
@login_required
def edit_player(player_id):
    if request.method == "POST":
        player_first_name = request.form.get('playerFirstName')
        player_last_name = request.form.get('playerLastName')
        player_country = request.form.get('playerCountry')

        player = Player.query.filter_by(id=player_id).first()
        # disable updating db if no changes were made
        if player.first_name == player_first_name \
                and player.last_name == player_last_name \
                and player.country == player_country:
            flash(f'No changes were made.', category="error")
        else:
            player.first_name = player_first_name
            player.last_name = player_last_name
            player.country = player_country
            db.session.commit()
            flash(f'Player updated successfully.', category="success")
        return redirect(url_for('views.home'))
    player = Player.query.filter_by(id=player_id).first()
    return render_template("edit.html", mode="player", user=current_user, country_list=COUNTRIES, player=player)


@views.route('/market', methods=['GET', 'POST'])
@login_required
def market():
    def get_players_on_sale():
        players_on_sale = Player.query.filter_by(is_on_sale=True)
        current_team = [Team.query.filter_by(id=i.team_id).first() for i in players_on_sale]
        return list(zip(players_on_sale, current_team))
    team = current_user.team[0]
    if request.method == "POST":
        # sell player
        if 'player' in request.form and 'sellPrice' in request.form:
            player_id = request.form.get('player')
            sell_price = request.form.get('sellPrice')

            player = Player.query.filter_by(id=player_id).first()
            if not player:
                flash('Player not found.', category="error")
                return render_template("market.html", user=current_user, team=team,
                                       players_on_sale=get_players_on_sale())
            if not sell_price.isnumeric():
                flash('Invalid price.', category="error")
                return render_template("market.html", user=current_user, team=team,
                                       players_on_sale=get_players_on_sale())
            sell_price = int(sell_price)
            player.is_on_sale = True
            player.selling_price = sell_price
            db.session.commit()
            flash(f'{player.first_name} {player.last_name} is put on sale for ${sell_price}.', category="success")
        # buy player
        elif 'playerToBuy' in request.form:
            # update player
            player_id = request.form.get('playerToBuy')
            player = Player.query.filter_by(id=player_id).first()

            # check if purchasing team has enough money
            purchase_price = player.selling_price
            if team.cash_available < purchase_price:
                flash('Insufficient money, unable to purchase player.', category="error")
                return render_template("market.html", user=current_user, team=team,
                                       players_on_sale=get_players_on_sale())
            increment_percentage = round(random.uniform(.1, 1), 2) + 1
            increased_value = int(player.market_value * increment_percentage)
            player.market_value = increased_value
            player.is_on_sale = False
            player.selling_price = 0
            # update team
            old_team = Team.query.filter_by(id=player.team_id).first()
            old_team.cash_available += purchase_price
            player.team_id = team.id
            team.cash_available -= purchase_price

            db.session.commit()
            flash(f'Purchased {player.first_name} {player.last_name} for ${purchase_price}!', category="success")
        elif 'cancelSell' in request.form:
            player_id = request.form.get('cancelSell')
            player = Player.query.filter_by(id=player_id).first()
            player.is_on_sale = False
            player.selling_price = 0
            db.session.commit()
            flash(f'Removed {player.first_name} {player.last_name} from transfer list.', category="success")
        else:
            flash('Invalid request.', category="error")
    team = current_user.team[0]
    return render_template("market.html", user=current_user, team=team, players_on_sale=get_players_on_sale())


@views.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    # restrict page only for admin
    if current_user.username != "admin":
        return redirect(url_for('views.home'))

    all_users = User.query.all()
    all_users = [i.username for i in all_users]

    if request.method == "POST":
        user_cred = request.form.get('getUser')
        if is_email(user_cred):
            get_user = User.query.filter_by(email=user_cred)\
                .first()
        else:
            get_user = User.query.filter_by(username=user_cred)\
                .first()
        return render_template("admin.html", user=current_user, get_user=get_user, all_users=all_users)

    return render_template("admin.html", user=current_user, all_users=all_users)
