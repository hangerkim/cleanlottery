import random
import time

import dateutil.parser
from datetime import timedelta
from flask import Blueprint, jsonify, render_template, request, url_for

from app import utils
from app.models import db, Candidate, Result

bp = Blueprint('views', __name__, url_prefix='/')


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/extract', methods=['POST'])
def extract_candidates():
    json_data = request.get_json()
    article_url = json_data['article_url']
    allow_guest = json_data['allow_guest']

    # UTC
    time_limit = dateutil.parser.parse(json_data['time_limit'])
    # Convert to KST
    time_limit = time_limit + timedelta(hours=9)
    # Remove timezone info
    time_limit = time_limit.replace(tzinfo=None)

    candidates = utils.get_candidates_from_article(
        article_url=article_url, allow_guest=allow_guest,
        time_limit=time_limit)
    return jsonify({'candidates': candidates})


@bp.route('/draw', methods=['POST'])
def draw_lottery():
    json_data = request.get_json()
    num_winners = json_data['num_winners']
    cand_names = json_data['candidates']
    seed = int(time.time() * 1000)

    result = Result(seed=seed)
    candidates = [Candidate(name=name, result=result) for name in cand_names]

    random.seed(seed)
    winner_indices = random.sample(range(len(cand_names)), num_winners)
    winners = [candidates[i] for i in winner_indices]
    for winner in winners:
        winner.is_winner = True

    db.session.add(result)
    db.session.commit()

    winner_names = [winner.name for winner in winners]

    result_url = url_for('views.show_result', result_id=result.id)
    return jsonify({'winners': winner_names, 'result_id': result.id,
                    'result_url': result_url})


@bp.route('/recent_results', methods=['GET'])
def recent_results():
    recent_results = Result.query.order_by(Result.id.desc()).limit(50).all()
    return render_template('recent_results.html', results=recent_results)


@bp.route('/result/<int:result_id>')
def show_result(result_id):
    result = Result.query.get(result_id)
    return render_template('show_result.html', result=result)
