from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import flash
from flask import url_for
import os
import amazon_review_scrape



app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/asin', methods=['GET'])
def get_asin():
    return render_template('myasin.html')


@app.route('/asin', methods=['POST'])
def show_review():
    if request.form['asin']:
        asin = request.form['asin']
        all_review_list = []
        all_review_list = amazon_review_scrape.run(asin)
        # レビューが無ければ
        if not all_review_list:
            flash('\"{0}\" はレビューが無いか、正しいASINではありません'.format(asin), 'danger')
            # get_asin関数のページにリダイレクト
            return redirect(url_for('get_asin'))

        return render_template('/myasin.html', asin=asin, all_review_list=all_review_list)
    else:
        flash('ASINを入力して下さい', 'danger')
        # get_asin関数のページにリダイレクト
        return redirect(url_for('get_asin'))


if __name__ == '__main__':
    # 公式でos.urandom(24)で生成するのを推奨している
    # 外部に公開したければapp.run(host='0.0.0.0')を指定
    app.secret_key = os.urandom(24)
    app.run(port=5000, debug=True)
