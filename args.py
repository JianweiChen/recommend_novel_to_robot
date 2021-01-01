# coding=utf8
import os
class Args:
    jupyter_home_path = "/Users/jianweichen/Desktop/jupyter_workspace"
    novel_ffm_home_path = os.path.join(jupyter_home_path, "novel_ffm", 'recommend_novel_to_robot')
    fiction_home_path = os.path.join(jupyter_home_path, 'fiction')
    fiction_article_pb_path = os.path.join(fiction_home_path, 'article_pb')

    data_path = os.path.join(jupyter_home_path, 'data')
    book_warehouse_1t_path = os.path.join(data_path, 'book_warehouse_1t.bin')
    book_warehouse_10t_path = os.path.join(data_path, 'book_warehouse_10t.bin')
    book_meta_10t_csv_path = os.path.join(data_path, 'book_meta_10t.csv')
    library_path = os.path.join(data_path, 'library')
    event_csv_path = os.path.join(data_path, 'event')
    book_meta_pickle_path = os.path.join(data_path, 'book_meta.pkl')
    
    wv_corpus_path = os.path.join(data_path, 'wv_corpus.txt')
    wv_bin_path = os.path.join(data_path, 'wv.bin')
    wv_cn_path = os.path.join(data_path, 'wv_cn_50.txt')
    word_book_count_path = os.path.join(data_path, 'word_book_count.csv')
    new_word_cn_path = os.path.join(data_path, 'new_word_cn.txt')
    
    static_path = os.path.join(novel_ffm_home_path, 'static')
    css_path = os.path.join(static_path, 'book.css')
    javascript_path = os.path.join(static_path, 'book.js')
    
    robot_army_path = os.path.join(data_path, 'robot_army_0p1.bin') # 0.1版本
    
    stop_flag_file_path = os.path.join(novel_ffm_home_path, 'stop_flag')

    robot_count_per_regiment = 1000
    period_threshold = 100

    default_sample_loop = 2
    ub_dot_threshold_alpha = 0.085
    ub_dot_chapter_finish_threshold_alpha = 0.045

    click_drive_threshold = 0.045
    read_drive_threshold = 0.035
    detest_drive_threshold = 0.025 # 在click和read判断时，也要看detest_score的情况

    clean_addict_value_rate = 0.00 # 会直接撤出阅读
    addict_value_detest_rate = 0.5
    addict_value_init_value = 0.1
    addict_value_restore_rate_init_value = 0.01
    detest_value_init_value = -0.1
    detest_value_restore_rate_init_value = 0.01


if __name__ == '__main__':
    print(Args.novel_ffm_home_path)
