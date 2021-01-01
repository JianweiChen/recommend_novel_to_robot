#coding=utf8

import os
import sys
import random
import collections
import pickle
import numpy as np
import pandas as pd
import word2vec
import googletrans
from nltk.corpus import stopwords
from googletrans import Translator
from google.protobuf import text_format
from nltk import sent_tokenize
from nltk import word_tokenize

from args import Args
from proto.article_pb2 import Article
from proto.book_def_pb2 import Book as BookDef, BookWarehouse, Paragraph, Sentence

class S:
    line_break = '\n'
    stopword_set = set(stopwords.words('english'))
    letter_set = set([chr(ord('a')+i) for i in range(26)])
    digit_set = set([chr(ord('1')+i) for i in range(10)])
    @staticmethod
    def sentence_to_string_list(sentence):
        return list(sentence.word)

    @staticmethod
    def paragraph_to_string_list(paragraph):
        string_list = []
        for sentence in paragraph.sentence:
            sentence_string_list = S.sentence_to_string_list(sentence)
            string_list.extend(sentence_string_list)
            string_list.append(S.line_break)
        return string_list
    
    @staticmethod
    def book_to_string_list(book):
        string_list = []
        string_list.extend(S.sentence_to_string_list(book.title))
        string_list.append(S.line_break)
        string_list.extend(S.sentence_to_string_list(book.synopsis))
        string_list.append(S.line_break)
        for paragraph in book.paragraph:
            paragraph_string_list = S.paragraph_to_string_list(paragraph)
            string_list.extend(paragraph_string_list)
            string_list.append(S.line_break)
        return string_list

    @staticmethod
    def capitalize_string_list(string_list):
        return [
            word.capitalize() for word in string_list
        ]

    @staticmethod
    def lower_string_list(string_list):
        return [
            word.lower() for word in string_list
        ]

    @staticmethod
    def remove_line_break_from_string_list(string_list):
        return [
            word for word in string_list if word != '\n'
        ]
    
    @staticmethod
    def remove_stopword_from_string_list(string_list):
        return [word for word in string_list if word.lower() not in S.stopword_set]
    
    @staticmethod
    def is_a_word(word):
        word = word.lower()
        return all([c in S.letter_set or c in S.digit_set or c=='-' for c in word])
        
class BookWarehouseDumper(object):
    def get_book_ids(self, random_shuffle=False, in10t=True):
        book_ids = []
        if not in10t:
            filenames = os.listdir(Args.fiction_article_pb_path)
            for filename in filenames:
                if filename.endswith(".txt"):
                    book_id = filename.split('.')[0]
                    book_ids.append(book_id)
        else:
            df = pd.read_csv(Args.book_meta_10t_csv_path)
            book_ids = df['book_id'].to_list()

        if random_shuffle:
            random.shuffle(book_ids)
        return book_ids
    def _get_article_pb_path(self, book_id):
        return os.path.join(Args.fiction_article_pb_path, '%s.txt' % book_id)

    def has_article(self, book_id):
        article_pb_path = self._get_article_pb_path(book_id)
        if os.path.exists(article_pb_path):
            return True
        return False
    def load_article(self, book_id):
        assert self.has_article(book_id)
        article_pb_path = self._get_article_pb_path(book_id)
        with open(article_pb_path, 'r') as f:
            article = Article()
            text_format.Parse(f.read(), article)
            return article

    def article_to_book(self, article):
        book_def = BookDef()
        title = article.title[30:]
        book_def.bid = article.id
        book_def.title.word.extend(list(word_tokenize(title)))
        book_def.synopsis.word.extend(list(word_tokenize(article.synopsis)))
        book_def.keyword.extend(article.keyword)
        book_def.category.extend(article.category)
        book_def.rating = article.rating
        book_def.author = article.author_name
        for paragraph in article.paragraph:
            book_paragraph = Paragraph()
            content = paragraph.replace('\n', ' ').replace('\r', '')
            sens = sent_tokenize(content)

            for sen in sens:
                sentence = Sentence()
                for word in word_tokenize(sen):
                    sentence.word.append(word)
                book_paragraph.sentence.append(sentence)
            book_def.paragraph.append(book_paragraph)
        return book_def

    def load_book_warehouse(self, type="1t"):
        assert type in ('1t', '10t')
        if type == "1t":
            book_warehouse_path = Args.book_warehouse_1t_path
        elif type == "10t":
            book_warehouse_path = Args.book_warehouse_10t_path
        book_warehouse = BookWarehouse()
        with open(book_warehouse_path, 'rb') as f:
            book_warehouse.ParseFromString(f.read())
        return book_warehouse

    def dump_book_warehouse(self): # call at once
        book_ids = self.get_book_ids()[:10000]
        book_warehouse_1t = BookWarehouse()
        book_warehouse_10t = BookWarehouse()
        for idx, book_id in enumerate(book_ids):
            article = self.load_article(book_id)
            book = self.article_to_book(article)
            book_warehouse_10t.book.append(book)
            if idx <= 1000:
                book_warehouse_1t.book.append(book)
            sys.stdout.write("\r %s" % idx)
        with open(Args.book_warehouse_1t_path, 'wb') as fw:
            fw.write(book_warehouse_1t.SerializeToString())
        with open(Args.book_warehouse_10t_path, 'wb') as fw:
            fw.write(book_warehouse_10t.SerializeToString())    

    def __gen_10t_csv(self):
        book_ids = get_book_ids(in10t=False)
        titles = []
        for idx, book_id in enumerate(book_ids):
            article = self.load_article(book_id)
            book = self.article_to_book(article)
            title = book.title
            titles.append(title)
            sys.stdout.write("\r %s" % idx)
        data = {'book_id': book_ids, 'title': titles}
        df = pd.DataFrame(data)
        df.to_csv(Args.book_meta_10t_csv_path)
        
class NovelHelper(object):
    def __init__(self, book_warehouse=None):
        if not book_warehouse:
            book_warehouse = BookWarehouse()
        self.book_warehouse = book_warehouse
        self.wv_cn_map = dict()
        self.word_book_count_map = dict()
        self.wv_word_idx_map = dict()
        self.wv_model = None
        self.load_wv_bin()
        self.load_wv_cn()
        self.load_word_book_count()
    
    def get_book_content_for_library(self, book):
        content = 'bid=%s\n' % book.bid
        content += 'rating=%s\n' % book.rating
        content += 'keyword:\n'
        content += ', '.join(book.keyword)
        content += '\n'
        content += 'category:\n'
        content += ', '.join(book.category)
        content += '\n'
        content += ' '.join(S.book_to_string_list(book))
        return content
    
    def dump_book_to_library(self, book):
        title = '_'.join(S.sentence_to_string_list(book.title))
        library_book_path = os.path.join(Args.library_path, '%s.txt' % title)
        with open(library_book_path, 'w') as fw:
            content = self.get_book_content_for_library(book)
            fw.write(content)

    @classmethod
    def load_book_warehouse(cls, book_warehouse_type='10t'):
        book_warehouse_path = Args.book_warehouse_10t_path \
            if book_warehouse_type == '10t' \
            else Args.book_warehouse_1t_path
        with open(book_warehouse_path, 'rb') as f:
            book_warehouse = BookWarehouse()
            book_warehouse.ParseFromString(f.read())
            return book_warehouse

    def load_wv_bin(self):
        self.wv_word_idx_map = dict()
        with open(Args.wv_bin_path, 'rb') as f:
            self.wv_model = word2vec.load(Args.wv_bin_path)
            for idx, word in enumerate(self.wv_model.vocab):
                self.wv_word_idx_map[word.lower()] = idx
    
    def _p2_to_p3(self, p2):
        word = p2[0]
        score = p2[1]
        cn = self.get_cn(word)
        return (word, cn, score)
    
    def get_similar_word(self, word1, k=20):
        word1 = word1.lower()
        if word1 not in self.wv_word_idx_map:
            return []
        idx1 = self.wv_word_idx_map[word1]
        word_score_map = dict()
        for word2, idx2 in self.wv_word_idx_map.items():
            if idx1 == idx2:
                continue
            score = np.dot(self.wv_model.vectors[idx1], self.wv_model.vectors[idx2])
            word_score_map[word2] = score
        r = sorted(word_score_map.items(), key=lambda x: x[1], reverse=True)[:k]
        return [self._p2_to_p3(p2) for p2 in r]
    
    def get_analogy_word(self, word1, word2, word3, k=20):
        wm = self.wv_word_idx_map
        wvmv = self.wv_model.vectors
        if word1 not in wm or word2 not in wm or word3 not in wm:
            return []
        idx1, idx2, idx3 = wm[word1], wm[word2], wm[word3]
        v1, v2, v3 = wvmv[idx1], wvmv[idx2], wvmv[idx3]
        vt = v3 + v2 - v1
        word_score_map = dict()
        for word4, idx4 in wm.items():
            if idx4 in set([idx1, idx2, idx3]):
                continue
            score = np.dot(wvmv[idx4], vt)
            word_score_map[word4] = score
        r = sorted(word_score_map.items(), key=lambda x: x[1], reverse=True)[:k]
        return [self._p2_to_p3(p2) for p2 in r]
            
    def _dump_wv_corpus(self):
        with open(Args.wv_corpus_path, 'w') as fw:
            for book in self.book_warehouse.book:
                word_list = S.book_to_string_list(book)
                word_list = S.lower_string_list(word_list)
                text = ' '.join(word_list)
                fw.write(text)
                fw.write(S.line_break)
    
    def train_and_dump_wv_bin(self, vec_dim=64):
        self._dump_wv_corpus()
        word2vec.word2vec(Args.wv_corpus_path, Args.wv_bin_path, size=vec_dim, binary=True, verbose=True)
    
    def load_wv_cn(self):
        self.wv_cn_map = dict()
        with open(Args.wv_cn_path, 'r') as f:
            for line in f:
                word, cn = line.strip().split(" ", 1)
                self.wv_cn_map[word.lower()] = cn

    def load_word_book_count(self):
        self.word_book_count_map = dict()
        self.word_list = []
        df = pd.read_csv(Args.word_book_count_path)
        for row in df.iterrows():
            word = row[1].word
            book_count = row[1].book_count
            # if book_count < 10:
            #     break
            self.word_book_count_map[word] = book_count
            self.word_list.append(word)
        

    def dump_word_book_count_csv(self):
        word_book_count_map = collections.defaultdict(int)
        for book in self.book_warehouse.book:
            words = S.book_to_string_list(book)
            words = S.remove_line_break_from_string_list(words)
            words = S.lower_string_list(words)
            for word in set(words):
                word_book_count_map[word] += 1
        pair_list = sorted(word_book_count_map.items(), key=lambda x:x[1], reverse=True)
        word_list = [pair[0] for pair in pair_list]
        book_count_list = [pair[1] for pair in pair_list]
        df = pd.DataFrame({'word': word_list, 'book_count': book_count_list})
        df.to_csv(Args.word_book_count_path)
    
    def get_cn(self, word):
        word = word.capitalize()
        if word not in self.wv_cn_map:
            return 'x'
        return self.wv_cn_map[word]
    
    def _fetch_cn_online(self, book_count_threshold=50):
        url = 'translate.google.com'
        online_translator = Translator(service_urls=[url,])
        df = pd.read_csv(Args.word_book_count_path)
        with open(Args.new_word_cn_path, 'a') as fw:
            idx = 1
            for row in df.iterrows():
                word = row[1].word
                book_count = row[1].book_count
                if book_count < book_count_threshold:
                    break
                if word in self.wv_cn_map:
                    continue
                try:
                    rsp = online_translator.translate(word, src='en',dest='zh-cn')
                    cn = rsp.text
                    fw.write("%s %s\n" % (word, cn))
                    if idx % 50 == 0:
                        fw.flush()
                    sys.stdout.write("\r %s %s %s" % (idx, word, cn) + ' '*20)
                except Exception as e:
                    print(e)
                idx += 1

    # 整体上认知一下词汇之间的相似度分数；另外对robot自身是可以产出一些指标的
    def get_similar_score_for_word_list(self, word_list):
        word_list = word_list[:10] # 最多研究10个词的相似性
        return None
            
                
          
class MetaManager(object):
    def __init__(self, book_warehouse=None):
        self.book_warehouse = book_warehouse
    
    def dump_meta(self):
        if not self.book_warehouse:
            raise Exception("No Book Warehouse set in this MetaManager!")
        keyword_bid_list = collections.defaultdict(list)
        category_bid_list = collections.defaultdict(list)
        bid_title_map = dict()
        for idx, book in enumerate(self.book_warehouse.book):
            bid = book.bid
            title = ' '.join(S.sentence_to_string_list(book.title))
            for keyword in book.keyword:
                keyword = keyword.replace("/", 'or')
                keyword_bid_list[keyword].append(bid)
            for category in book.category:
                category = category.replace("/", 'or')
                category_bid_list[category].append(bid)
            bid_title_map[bid] = title
            sys.stdout.write("\r %s" % idx)
            sys.stdout.flush()
        with open(Args.book_meta_pickle_path, 'wb') as fw:
            obj_tup = (
                keyword_bid_list,
                category_bid_list,
                bid_title_map,
            )
            pickle.dump(obj_tup, fw)
    def load_meta(self):
        with open(Args.book_meta_pickle_path, 'rb') as f:
            obj_tup = pickle.load(f)
            return obj_tup

