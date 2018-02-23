# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - api is an example of Hypermedia API support and access control
#########################################################################
from gluon.tools import Mail
import random

mail = Mail()
mail.settings.server = 'smtp.gmail.com:587'
mail.settings.sender = ''
mail.settings.login = ''

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    ref = {'short': db.shrt, 'long': db.lng, 'opening': db.opn, 'mixed': db.mx}
    if request.vars.prompt_type:
        if request.vars.prompt_type == 'surprise':
            database = random.choice(ref.values())
        else:
            database = ref[request.vars.prompt_type]

        if request.vars.prompt_text and request.vars.prompt_type != 'surprise':
            parse_list = request.vars.prompt_text.splitlines()
            for i in parse_list:
                try:
                    database.insert(prompt=i)
                except:
                    pass
        else:
            record_random = db().select(database.prompt, orderby='<random>')[0].prompt
            session.record_random = str(record_random)
            redirect(URL('generate'))

    del_prompt = SQLFORM.factory(Field('short_prompts', requires=IS_IN_DB(db, 'shrt.id', '%(prompt)s')),
                                Field('long_prompts', requires=IS_IN_DB(db, 'lng.id', '%(prompt)s')),
                                Field('opener_prompts', requires=IS_IN_DB(db, 'opn.id', '%(prompt)s')),
                                Field('criteria_prompts', requires=IS_IN_DB(db, 'mx.id', '%(prompt)s')), submit_button="Delete")
    del_ref = {request.vars.short_prompts: db.shrt,
            request.vars.long_prompts: db.lng,
            request.vars.opener_prompts: db.opn,
            request.vars.criteria_prompts: db.mx}
    for key in del_ref:
        if key:
            db(del_ref[key].id == key).delete()
    return dict(form=del_prompt)


def generate():
    if request.vars.title and request.vars.body:
        try:
            db.writing.insert(body=request.vars.body, title=request.vars.title, prompt=request.vars.hide)
        except:
            pass
        redirect(URL('data'))

    word_short = [100, 150, 150, 150, 200, 200, 200, 250, 250, 300]
    word_medium = [350, 400, 400, 400, 450, 500, 500, 550, 550, 600]
    word_long = [650, 700, 700, 700, 750, 750, 800, 800, 850, 900]
    amount = "%s / %s or %s" % (random.choice(word_short), random.choice(word_medium), random.choice(word_long))
    return dict(word=amount)


def data():
    disp_title = " "
    disp_prompt = " "
    disp_body = " "
    disp_cmt = ""
    cmt_box = " "
    results = " "

    writings = SQLFORM.factory(Field('list_of_writings', requires=IS_IN_DB(db, 'writing.id', '%(title)s')), submit_button="View")
    if request.vars.list_of_writings:
        redirect(URL('data', args=request.vars.list_of_writings))

    if request.vars.search_db:
        query1 = db.writing.body.contains(request.vars.search_db)
        query2 = db.writing.prompt.contains(request.vars.search_db)
        results = db(query1 | query2).select()

    if request.vars.subscribe:
        try:
            db.mails.insert(address=request.vars.subscribe)
        except:
            pass

    if request.args:
        db_row = db(db.writing.id == request.args(0)).select()[0]
        disp_title = db_row.title
        disp_prompt = db_row.prompt
        disp_prompt = "Written for <" + str(disp_prompt) + ">"
        disp_body = db_row.body
        disp_cmt = db_row.cmt

        cmt_box = SQLFORM.factory(Field('add_comment', 'text', requires=IS_NOT_EMPTY()), submit_button="Post")
        cmt_box.element('textarea[name=add_comment]')['_style'] = 'width:300px;height:50px;'
        if cmt_box.process().accepted:
            if disp_cmt is not None:
                disp_cmt = disp_cmt + "#newline" + cmt_box.vars.add_comment
            else:
                disp_cmt = cmt_box.vars.add_comment
            db(db.writing.id == request.args(0)).select()[0].update_record(cmt=disp_cmt)
            listmail = []
            for item in db().select(db.mails.address):
                listmail.append(str(item.address))
            msg = 'For the writing ' + '<' + str(disp_title) + '>'
            mail.send(to=listmail, subject='Prompt Generator - New Comment Posted', message=msg)
    return dict(form=writings, results=results, disp_title=disp_title, disp_prompt=disp_prompt, disp_body=disp_body, disp_cmt=disp_cmt, cmt_box=cmt_box)

def secret():
    del_writing = SQLFORM.factory(Field('delete_writing', requires=IS_IN_DB(db, 'writing.id', '%(title)s')))
    if request.vars.delete_writing:
        db(db.writing.id == request.vars.delete_writing).delete()
    return dict(form=del_writing)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_login()
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)
