# -*- coding: utf-8 -*-

import sys, os, random, ssl, datetime
from collections import defaultdict
from flaskext.markdown import Markdown
from flask import Flask, render_template, request, redirect, session, make_response
from functools import wraps

from features import FEATURES
from cadapter import CAdapter
from load_env_variables import CONTENTFUL_MANAGEMENT_API, CONTENTFUL_SPACE_ID, FLASK_DEBUG, HASH_DATA, HTTP_AUTH_NAME, HTTP_AUTH_PASSWORD
from mail_integration import handle_mail

if not os.path.exists('src/static/css'):
    os.makedirs('src/static/css')

reload(sys)
sys.setdefaultencoding('utf-8')
PREVIEW_STRING = 'preview/'

ContentfulAdapter = CAdapter()

app = Flask(__name__)
app.secret_key = 'temporary'  # TODO Used to enable sessions

Markdown(app)

if FLASK_DEBUG == '0':
    if os.path.exists('css_suffix.txt'):
        with open('css_suffix.txt', 'r') as f:
            HASH_DATA = f.read().rstrip()


@app.before_request
def before():
    ContentfulAdapter.check_timed_update()
    set_session_language()
    set_session_preview()


def set_session_language():
    lang_updated = False
    if 'language' in request.args:
        # Specific language was requested
        if request.args['language'] not in [
                l.code for l in ContentfulAdapter.languages
        ]:
            # Unrecognized language requested, return default
            session['language'] = ContentfulAdapter.user_language
        session['language'] = request.args['language']
        lang_updated = True
    elif 'language' not in session and request.cookies.get(
            'user_language') != None:
        # No language requested, but cookie exists
        session['language'] = request.cookies.get('user_language')
    elif 'language' not in session:
        # No language requested, and no cookie, use default language
        session['language'] = ContentfulAdapter.default_language

    ContentfulAdapter.user_language = session['language']
    session['lang_updated'] = lang_updated


def set_session_preview():
    if 'preview' == request.path[1:8]:
        ContentfulAdapter.use_preview = True
        ContentfulAdapter.synchronize_with_contentful(preview=True)
        session['preview'] = True
        session['admin'] = False
    else:
        ContentfulAdapter.use_preview = False
        session['preview'] = False


@app.after_request
def after_request(response):
    if session['lang_updated']:
        expire_date = datetime.datetime.now()
        expire_date = expire_date + datetime.timedelta(days=3000)
        response.set_cookie(
            'user_language', session['language'], expires=expire_date)
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


def get_default_page_data():
    space_id = CONTENTFUL_SPACE_ID
    features = FEATURES
    hash_data = HASH_DATA
    entry_path = request.path
    preview = session['preview']
    adminMode = True if 'admin' in session and session['admin'] else False
    language = session['language']

    menu = ContentfulAdapter.get_entry(
        content_type='contentList', name='menuList')
    sponsors = ContentfulAdapter.get_entries(content_type='sponsor')
    adapter = ContentfulAdapter
    return locals()


@app.route('/admin')
def admin():
    session['admin'] = True
    return redirect('/', code=302)


@app.route('/logout')
def logout():
    session['admin'] = False
    return redirect('/', code=302)


@app.route('/')
@app.route('/preview')
def index():
    data_dictionary = get_default_page_data()
    meetups = ContentfulAdapter.get_entries(
        content_type='meetup', order='-date')[:3]
    guide = ContentfulAdapter.get_entry(content_type='guide')
    main_sponsors = ContentfulAdapter.get_entries(
        content_type='sponsor', isMainSponsor=1)
    news_items = ContentfulAdapter.get_entry(
        content_type='contentList', name='newsList')

    faq_list = ContentfulAdapter.get_entry(
        content_type='contentList', name='FAQList')

    data_dictionary.update(locals())

    resp = make_response(render_template('index.html', **data_dictionary))
    return resp


@app.route('/friend')
@app.route('/friend/<string:page_url>')
@app.route('/preview/friend/<string:page_url>')
def friend(page_url=None, entry_id=None):
    data_dictionary = get_default_page_data()

    if page_url is None:
        query = {'content_type': 'friend'}
    else:
        query = {'content_type': 'friend', 'url': '/' + page_url}

    friend = ContentfulAdapter.get_entry(**query)
    questions = ContentfulAdapter.get_entries(content_type='question', limit=3)
    data_dictionary.update(locals())
    return render_template('friend.html', **data_dictionary)


@app.route('/about')
@app.route('/about/<string:page_url>')
@app.route('/preview/about/<string:page_url>')
def about(page_url=None, entry_id=None):
    data_dictionary = get_default_page_data()

    if page_url == None:
        return render_template('about.html', **data_dictionary)
    elif page_url == 'terms':
        return render_template('terms.html', **data_dictionary)
    elif page_url == 'newsarchive':
        news_items = ContentfulAdapter.get_entries(content_type='newsItem')
        data_dictionary.update(locals())
        return render_template('newsarchive.html', **data_dictionary)

    return render_template('about.html', **data_dictionary)


@app.route('/faq')
@app.route('/preview/faq')
def faq(entry_id=None):
    data_dictionary = get_default_page_data()

    questions = ContentfulAdapter.get_entries(content_type='question')

    q_dict = defaultdict(list)
    for question in questions:
        category = question.category.rstrip().lstrip()
        q_dict[category].append(question)

    data_dictionary.update(locals())
    return render_template('faq.html', **data_dictionary)


@app.route('/news/<string:news_article_id>')
@app.route('/preview/news/<string:news_article_id>')
def news_article(news_article_id):
    data_dictionary = get_default_page_data()
    news_item = ContentfulAdapter.get_entry(
        content_type='newsItem', id=news_article_id)

    data_dictionary.update(locals())
    return render_template('news.html', **data_dictionary)


@app.route('/gallery')
@app.route('/preview/gallery')
def gallery():
    data_dictionary = get_default_page_data()
    meetups = ContentfulAdapter.get_entries(
        content_type='meetup', order='-date')  #TODO: Sort on date in meetup

    data_dictionary.update(locals())
    return render_template('gallery.html', **data_dictionary)


@app.route('/mail-notifier', methods=['POST'])
def mail_notifier():
    if request.method == 'POST':
        body = request.form['body-plain']
        size = 0
        image = None
        for key in request.files:
            key_size = int(request.files[key].headers['Content-Length'])
            if key_size > size:
                size = key_size
                image = request.files[key]

        if image != None and size < 30000000:
            handle_mail(body, image)
    return 'OK', 200


@app.errorhandler(404)
def page_not_found(error_msg=None):
    data_dictionary = get_default_page_data()
    data_dictionary.update(locals())
    return render_template('404.html', **data_dictionary), 404


if __name__ == '__main__':
    if FEATURES['use_dummy_ssl']:
        context = ('server.crt', 'server.key')
    else:
        context = None
    app.run(ssl_context=context)
