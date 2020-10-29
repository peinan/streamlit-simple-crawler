#!/usr/bin/env python
# coding: utf-8
#
# Filename:   main.py
# Author:     Peinan ZHANG
# Created at: 2020-10-29

import streamlit as st
from cache_on_button_press import cache_on_button_press

import requests
from bs4 import BeautifulSoup

import pandas as pd


@cache_on_button_press('▶️  Run Crawl !')
def crawl_and_parse(cfg: dict) -> dict:
    res = requests.get(cfg['url'])
    status_code = res.status_code
    if status_code != 200:
        raise requests.exceptions.ConnectionError

    soup = BeautifulSoup(res.text, 'html.parser')
    html = soup.prettify()

    target_type = cfg['target_type']
    clue_type = cfg['clue_type']
    clues = cfg['clues']
    try:
        if target_type == 'text':
            if clue_type == 'css_selector':
                parsed_results = [ e.text for e in soup.select(clues['css_selector']) ]
            elif clue_type == 'tag_prop':
                parsed_results = [
                    e.text for e in soup.find_all(clues['tag'], class_=clues['class'], attrs={'id': clues['id']})
                ]
            else:
                parsed_results = []
    except:
        raise ValueError

    if target_type == 'text':
        results = {
            'json': parsed_results,
            'dataframe': pd.read_html(html, attrs={'id': clues['id']})[0] \
                         if set(clues.values()) == {''} \
                         else pd.DataFrame(parsed_results),
            'raw': '\n'.join(parsed_results),
            'html': html
        }
    elif target_type == 'table':
        dataframe = pd.read_html(html, attrs={'id': clues['id']})[0]
        results = {
            'json': dataframe.to_dict(),
            'dataframe': dataframe,
            'raw': dataframe.to_csv(),
            'html': html
        }

    return results


def main():
    st.title("""Simple Crawler""")
    st.sidebar.write("""
        ## How to use

        1. Enter the **URL** of the web page you want to crawl.
        2. Choose the **Target Type** from "**text**" and "**table**".
        3. Select the proper **Clue Type**.
            - **HTML Tag** is the most popular clue lead you to what you want.
            - **CSS Selector** is good at the pages lack of `class` or `id` attributes.
            - **none** only used when the Target Type is `table`.
        4. Fill the clues and hit the "**Run Crawl !**" button.
        ---
        """)

    url = st.sidebar.text_input('URL', value='https://')
    target_type = st.sidebar.selectbox('Target Type', ('text', 'table'))
    clue_type = st.sidebar.selectbox('Clue Type', ('css_selector', 'tag_prop', 'none'))

    css_selector = ''
    html_tag = ''
    html_id = ''
    html_class = ''

    if clue_type == 'css_selector':
        css_selector = st.sidebar.text_input('CSS Selector')
    elif clue_type == 'tag_prop':
        html_tag = st.sidebar.text_input('tag', value='div')
        html_id = st.sidebar.text_input('id (optional but recommended)')
        html_class = st.sidebar.text_input('class (optional but recommended)')
    elif clue_type == 'none':
        pass

    crawl_config = {
        'url': url,
        'target_type': target_type,
        'clue_type': clue_type,
        'clues': {
            'css_selector': css_selector,
            'tag': html_tag,
            'id':  html_id,
            'class': html_class
        },
    }

    st.sidebar.write('---')

    try:
        results = crawl_and_parse(crawl_config)
    except requests.exceptions.InvalidURL:
        st.error(f'Invalid URL "{url}"')
        st.stop()
        return
    except requests.exceptions.ConnectionError:
        st.error(f'Connection failed')
        st.stop()
        return
    except ValueError:
        st.error('Parsing failed')
        st.stop()
        return

    st.subheader('Crawl Result')

    result_format = st.selectbox(
        'Select the result format',
        options=('json', 'dataframe', 'raw (CSV)') \
            if target_type == 'text' else ('dataframe', 'json', 'raw (CSV)')
    )

    if result_format == 'json':
        st.json({
            'results': results['json']
        })
    elif result_format == 'dataframe':
        st.dataframe(results['dataframe'])
    elif result_format == 'raw (CSV)':
        st.code(results['raw'])

    with st.beta_expander('See Raw HTML'):
        st.code(results['html'], language='html')


if __name__ == '__main__':
    main()

