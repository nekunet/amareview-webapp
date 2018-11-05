# -*- coding: utf-8 -*-

import os
import sys
import codecs
import argparse

if sys.version_info[0] >= 3:
    import urllib
    import urllib.request as request
    import urllib.error as urlerror
else:
    import urllib2 as request
    import urllib2 as urlerror
import socket
from contextlib import closing
from time import sleep
import re

import csv
import fnmatch
from bs4 import BeautifulSoup

if sys.version_info[0] >= 3:
    import html


# レビューを保存するためのリスト（星の数と対応）
review_list_1 = []
review_list_2 = []
review_list_3 = []
review_list_4 = []
review_list_5 = []



# パースのための正規表現
idre = re.compile('product\-reviews/([A-Z0-9]+)/ref\=cm_cr_arp_d_hist', re.MULTILINE | re.S)
contentre = re.compile(
    'cm_cr-review_list.*?>(.*?)(?:askReviewsPageAskWidget|a-form-actions a-spacing-top-extra-large|/html)',
    re.MULTILINE | re.S)
blockre = re.compile('a-section review\">(.*?)report-abuse-link', re.MULTILINE | re.S)
ratingre = re.compile('star-(.) review-rating', re.MULTILINE | re.S)
titlere = re.compile('review-title.*?>(.*?)</a>', re.MULTILINE | re.S)
datere = re.compile('review-date">(.*?)</span>', re.MULTILINE | re.S)
reviewre = re.compile('base review-text">(.*?)</span', re.MULTILINE | re.S)
userre = re.compile('profile\/(.*?)["/].*?\<\/div\>.*?\<\/div\>.', re.MULTILINE | re.S)
helpfulre = re.compile('review-votes.*?([0-9]+).*?([0-9]+)', re.MULTILINE | re.S)


# ページをダウンロードする関数
def download_page(url, referer, maxretries, timeout, pause):
    tries = 0
    htmlpage = None
    while tries < maxretries and htmlpage is None:
        try:
            code = 404
            req = request.Request(url)
            req.add_header('Referer', referer)
            req.add_header('User-agent',
                           'Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.91 Chrome/12.0.742.91 Safari/534.30')
            with closing(request.urlopen(req, timeout=timeout)) as f:
                code = f.getcode()
                htmlpage = f.read()
                sleep(pause)
        except (urlerror.URLError, socket.timeout, socket.error):
            tries += 1
    if htmlpage:
        return htmlpage.decode('utf-8'), code
    else:
        return None, code


# ページをパースする関数
def ama_parser(htmlpage):
    reviews = dict()

    if not idre.search(htmlpage):
        return
    id_ = idre.findall(htmlpage)[0]

    htmlpage = contentre.findall(htmlpage)[0]
    for block in blockre.findall(htmlpage):
        title = titlere.findall(block)[0]
        reviewtext = reviewre.findall(block)[0]
        if sys.version_info[0] >= 3:
            try:
                title = html.unescape(title)
            except Exception:
                pass
            try:
                reviewtext = html.unescape(reviewtext)
            except Exception:
                pass
        rating = int(ratingre.findall(block)[0])
        date = datere.findall(block)[0]
        user = 'ANONYMOUS'
        usermatch = userre.findall(block)
        if usermatch:
            user = usermatch[0]
        helptot = 0
        helpyes = 0
        helpmatch = helpfulre.findall(block)
        if helpmatch:
            helptot = int(helpmatch[0][0])
            helpyes = int(helpmatch[0][1])
            if helpyes > helptot:
                helptot, helpyes = helpyes, helptot

        if rating >= 4:
            binaryrating = 'positive'
        else:
            binaryrating = 'negative'
        if sys.version_info[0] >= 3:
            review_row = [id_, date, user, title, reviewtext, rating, binaryrating, helptot, helpyes]
        else:
            review_row = [id_, unicode.encode(date, encoding='ascii', errors='ignore'),
                          unicode.encode(user, encoding='ascii', errors='ignore'),
                          unicode.encode(title, encoding='ascii', errors='ignore'),
                          unicode.encode(reviewtext, encoding='ascii', errors='ignore'), rating,
                          binaryrating, helptot, helpyes]

        soup = BeautifulSoup(reviewtext, "lxml")
        #print("rating: {0}".format(rating))
        #print(soup.get_text()+"\n")
        if rating == 1:
            review_list_1.append(soup.get_text())
        elif rating == 2:
            review_list_2.append(soup.get_text())
        elif rating == 3:
            review_list_3.append(soup.get_text())
        elif rating == 4:
            review_list_4.append(soup.get_text())
        elif rating == 5:
            review_list_5.append(soup.get_text())



# メイン関数
def main(asin):

    domain = 'co.jp'    # Amazonの国ドメイン
    maxretries = 3      # 最大リトライ数
    timeout = 180       # httpコネクションのタイムアウト時間（秒）
    pause = 1           # httpリクエスト毎のwaitタイム（秒）
    maxreviews = -1     # ダウンロードするレビューの最大数（-1: unlimited）
    captcha = False     # captchページをcaptchaが無くなるまでリクエストするか
    ids = []            # asinのリスト
    ids.append(asin)


    counterre = re.compile('cm_cr_arp_d_paging_btm_([0-9]+)')
    robotre = re.compile('images-amazon\.com/captcha/')

    for id_ in ids:

        urlPart1 = "http://www.amazon." + domain + "/product-reviews/"
        urlPart2 = "/?ie=UTF8&showViewpoints=0&pageNumber="
        urlPart3 = "&sortBy=bySubmissionDateDescending"

        referer = urlPart1 + str(id_) + urlPart2 + "1" + urlPart3

        page = 1
        lastPage = 1
        while page <= lastPage:

            url = urlPart1 + str(id_) + urlPart2 + str(page) + urlPart3
            print(url)
            htmlpage, code = download_page(url, referer, maxretries, timeout, pause)

            if htmlpage is None or code != 200:
                if code == 503:
                    page -= 1
                    pause += 2
                    print('(' + str(code) + ') Retrying downloading the URL: ' + url)
                else:
                    print('(' + str(code) + ') Done downloading the URL: ' + url)
                    break
            else:
                print('Got page ' + str(page) + ' out of ' + str(lastPage) + ' for product ' + id_ + ' timeout=' + str(
                    pause))
                if robotre.search(htmlpage):
                    print('ROBOT! timeout=' + str(pause))
                    if captcha or page == 1:
                        pause *= 2
                        continue
                    else:
                        pause += 2
                for match in counterre.findall(htmlpage):
                    try:
                        value = int(match)
                        if value > lastPage:
                            lastPage = value
                    except:
                        pass
                ama_parser(htmlpage)
            referer = urlPart1 + str(id_) + urlPart2 + str(page) + urlPart3
            if maxreviews > 0 and page*10 >= maxreviews:
                break
            page += 1


def run(asin):
    review_list_1.clear()
    review_list_2.clear()
    review_list_3.clear()
    review_list_4.clear()
    review_list_5.clear()
    main(asin)
    all_review_list = []
    if not (review_list_1 or review_list_2 or review_list_3 or review_list_4 or review_list_5):
        return all_review_list
    all_review_list.append(review_list_1)
    all_review_list.append(review_list_2)
    all_review_list.append(review_list_3)
    all_review_list.append(review_list_4)
    all_review_list.append(review_list_5)
    return all_review_list
