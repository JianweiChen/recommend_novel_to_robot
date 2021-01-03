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
    metrics_data_path = os.path.join(data_path, 'metrics_data')
    book_meta_pickle_path = os.path.join(data_path, 'book_meta.pkl')
    
    wv_corpus_path = os.path.join(data_path, 'wv_corpus.txt')
    wv_bin_path = os.path.join(data_path, 'wv.bin')
    wv_cn_path = os.path.join(data_path, 'wv_cn_50.txt')
    word_book_count_path = os.path.join(data_path, 'word_book_count.csv')
    new_word_cn_path = os.path.join(data_path, 'new_word_cn.txt')

    robot_army_path = os.path.join(data_path, 'robot_army_0p1.bin') # 0.1版本
    stop_flag_file_path = os.path.join(novel_ffm_home_path, 'stop_flag')

    robot_count_per_regiment = 1000
    period_threshold = 100

    default_sample_loop = 2

    # drive
    use_app_impluse_value_update_rate = 0.1
    click_drive_threshold = 0.12
    read_drive_threshold = 0.12
    detest_drive_threshold = 0.25 # 在read_drive判断时，也要看detest_score的情况
    title_detest_drive_threshold = 0.2 # 在click_drive判断时，也要看title_detest_score的情况


if __name__ == '__main__':
    print(Args.novel_ffm_home_path)
